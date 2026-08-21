cmake_minimum_required(VERSION 3.16)

project(xeryon_sdk
    VERSION 1.0.0
    LANGUAGES CXX
)

# Prevent in-source builds (keeps repo clean)
if (CMAKE_SOURCE_DIR STREQUAL CMAKE_BINARY_DIR)
    message(FATAL_ERROR "Do not build in-source. Use: cmake -B build")
endif()


# =========================================================
# Options
# =========================================================
option(XERYON_ENABLE_LOG "Enable Xeryon logging" ON)
option(XERYON_BUILD_EXAMPLES "Build examples" ON)
option(XERYON_BUILD_UT "Build Unit Test" ON)

# =========================================================
# C++ Standard
# =========================================================
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# =========================================================
# Version header
# =========================================================
configure_file(
    ${PROJECT_SOURCE_DIR}/include/xeryon/version.h.in
    ${PROJECT_BINARY_DIR}/include/xeryon/version.h
    @ONLY
)

# =========================================================
# Windows version resource
# =========================================================
if(WIN32)
    configure_file(
        ${PROJECT_SOURCE_DIR}/cmake/version.rc.in
        ${PROJECT_BINARY_DIR}/version.rc
        @ONLY
    )
endif()

# =========================================================
# Common sources
# =========================================================
configure_file(
    ${CMAKE_SOURCE_DIR}/config/settings_default.txt
    ${CMAKE_BINARY_DIR}/config/settings_default.txt
    COPYONLY
)

set(XERYON_SOURCES
    src/axis/axis.cpp
    src/logging/xlog.cpp
    src/transport/serial.cpp
    src/command/channel.cpp
    src/protocol/ascii/info_listener.cpp
    src/controller/controller.cpp
    src/protocol/ascii/ascii_protocol.cpp
)

# =========================================================
# SHARED LIB (DLL / SO / DYLIB)
# =========================================================
add_library(xeryon_shared SHARED ${XERYON_SOURCES})

set_target_properties(xeryon_shared PROPERTIES
    OUTPUT_NAME "xeryon"
    VERSION ${PROJECT_VERSION}
    SOVERSION ${PROJECT_VERSION_MAJOR}
)

# Windows resource
if(WIN32)
    target_sources(xeryon_shared PRIVATE ${PROJECT_BINARY_DIR}/version.rc)
endif()

# =========================================================
# STATIC LIB (for embedded / deterministic builds)
# =========================================================
add_library(xeryon_static STATIC ${XERYON_SOURCES})

set_target_properties(xeryon_static PROPERTIES
    OUTPUT_NAME "xeryon_static"
)

# =========================================================
# Common includes
# =========================================================
foreach(TARGET xeryon_shared xeryon_static)

    target_include_directories(${TARGET}
        PUBLIC
            $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
            $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}/include>
    )

endforeach()

# =========================================================
# Logging define
# =========================================================
if(XERYON_ENABLE_LOG)
    target_compile_definitions(xeryon_shared PUBLIC XERYON_ENABLE_LOG)
    target_compile_definitions(xeryon_static PUBLIC XERYON_ENABLE_LOG)
endif()

# =========================================================
# Compiler warnings
# =========================================================
if(MSVC)
    target_compile_options(xeryon_shared PRIVATE /W4)
    target_compile_options(xeryon_static PRIVATE /W4)
else()
    target_compile_options(xeryon_shared PRIVATE -Wall -Wextra -Wpedantic)
    target_compile_options(xeryon_static PRIVATE -Wall -Wextra -Wpedantic)
endif()

# =========================================================
# Examples (choose SHARED by default)
# =========================================================
if(XERYON_BUILD_EXAMPLES)

    set(EXAMPLE_NAMES
        single_axis_example
        multi_axis_example
        1-axis-plot-example
        rotary_stage_example
    )

    foreach(NAME IN LISTS EXAMPLE_NAMES)

        add_executable(example_${NAME}
            examples/${NAME}.cpp
        )

        target_link_libraries(example_${NAME}
            PRIVATE xeryon_static
        )

    endforeach()

endif()

# =========================================================
# Install (PRODUCTION READY)
# =========================================================
include(GNUInstallDirs)

install(TARGETS xeryon_shared xeryon_static
    EXPORT xeryonTargets
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}   # DLL
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}   # SO / DYLIB
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}   # .lib / .a
)

install(DIRECTORY include/
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(FILES
    ${PROJECT_BINARY_DIR}/include/xeryon/version.h
    DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/xeryon
)

# =========================================================
# Unit Tests
# =========================================================
if(XERYON_BUILD_UT)

    enable_testing()

    add_executable(xeryon_tests
        tests/test_axis.cpp
        tests/test_channel.cpp
        tests/test_controller.cpp
        tests/test_protocol.cpp
        tests/test_main.cpp
    )

    target_include_directories(xeryon_tests
        PRIVATE
            ${PROJECT_SOURCE_DIR}/tests
    )

    target_link_libraries(xeryon_tests
        PRIVATE xeryon_static
    )

    # warnings for tests
    if(MSVC)
        target_compile_options(xeryon_tests PRIVATE /W4)
    else()
        target_compile_options(xeryon_tests PRIVATE -Wall -Wextra -Wpedantic)
    endif()

    add_test(NAME xeryon_unit_tests COMMAND xeryon_tests)

endif()

# =========================================================
# Licensing files (IMPORTANT)
# =========================================================
install(FILES
    ${CMAKE_SOURCE_DIR}/LICENSE
    ${CMAKE_SOURCE_DIR}/NOTICE
    DESTINATION ${CMAKE_INSTALL_DATAROOTDIR}/xeryon
)