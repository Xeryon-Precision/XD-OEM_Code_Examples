# Xeryon SDK

Cross-platform C++ SDK for controlling **Xeryon XControllers** and motion systems.

Supports:
- Single-axis and multi-axis controllers
- Real-time motion control
- Device tuning via configuration files
- Windows / Linux / macOS
- CMake-based integration

---

# Requirements

- CMake ≥ 3.16
- C++17 compatible compiler
- Visual Studio 2019+ (Windows) or GCC/Clang (Linux/macOS)

---

# Build Instructions

## Step 1 — Configure project

```
cmake -S . -B build
```
---

## Step 2 — Build SDK

```
Release build:
cmake --build build --config Release

Debug build:
cmake --build build --config Debug
```
---

## Step 3 — Install SDK (optional but recommended)

```
cmake --install build --config Release --prefix C:\XeryonSDK
```
---

# Installed SDK Structure

```
C:\XeryonSDK
 ├── include
 │    ├── xeryon
 │    │     ├── axis.hpp
 │    │     ├── controller.hpp
 │    │     └── ...
 │    └── xeryon.hpp        (main umbrella header)
 │
 ├── lib
 │    ├── xeryon_static.lib
 │    └── xeryon.lib (if shared enabled)
 │
 ├── bin
 │    └── xeryon.dll (if shared enabled)
 │
 └── share
      └── xeryon
           ├── LICENSE
           └── NOTICE
```
---

# Quick Usage Example

```
#include <xeryon.hpp>

using namespace xeryon;

int main()
{
    XController ctrl("COM7", 115200);
    if (!ctrl.connect()) return -1;

    Axis& axis = ctrl.axis();

    while (!axis.is_ready());
    axis.applyDefaultSettings("");

    axis.enableDrive();
    axis.home();

    axis.setSpeed(5_mm);
    axis.setDPOS(10_mm);

    ctrl.disconnect();
    return 0;
}
```

# Plotting (Optional)

The SDK supports optional motion data logging and visualization using Gnuplot.

Enable logging:

```
axis.applyDefaultSettings(""); // after this line
axis.enable_info_log(true);
```
This generates a log file with motion logs in:

```
./logs/info.log
```
Use the provided example utility (examples/plot_helper.hpp) to convert logs into CSV and generate a plot.
Refer example app with ploting examples/1-axis-plot-example.cpp

Output:

- CSV file with motion data
- PNG graph generated via Gnuplot

Requirement:

- Gnuplot must be installed on the system

This feature is intended for debugging and motion analysis. It may not provide real-time performance when logging is enabled.

---

# CMake Integration (Recommended)

```
cmake_minimum_required(VERSION 3.16)
project(app)

add_executable(app main.cpp)

target_include_directories(app PRIVATE
    "C:/XeryonSDK/include"
)

target_link_directories(app PRIVATE
    "C:/XeryonSDK/lib"
)

target_link_libraries(app PRIVATE xeryon_static)
```
---

# Configuration / Tuning File

The SDK uses a device-specific tuning file:

config/settings_default.txt

Example:
```
FREQ=173000
PROP=120
MSPD=200
SSPD=100
LLIM=-12.5
HLIM=12.5
```
Notes:
- Provided with the hardware or available on request from Xeryon
- Used for controller initialization and tuning
- May vary per device/model
- Loaded at runtime by the SDK

---

# Examples

- single_axis_example
- multi_axis_example
- 1-axis-plot-example

Build:

```
cmake -S . -B build
cmake --build build --config Release
```
---

# Features

- Motion control abstraction layer
- Position control (DPOS / STEP)
- Speed and scan control
- Device status monitoring
- Safety and limit handling
- Cached command system
- Cross-platform transport layer

---

# License

Apache License 2.0

You may:
- Use commercially
- Modify
- Redistribute
- Include in proprietary software

See LICENSE file for details.

---

# Notes

- Always use out-of-source builds (build/)
- Install step creates clean SDK distribution
- Examples are optional
- Recommended: use xeryon_static for deployment

---

# Typical Workflow

```
cmake -S . -B build
cmake --build build --config Release
cmake --install build --config Release --prefix C:\XeryonSDK
```
---

# Summary

Xeryon SDK provides a lightweight, cross-platform C++ interface for industrial motion control systems designed for production reliability and easy integration.
