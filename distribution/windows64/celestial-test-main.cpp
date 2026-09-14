// Keep wxWidgets available between the standalone plugin test groups.
#include <gtest/gtest.h>
#include <wx/app.h>
#include <wx/debug.h>
#include <wx/init.h>
#include <wx/log.h>

#include <cstdlib>
#include <iostream>
#include <memory>

int main(int argc, char** argv) {
  ::testing::InitGoogleTest(&argc, argv);
  std::unique_ptr<wxInitializer> wx;
  // The upstream opt-in GUI tests create and clean up their own application.
  if (!std::getenv("CELESTIAL_RUN_UI_TESTS")) {
    wx = std::make_unique<wxInitializer>();
    if (!wx->IsOk()) {
      std::cerr << "Unable to initialize wxWidgets for Celestial tests\n";
      return 1;
    }
    wxTheApp->SetAppName("celestial-windows64-tests");
  }
  delete wxLog::SetActiveTarget(new wxLogStderr());
  wxSetAssertHandler([](const wxString& file, int line, const wxString& function,
                        const wxString& condition, const wxString& message) {
    ADD_FAILURE() << file.ToStdString() << ':' << line << ' '
                  << function.ToStdString() << ' ' << condition.ToStdString()
                  << ' ' << message.ToStdString();
  });
  return RUN_ALL_TESTS();
}
