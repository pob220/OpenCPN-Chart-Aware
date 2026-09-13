#ifndef OCPN_WINDOWS64_PREVIEW_PATHS_H
#define OCPN_WINDOWS64_PREVIEW_PATHS_H
#ifdef OCPN_WINDOWS64_PREVIEW
#include <windows.h>
#include <shlobj.h>
#include <stdexcept>
#include <wx/filename.h>
#include <wx/stdpaths.h>

// Use the OS known folder, not HOME or an ordinary OpenCPN configuration path.
inline wxString Windows64PreviewProfile() {
  wchar_t folder[MAX_PATH];
  if (FAILED(SHGetFolderPathW(nullptr, CSIDL_LOCAL_APPDATA, nullptr,
                            SHGFP_TYPE_CURRENT, folder)))
    throw std::runtime_error("Cannot locate Windows Preview application data");
  return wxString(folder) + "\\OpenCPN-64bit-Preview\\profile";
}
#endif
#endif
