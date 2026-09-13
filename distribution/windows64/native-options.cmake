# Apply diagnostics after project() without replacing CMake's Windows flags.
include_guard(GLOBAL)
if (NOT MSVC OR NOT CMAKE_SIZEOF_VOID_P EQUAL 8)
  message(FATAL_ERROR "The Preview SDK requires native MSVC x64")
endif ()
add_compile_options(/we4302 /we4311 /we4312)
add_link_options(/LARGEADDRESSAWARE)
