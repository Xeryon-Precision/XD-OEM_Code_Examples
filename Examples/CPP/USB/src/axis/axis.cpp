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

#include <chrono>
#include <thread>
#include <fstream>
#include <filesystem>
#include "xeryon/axis/axis.hpp"
#include "xeryon/logging/xlog.hpp"
#include "xeryon/controller/controller.hpp"

namespace xeryon
{

    Axis::Axis(char id, XController* XController)
        : id_(id), XController_(XController)
    {
    }

    long double Axis::to_internal(const UnitConverter& v) const
    {
        return v.canonical();
    }

    int Axis::to_counts(long double value) const
    {
        if (is_rotary_)
        {
            if (counts_per_rev_ <= 0)
                return 0;

            return static_cast<int>(
                std::llround(
                    value * counts_per_rev_ / 360.0L));
        }

        if (units_per_count_ <= 0)
            return 0;

        return static_cast<int>(
            std::llround(
                value / units_per_count_));
    }

    void Axis::setUnit(Unit u)
    {
        default_unit_ = u;
    }

    UnitConverter Axis::from_value(long double v) const
    {
        return UnitConverter(v, default_unit_);
    }

    std::string Axis::prefix() const
    {
        return std::string(1, id_) + ":";
    }

    void Axis::update(const std::string& key, int value)
    {
        std::lock_guard<std::mutex> lock(mutex_);
        data_[key] = value;
    }

    bool Axis::wait_position(int timeout_ms)
    {
        auto start = std::chrono::steady_clock::now();

        XController_->set_info_mode(InfoMode::Off);

        std::this_thread::sleep_for(std::chrono::milliseconds(100));

        while (true)
        {
            int stat = XController_->strong_value(prefix() + "STAT=?");

            if (stat & (1 << 10))
            {
                restoreInfo();
                return true;
            }

            if (stat & ((1 << 14) | (1 << 15) | (1 << 16) |
                (1 << 18) | (1 << 21)))
            {
                XLOG("Motion aborted due to status flag");
                restoreInfo();
                return false;
            }

            if (std::chrono::steady_clock::now() - start >
                std::chrono::milliseconds(timeout_ms))
            {
                restoreInfo();
                return false;
            }

            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
    }

    void Axis::set_model(const std::string& model)
    {
        std::lock_guard<std::mutex> lock(mutex_);

        model_ = model;

        for (const auto& s : stage_table)
        {
            if (model == s.model)
            {
                units_per_count_ = s.units_per_count;
                speed_multiplier_ = s.speed;
                counts_per_rev_ = s.counts_per_rev;
                is_rotary_ = s.is_rotary;

                XLOG("Axis " << id_
                    << " Model: " << model_
                    << " Units/Count: " << units_per_count_
                    << " Speed: " << speed_multiplier_
                    << " Rotary: " << is_rotary_);

                return;
            }
        }

        XLOG("Unknown model: " << model_);

        units_per_count_ = 0.0;
        speed_multiplier_ = 1.0;
        counts_per_rev_ = 0.0;
        is_rotary_ = false;
    }

    int Axis::get_value(const std::string& key)
    {
        std::string full_key = prefix() + key;

        if (auto cached = XController_->cached_value(full_key); cached.has_value())
            return *cached;

        auto resp = XController_->query(full_key + "=?");

        if (resp.empty())
            return 0;

        auto pos = resp.find('=');
        if (pos == std::string::npos || pos + 1 >= resp.size())
            return 0;

        try
        {
            int val = std::stoi(resp.substr(pos + 1));
            update(key, val);
            XController_->update_cache(full_key, val);
            return val;
        }
        catch (...)
        {
            return 0;
        }
    }

    bool Axis::applyDefaultSettings(const std::string& customPath)
    {
        enable_info_log(false);
        std::this_thread::sleep_for(std::chrono::milliseconds(100));

        const std::string filename =
            customPath.empty() ? "config/settings_default.txt" : customPath;

        std::string absPath = std::filesystem::absolute(filename).string();
        XLOG("Reading settings from: " + absPath);

        std::ifstream file;
        file.open(absPath, std::ios::in);

        if (!file.is_open())
        {
            XController_->send(prefix() + "LOAD");
            XLOG("settings file not found! using internal settings");
            return true;
        }

        std::string line;

        while (std::getline(file, line))
        {
            size_t start = line.find_first_not_of(" \t\r\n");
            if (start == std::string::npos) continue;
            line = line.substr(start);

            if (line.empty() || line[0] == '%')
                continue;

            size_t commentPos = line.find('%');
            if (commentPos != std::string::npos)
                line = line.substr(0, commentPos);

            if (line.find("MMAS") != std::string::npos ||
                line.find("UART") != std::string::npos ||
                line.find("PWMF") != std::string::npos ||
                line.find("STPS") != std::string::npos ||
                line.find("LEAD") != std::string::npos ||
                line.find("FLAG") != std::string::npos)
            {
                continue;
            }

            size_t end = line.find_last_not_of(" \t\r\n");
            if (end == std::string::npos) continue;
            line = line.substr(0, end + 1);

            size_t eq = line.find('=');
            if (eq == std::string::npos) continue;

            std::string tag = line.substr(0, eq);
            std::string value = line.substr(eq + 1);

            auto trim = [](std::string& s)
                {
                    size_t s1 = s.find_first_not_of(" \t\r\n");
                    size_t s2 = s.find_last_not_of(" \t\r\n");
                    if (s1 == std::string::npos) { s.clear(); return; }
                    s = s.substr(s1, s2 - s1 + 1);
                };

            trim(tag);
            trim(value);

            value = applySettingMultipliers(tag, value);

            XLOG("SETTINGS << " + tag + "=" + value);

            if (tag.find("INFO") != std::string::npos)
                continue; // Ignore
            else
                XController_->send(tag + "=" + value);

            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }

        file.close();
        std::this_thread::sleep_for(std::chrono::milliseconds(100));

        return true;
    }

    std::string Axis::applySettingMultipliers(const std::string& tag,
        const std::string& value)
    {
        try
        {
            if (tag.find("MAMP") != std::string::npos ||
                tag.find("MIMP") != std::string::npos ||
                tag.find("OFSA") != std::string::npos ||
                tag.find("OFSB") != std::string::npos ||
                tag.find("AMPL") != std::string::npos ||
                tag.find("MAM2") != std::string::npos)
            {
                return std::to_string((int)(std::stoi(value) * amplitudeMultiplier_));
            }

            if (tag.find("PHAC") != std::string::npos ||
                tag.find("PHAS") != std::string::npos)
            {
                return std::to_string((int)(std::stoi(value) * phaseMultiplier_));
            }

            if (tag.find("SSPD") != std::string::npos ||
                tag.find("MSPD") != std::string::npos ||
                tag.find("ISPD") != std::string::npos)
            {
                return std::to_string((int)(std::stof(value) * speed_multiplier_));
            }

            if (tag.find("LLIM") != std::string::npos ||
                tag.find("RLIM") != std::string::npos ||
                tag.find("HLIM") != std::string::npos ||
                tag.find("ZON1") != std::string::npos ||
                tag.find("ZON2") != std::string::npos)
            {
                long double intVal = std::stof(value);
                long double nm = to_internal(from_value(intVal));
                return std::to_string(to_counts(nm));
            }

            return value;
        }
        catch (...)
        {
            return value;
        }
    }

    void Axis::restoreInfo()
    {
        XController_->restore_info_mode();
    }

    void Axis::saveSettings()
    {
        XController_->send(prefix() + "SAVE");
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    void Axis::rsetSettings()
    {
        XController_->send(prefix() + "RSET");
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    bool Axis::isThermalProtection1() { return get_value("STAT") & (1 << 2); }
    bool Axis::isThermalProtection2() { return get_value("STAT") & (1 << 3); }
    bool Axis::isEncoderValid() { return get_value("STAT") & (1 << 8); }
    bool Axis::isPositionReached() { return get_value("STAT") & (1 << 10); }
    bool Axis::isScanning() { return get_value("STAT") & (1 << 13); }
    bool Axis::isAtLeftEnd() { return get_value("STAT") & (1 << 14); }
    bool Axis::isAtRightEnd() { return get_value("STAT") & (1 << 15); }
    bool Axis::isErrorLimit() { return get_value("STAT") & (1 << 16); }
    bool Axis::isSafetyTimeoutTriggered() { return get_value("STAT") & (1 << 18); }
    bool Axis::isPositionFailTriggered() { return get_value("STAT") & (1 << 21); }

    void Axis::enable_info_log(bool mode)
    {
        XController_->log_info(mode);
    }

    bool Axis::is_ready() const
    {
        return units_per_count_ > 0.0;
    }

    bool Axis::setDPOS(long double value)
    {
        if (!is_ready())
            return false;

        UnitConverter d = from_value(value);

        int counts = to_counts(to_internal(d));

        XController_->send(prefix() + "DPOS=" + std::to_string(counts));
        was_valid_dpos_ = true;

        return wait_position(2000);
    }

    bool Axis::setStep(long double value)
    {
        if (!is_ready())
            return false;

        UnitConverter d = from_value(value);

        int step_counts = to_counts(to_internal(d));

        XController_->send(prefix() + "STEP=" + std::to_string(step_counts));
        return true;
    }

    void Axis::setSpeed(long double value)
    {
        if (!is_ready())
            return;

        UnitConverter d = from_value(value);

        int nm = static_cast<int>(to_internal(d));
        int scaled = static_cast<int>(nm * speed_multiplier_);

        XController_->send(prefix() + "SSPD=" + std::to_string(scaled));
    }

    void Axis::setScan(int direction)
    {
        XController_->send(prefix() + "SCAN=" + std::to_string(direction));
    }

    void Axis::setScan(int direction, int ms)
    {
        XController_->send(prefix() + "SCAN=" + std::to_string(direction));
        std::this_thread::sleep_for(std::chrono::milliseconds(ms));
        XController_->send(prefix() + "SCAN=0");
    }

    void Axis::stopScan()
    {
        XController_->send(prefix() + "SCAN=0");
    }

    void Axis::index(int direction)
    {
        XController_->send(prefix() + "INDX=" + std::to_string(direction));
        was_valid_dpos_ = false;
    }

    void Axis::auto_index()
    {
        XController_->send(prefix() + "INDA=1");
    }

    void Axis::home()
    {
        XController_->send(prefix() + "HOME");
    }

    void Axis::reset()
    {
        XController_->send(prefix() + "RSET=0");
        was_valid_dpos_ = false;
    }

    std::string Axis::queryCMD(const std::string& cmd)
    {
        return XController_->query(prefix() + cmd);
    }

    void Axis::sendCMD(const std::string& cmd)
    {
        XController_->send(prefix() + cmd);
    }

    void Axis::sendCMD(std::string cmd, int val)
    {
        XController_->send(prefix() + cmd + "=" + std::to_string(val));
    }

    void Axis::enableDrive()
    {
        XController_->send(prefix() + "ENBL=1");
    }

    void Axis::readSettings()
    {
        XController_->query(prefix() + "HLIM=?");
        XController_->query(prefix() + "LLIM=?");
        XController_->query(prefix() + "SSPD=?");
        XController_->query(prefix() + "PTO2=?");
        XController_->query(prefix() + "PTOL=?");
    }

}
