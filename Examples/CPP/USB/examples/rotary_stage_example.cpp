#include <xeryon.hpp>
#include <thread>
#include <chrono>
#include <iostream>

using namespace xeryon;

static void wait_ms(int ms)
{
    auto end = std::chrono::steady_clock::now() + std::chrono::milliseconds(ms);

    while (std::chrono::steady_clock::now() < end)
    {
        std::this_thread::yield();
    }
}

int main()
{
    XController ctrl("COM8", 115200);

    if (!ctrl.connect())
    {
        std::cout << "Failed to connect XController\n";
        return -1;
    }

    Axis& axis = ctrl.axis();

    std::cout << "Waiting for stage detection...\n";
    while (!axis.is_ready())
        wait_ms(10);

    std::string configPath = R"(config\settings_default.txt)";
    axis.applyDefaultSettings(configPath);

    std::cout << "Axis ready!\n";

    axis.setUnit(Unit::DEG);

    axis.enableDrive();
    wait_ms(500);

    std::cout << "\n[1] INDEXING\n";

    axis.index(1);
    wait_ms(1000);

    std::cout << "\n[2] SCAN OSCILLATION\n";

    axis.setScan(-1);
    wait_ms(500);

    axis.setScan(1);
    wait_ms(500);

    axis.setScan(0);
    wait_ms(500);

    std::cout << "\n[3] SPEED SET\n";

    axis.setSpeed(10);   // deg/s
    wait_ms(500);

    axis.setScan(-1);
    wait_ms(500);

    axis.setScan(1);
    wait_ms(500);

    axis.setSpeed(30);
    wait_ms(500);

    axis.index(1);
    wait_ms(500);

    std::cout << "\n[4] POSITION SWEEP\n";

    axis.setDPOS(0);
    wait_ms(500);

    axis.setDPOS(45);
    wait_ms(500);

    axis.setDPOS(-45);
    wait_ms(500);

    axis.setDPOS(-120);
    wait_ms(500);

    axis.setDPOS(120);
    wait_ms(500);

    axis.setDPOS(-180);
    wait_ms(500);

    axis.setDPOS(180);
    wait_ms(500);

    axis.setDPOS(0);
    wait_ms(500);

    std::cout << "\n[5] HIGH SPEED MOTION\n";

    axis.setSpeed(60);
    wait_ms(500);

    axis.setDPOS(90);
    wait_ms(500);

    axis.setDPOS(-90);
    wait_ms(500);

    axis.setDPOS(0);
    wait_ms(500);

    std::cout << "\n[6] STEP LOOP (jogging)\n";

    axis.setSpeed(100);
    wait_ms(500);

    for (int i = 0; i < 180; ++i)
    {
        axis.setStep(1);   // 1 degree step
        wait_ms(100);
    }

    for (int i = 0; i < 360; ++i)
    {
        axis.setStep(-1);
        wait_ms(100);
    }

    axis.index(1);
    wait_ms(1000);

    for (int i = 0; i < 24; ++i)
    {
        axis.setStep(0.5);
        wait_ms(100);
    }

    for (int i = 0; i < 48; ++i)
    {
        axis.setStep(-0.5);
        wait_ms(100);
    }

    axis.setSpeed(10);
    wait_ms(500);

    axis.setDPOS(0);
    wait_ms(500);

    std::cout << "\n[7] MICRO STEP TEST\n";

    axis.setStep(0.5);
    wait_ms(500);

    axis.setStep(-0.5);
    wait_ms(500);

    std::cout << "\n[8] TIMED SCAN BURST\n";

    axis.setScan(-1);
    wait_ms(500);

    axis.setScan(0);
    wait_ms(500);

    axis.setScan(1);
    wait_ms(500);

    axis.setScan(0);
    wait_ms(500);

    std::cout << "\n[9] HOME\n";

    axis.home();
    wait_ms(1000);

    std::cout << "\nDone. Disconnecting...\n";
    ctrl.disconnect();

    return 0;
}