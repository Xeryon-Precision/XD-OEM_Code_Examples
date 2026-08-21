#include <iostream>
#include <fstream>
#include <string>
#include <sstream>
#include <regex>
#include <filesystem>
#include <xeryon.hpp>

#include "plot_helper.hpp"

using namespace xeryon;
namespace fs = std::filesystem;

static void wait_ms(int ms)
{
    auto end = std::chrono::steady_clock::now() + std::chrono::milliseconds(ms);

    while (std::chrono::steady_clock::now() < end)
    {
        std::this_thread::yield();
    }
}

static std::string getLatestLog(const std::string& folder)
{
    std::string path = folder + "/info.log";

    if (fs::exists(path))
        return path;

    return {};
}

int main()
{
    XController ctrl("COM8", 115200);

    if (!ctrl.connect())
        return -1;

    Axis& axis = ctrl.axis();

    while (!axis.is_ready())
        wait_ms(10);

    axis.applyDefaultSettings("");

    //Enable info logging mode to generate logs for plotting; default info=2
    //Logs will generate in build dir logs/info.log
    axis.enable_info_log(true);

    axis.setUnit(Unit::MM);

    axis.enableDrive();
    wait_ms(500);

    axis.index(1);
    wait_ms(1000);

    std::cout << "\n[2] SCAN OSCILLATION\n";

    axis.setScan(-1);
    wait_ms(1000);

    axis.setScan(1);
    wait_ms(1000);

    axis.setScan(0);
    wait_ms(1000);

    axis.index(1);
    wait_ms(500);

    std::cout << "\n[3] SPEED SET\n";
    axis.setSpeed(10);   // smooth scan speed
    wait_ms(500);

    // short scan burst
    axis.setScan(-1);
    wait_ms(2000);

    axis.setScan(1);
    wait_ms(3500);

    axis.setScan(-1);
    wait_ms(3500);

    axis.setSpeed(10);
    wait_ms(500);

    axis.index(1);
    wait_ms(500);

    std::cout << "\n[4] POSITION SWEEP\n";

    axis.setDPOS(0);
    wait_ms(500);

    axis.setDPOS(5);
    wait_ms(500);

    axis.setDPOS(-5);
    wait_ms(500);

    axis.setDPOS(-12.5);
    wait_ms(500);

    axis.setDPOS(12.5);
    wait_ms(500);

    axis.setDPOS(-12.5);
    wait_ms(500);

    axis.setDPOS(12.5);
    wait_ms(500);

    axis.setDPOS(0);
    wait_ms(500);

    std::cout << "\n[5] HIGH SPEED MOTION\n";

    axis.setSpeed(50);
    wait_ms(500);

    axis.setDPOS(10);
    wait_ms(500);

    axis.setDPOS(-10);
    wait_ms(500);

    axis.setDPOS(0);
    wait_ms(500);

    std::cout << "\n[6] STEP LOOP (jogging)\n";
    axis.setSpeed(1);
    wait_ms(500);

    for (int i = 0; i < 10; ++i)
    {
        axis.setStep(1);
        wait_ms(500);
    }

    for (int i = 0; i < 20; ++i)
    {
        axis.setStep(-1);
        wait_ms(500);
    }

    axis.setSpeed(10);
    wait_ms(500);

    axis.setDPOS(0);
    wait_ms(500);

    std::cout << "\n[7] MICRO STEP TEST\n";

    axis.setStep(5500);
    wait_ms(500);

    axis.setStep(-5500);
    wait_ms(500);

    std::cout << "\n[8] TIMED SCAN BURST\n";

    axis.setScan(-1);
    wait_ms(500);

    axis.setScan(0);
    wait_ms(500);

    axis.setScan(-1);
    wait_ms(500);

    axis.setScan(0);
    wait_ms(500);

    std::cout << "\n[9] HOME\n";
    axis.home();
    wait_ms(1000);

    std::cout << "\nDone. Disconnecting...\n";
    ctrl.disconnect();

    std::string logFile = getLatestLog("./logs");

    if (logFile.empty())
    {
        std::cout << "No log file found\n";
        return -1;
    }
    std::cout << "Logfile to plot: " + logFile << std::endl;

    std::string csvFile = "epos_time.csv";

    if (!plot::buildCsv(312.5, logFile, csvFile))
    {
        std::cout << "Parse failed\n";
        return -1;
    }

    plot::plot(csvFile);

    std::cout << "Done: epos_time.png\n";

    return 0;
}
