param([string] $Stage = 'stage-windows64', [string] $Evidence = 'windows64-runtime-evidence')
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if ($env:GITHUB_ACTIONS -ne 'true') {
    throw 'This test creates fixture profiles and is restricted to disposable GitHub runners.'
}
$stagePath = (Resolve-Path $Stage).Path
$python = (Get-Command python).Source
$httpsCheck = (Resolve-Path 'distribution/windows64/verify_https.py').Path
$evidencePath = [IO.Path]::GetFullPath($Evidence)
New-Item -ItemType Directory -Force $evidencePath | Out-Null
$local = [Environment]::GetFolderPath('LocalApplicationData')
$roaming = [Environment]::GetFolderPath('ApplicationData')
$profile = Join-Path $local 'OpenCPN-64bit-Preview\profile'
if (Test-Path $profile) {
    # Core unit tests can leave a test profile on this disposable runner.
    # Preserve it separately and exercise the packaged GUI with a fresh profile.
    $previous = $profile + '-before-smoke'
    if (Test-Path $previous) { throw 'A previous smoke-test backup already exists.' }
    Move-Item $profile $previous
}
New-Item -ItemType Directory -Force $profile | Out-Null
$plugins = @('xweather_routing_pi.dll', 'xgrib_pi.dll', 'celestial_navigation_pi.dll',
             'polar_pi.dll', 'climatology_pi.dll', 'offlinetides_pi.dll')
$config = @"
[Settings]
ConfigVersionString=Version 5.14.0
NavMessageShown=1
OpenGL=0
DisableOpenGL=1
ShowMenuBar=1
[PlugIns/grib_pi.dll]
bEnabled=0
"@
# Deliberately omit the six bundled plugins.  This must exercise the same
# clean-profile defaults a tester receives after extracting the ZIP.
$config | Set-Content -Encoding utf8 (Join-Path $profile 'opencpn.ini')

$normalPaths = @((Join-Path $roaming 'opencpn'), (Join-Path $local 'opencpn'),
                 (Join-Path $env:ProgramData 'opencpn'))
foreach ($path in $normalPaths) {
    New-Item -ItemType Directory -Force $path | Out-Null
    $sentinel = Join-Path $path ('preview-isolation-sentinel-' + $env:GITHUB_RUN_ID + '.txt')
    if (Test-Path $sentinel) { throw 'A previous isolation sentinel already exists.' }
    'ordinary-opencpn-profile-sentinel' | Set-Content $sentinel
}
function Profile-Snapshot {
    $items = foreach ($root in $normalPaths) {
        foreach ($file in Get-ChildItem $root -Recurse -File -Force) {
            "$($file.FullName):$((Get-FileHash $file.FullName -Algorithm SHA256).Hash)"
        }
    }
    return ($items | Sort-Object) -join "`n"
}
$before = Profile-Snapshot
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Accept-Startup-Notice([int] $processId) {
    $processCondition = [Windows.Automation.PropertyCondition]::new(
        [Windows.Automation.AutomationElement]::ProcessIdProperty, $processId)
    $nameCondition = [Windows.Automation.PropertyCondition]::new(
        [Windows.Automation.AutomationElement]::NameProperty, 'Agree')
    $condition = [Windows.Automation.AndCondition]::new($processCondition, $nameCondition)
    $button = [Windows.Automation.AutomationElement]::RootElement.FindFirst(
        [Windows.Automation.TreeScope]::Descendants, $condition)
    if ($null -ne $button) {
        $button.GetCurrentPattern([Windows.Automation.InvokePattern]::Pattern).Invoke()
    }
}

function Save-Screenshot {
    $bounds = [Windows.Forms.SystemInformation]::VirtualScreen
    $bitmap = [Drawing.Bitmap]::new($bounds.Width, $bounds.Height)
    $graphics = [Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.CopyFromScreen($bounds.Location, [Drawing.Point]::Empty, $bounds.Size)
        $bitmap.Save((Join-Path $evidencePath 'preview-running.png'), [Drawing.Imaging.ImageFormat]::Png)
    } finally { $graphics.Dispose(); $bitmap.Dispose() }
}

$savedPath = $env:PATH
$app = $null
$log = Join-Path $profile 'opencpn.log'
try {
    $env:PATH = "$env:SystemRoot\System32;$env:SystemRoot"
    # Do not inherit development SDK data paths into the packaged process.
    foreach ($name in @('ECCODES_DEFINITION_PATH', 'ECCODES_SAMPLES_PATH', 'PROJ_DATA', 'PROJ_LIB')) {
        Remove-Item "Env:$name" -ErrorAction SilentlyContinue
    }
    & $python $httpsCheck $stagePath | Set-Content (Join-Path $evidencePath 'https.json')
    if ($LASTEXITCODE -ne 0) { throw 'Packaged HTTPS failed native certificate verification.' }
    $helper = Join-Path $stagePath 'plugins\xgrib_pi\bin\environmental-grib.exe'
    & $helper capabilities | Set-Content (Join-Path $evidencePath 'helper-capabilities.json')
    if ($LASTEXITCODE -ne 0) { throw 'Packaged xGRIB helper could not start without the SDK.' }
    $abi = & (Join-Path $stagePath 'opencpn-cmd.exe') print-abi
    if ($LASTEXITCODE -ne 0 -or ([string]$abi).Trim() -ne 'msvc-wx32-x64:10') {
        throw "The packaged console tool did not report the x64 Preview ABI: $abi"
    }
    $abi | Set-Content (Join-Path $evidencePath 'console-abi.txt')
    foreach ($override in @(@{name='portable'; argument='-p'},
                            @{name='configdir'; argument=('--configdir "' + $normalPaths[0] + '"')})) {
        $stderr = Join-Path $evidencePath ($override.name + '-rejection.txt')
        $probe = Start-Process (Join-Path $stagePath 'opencpn.exe') `
            -ArgumentList $override.argument -WorkingDirectory $stagePath `
            -RedirectStandardError $stderr -PassThru
        if (-not $probe.WaitForExit(15000)) {
            Stop-Process -Id $probe.Id -Force
            throw "Preview did not reject the $($override.name) profile override."
        }
        if ($probe.ExitCode -eq 0 -or -not ([string](Get-Content $stderr -Raw)).Contains('separate profile')) {
            throw "Preview did not report rejection of the $($override.name) profile override."
        }
    }
    $app = Start-Process (Join-Path $stagePath 'opencpn.exe') -WorkingDirectory $stagePath -PassThru
    $deadline = [DateTime]::UtcNow.AddSeconds(90)
    $ready = $false
    do {
        $app.Refresh()
        if ($app.HasExited) { throw "Preview exited during startup: $($app.ExitCode)" }
        Accept-Startup-Notice $app.Id
        if (Test-Path $log) {
            $content = [string](Get-Content $log -Raw)
            $ready = $content.Contains('OnInitTimer...Finalize Canvases')
            foreach ($plugin in $plugins) {
                $ready = $ready -and ($content -match ('Initializing PlugIn:.*' + [regex]::Escape($plugin)))
            }
        }
        if (-not $ready) { Start-Sleep -Milliseconds 500 }
    } while (-not $ready -and [DateTime]::UtcNow -lt $deadline)
    if (-not $ready) { throw 'The Preview did not initialize its main window and all six plugins.' }
    $weatherData = Join-Path $stagePath 'plugins\xweather_routing_pi'
    if (-not $content.Contains("PlugInManager: using data dir: $weatherData")) {
        throw 'xWeatherRouting did not resolve its bundled data directory.'
    }
    if ($content.Contains('Loading WeatherRouting toolbar icon: data\weather_routing_pi.svg') -or
        $content.Contains('Failed to load image from file "data\weather_routing_panel.png"')) {
        throw 'xWeatherRouting fell back to an invalid relative icon path.'
    }
    if (-not $content.Contains('Full chart-aware safety available')) {
        throw 'xWeatherRouting did not connect to the chart-aware core API.'
    }
    if (-not $content.Contains('initialization complete; package_loaded=1')) {
        throw 'OfflineTides did not open the bundled authenticated dataset.'
    }
    $app.Refresh()
    if ($app.MainWindowTitle -notlike '*64-bit Preview*') { throw 'Preview window identity is missing.' }
    $modules = @($app.Modules | ForEach-Object { $_.FileName })
    foreach ($plugin in $plugins) {
        if (-not ($modules | Where-Object { [IO.Path]::GetFileName($_) -eq $plugin })) {
            throw "The runtime module list is missing $plugin"
        }
    }
    foreach ($module in $modules) {
        if (-not $module.StartsWith($stagePath + '\', [StringComparison]::OrdinalIgnoreCase) -and
            -not $module.StartsWith($env:SystemRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            throw "Runtime dependency was loaded from outside the bundle/Windows: $module"
        }
    }
    $modules | ConvertTo-Json | Set-Content (Join-Path $evidencePath 'loaded-modules.json')
    Save-Screenshot
    [void]$app.CloseMainWindow()
    if (-not $app.WaitForExit(20000)) { throw 'The Preview did not close cleanly.' }
    if ($app.ExitCode -ne 0) { throw "The Preview returned exit code $($app.ExitCode)." }
    if ((Profile-Snapshot) -ne $before) { throw 'An ordinary OpenCPN profile was changed.' }
    @{
        initialized_plugins = $plugins
        native_chart_safety_connection = $true
        bundled_tides_loaded = $true
        ordinary_profiles_unchanged = $true
        forbidden_profile_overrides_rejected = $true
        packaged_https_verified = $true
        private_profile = $profile
        gui_mode = 'software rendering'
    } | ConvertTo-Json | Set-Content (Join-Path $evidencePath 'result.json')
} finally {
    $env:PATH = $savedPath
    if ($null -ne $app -and -not $app.HasExited) {
        try {
            @($app.Modules | ForEach-Object { $_.FileName }) | ConvertTo-Json |
                Set-Content (Join-Path $evidencePath 'loaded-modules-at-exit.json')
            Save-Screenshot
        } catch { Write-Warning "Could not retain final GUI diagnostics: $_" }
        Stop-Process -Id $app.Id -Force
    }
    if (Test-Path $log) { Copy-Item $log $evidencePath }
    Copy-Item (Join-Path $profile 'opencpn.ini') (Join-Path $evidencePath 'preview-test-profile.ini')
}
