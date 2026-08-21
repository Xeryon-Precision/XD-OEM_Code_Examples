/*
 * Copyright 2026 Xeryon
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.
 */

#pragma once

#include <string>
#include <unordered_map>
#include <mutex>

#include "xeryon/axis/distance.hpp"
#include "xeryon/axis/stage.hpp"

namespace xeryon
{
    class XController;

    class Axis
    {
    public:
        Axis(char id, XController* XController);

        void setUnit(Unit u);
        bool setDPOS(long double value);
        bool setStep(long double value);

        void setSpeed(long double value);

        void setScan(int direction);
        void setScan(int direction, int ms);
        void stopScan();

        void index(int direction);
        void auto_index();

        void home();
        void reset();

        bool wait_position(int timeout_ms);

        void update(const std::string& key, int value);

        int get_value(const std::string& key);

        void set_model(const std::string& model);
        bool is_ready() const;

        std::string queryCMD(const std::string& cmd);
        void sendCMD(const std::string& cmd);
        void sendCMD(std::string cmd, int val);

        void saveSettings();
        void rsetSettings();
        void readSettings();
        bool applyDefaultSettings(const std::string& customPath = "");

        bool isThermalProtection1();
        bool isThermalProtection2();
        bool isEncoderValid();
        bool isPositionReached();
        bool isScanning();
        bool isAtLeftEnd();
        bool isAtRightEnd();
        bool isErrorLimit();
        bool isSafetyTimeoutTriggered();
        bool isPositionFailTriggered();


        void enable_info_log(bool mode);
        void enableDrive();

    private:
        std::string prefix() const;
        long double Axis::to_internal(const UnitConverter& v) const;
        int to_counts(long double nm) const;
        std::string applySettingMultipliers(const std::string& tag,
            const std::string& value);
        void restoreInfo();
        UnitConverter from_value(long double v) const;

    private:
        char id_;
        XController* XController_;

        std::string model_;

        Unit default_unit_{ Unit::MM };
        double units_per_count_{ 0 };
        double speed_multiplier_{ 1 };
        double counts_per_rev_{ 0 };
        bool is_rotary_{ false };

        bool was_valid_dpos_{ false };

        double amplitudeMultiplier_{ 1456.0 };
        double phaseMultiplier_{ 182 };

        std::unordered_map<std::string, int> data_;
        std::mutex mutex_;
    };

}
