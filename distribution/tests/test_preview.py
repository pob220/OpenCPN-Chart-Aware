import configparser
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("preview", Path(__file__).parents[1] / "preview.py")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


def config(text):
    result = configparser.ConfigParser(strict=False, interpolation=None)
    result.read_string(text)
    return result


class SetupTest(unittest.TestCase):
    def test_fresh_defaults(self):
        cfg = config(preview.initial_config("", "software"))
        self.assertEqual(cfg["PlugIns/libgrib_pi.so"]["bEnabled"], "0")
        self.assertEqual(cfg["PlugIns/libxgrib_pi.so"]["bEnabled"], "1")
        self.assertEqual(cfg["Settings"]["OpenGL"], "0")
        self.assertEqual(cfg["Settings/GlobalState"]["AllowArbitrarySystemPlugins"], "1")
        self.assertEqual(cfg["PlugIns/WeatherRouting"]["EnforceExperimentalChartSafety"], "1")

    def test_import_does_not_enable_vulkan_or_connections(self):
        original = "[Settings]\nOpenGL=1\nRendererBackend=vulkan-experimental\n[Settings/NMEADataSource]\nDataConnections=OUTBOUND\n[PlugIns/libunknown_pi.so]\nbEnabled=1\n"
        cfg = config(preview.initial_config(original, "software"))
        self.assertEqual(cfg["Settings"]["RendererBackend"], "software")
        self.assertEqual(cfg["Settings/NMEADataSource"]["DataConnections"], "")
        self.assertEqual(cfg["PlugIns/libunknown_pi.so"]["bEnabled"], "0")

    def test_explicit_opengl(self):
        self.assertEqual(config(preview.initial_config("", "opengl"))["Settings"]["OpenGL"], "1")

    @patch.object(preview, "check_stopped")
    def test_backup_and_import_keep_original_and_personal_routing(self, stopped):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source, dest = base / "old", base / "preview"
            (source / "plugins/weather_routing").mkdir(parents=True)
            (source / "plugins/lib/opencpn").mkdir(parents=True)
            (source / "opencpn.conf").write_text("[ChartDirectories]\nChartDir1=/charts\n")
            (source / "navobj.xml").write_text("<gpx/>")
            (source / "plugins/weather_routing/WeatherRoutingConfiguration.xml").write_text("<routes/>")
            (source / "plugins/weather_routing/chart_safety_tiles_v1.cache").write_bytes(b"cache")
            (source / "plugins/lib/opencpn/libbad_pi.so").write_bytes(b"binary")
            (source / "outside").symlink_to("/etc/passwd")
            before = (source / "opencpn.conf").read_bytes()
            profile = preview.initialize(dest, source)
            self.assertEqual((source / "opencpn.conf").read_bytes(), before)
            self.assertEqual((profile / "navobj.xml").read_text(), "<gpx/>")
            self.assertTrue((profile / "plugins/weather_routing/WeatherRoutingConfiguration.xml").exists())
            self.assertFalse((profile / "plugins/weather_routing/chart_safety_tiles_v1.cache").exists())
            self.assertFalse((profile / "plugins/lib/opencpn/libbad_pi.so").exists())
            self.assertFalse((profile / "outside").exists())
            backup = next(dest.glob("backup-*"))
            self.assertEqual((backup / "opencpn.conf").read_bytes(), before)
            manifest = json.loads((backup / "backup-manifest.json").read_text())
            self.assertIn("outside", manifest["excluded"])
            self.assertEqual(profile.stat().st_mode & 0o777, 0o700)
            with self.assertRaises(RuntimeError):
                preview.initialize(dest, source)

    @patch.object(preview, "check_stopped")
    def test_refuse_overlapping_profile(self, stopped):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "opencpn.conf").write_text("[Settings]\n")
            with self.assertRaises(RuntimeError):
                preview.initialize(root / "nested", root)
            self.assertFalse((root / "nested").exists())

    @patch.object(preview, "check_stopped", side_effect=RuntimeError("running"))
    def test_running_application_blocks_import(self, stopped):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(RuntimeError):
                preview.initialize(Path(temp) / "new")
            self.assertFalse((Path(temp) / "new").exists())

    def test_updates_remove_duplicate_values(self):
        text = "[Settings]\nOpenGL=1\n[Settings]\nOpenGL=1\nOther=a=b\n"
        updated = preview.config_updates(text, {("Settings", "OpenGL"): "0"})
        self.assertEqual(updated.count("OpenGL="), 1)
        self.assertIn("Other=a=b", updated)

    @patch.object(preview.os, "execve")
    def test_launcher_keeps_home_and_sets_isolation(self, execute):
        with patch.dict(preview.os.environ, {"WR_HEADLESS_ROUTE_TEST": "1"}):
            preview.launch(Path("/tmp/test-profile"), [])
        env = execute.call_args.args[2]
        self.assertEqual(env.get("HOME"), preview.os.environ.get("HOME"))
        self.assertNotIn("WR_HEADLESS_ROUTE_TEST", env)
        self.assertEqual(env["OPENCPN_CHART_AWARE_PROFILE"], "/tmp/test-profile")


if __name__ == "__main__":
    unittest.main()
