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
#include <thread>
#include <mutex>
#include <queue>
#include <unordered_map>
#include <atomic>
#include <fstream>
#include <condition_variable>

#include "xeryon/axis/axis.hpp"

namespace xeryon
{

    enum class InfoMode : uint8_t
    {
        Off = 0,
        Mode1 = 1,
        Mode2 = 2,
        Mode3 = 3,
        Mode4 = 4,
        Mode5 = 5,
        Mode6 = 6,
        Mode7 = 7
    };

    struct InfoState
    {
        InfoMode current{ InfoMode::Off };
        InfoMode previous{ InfoMode::Off };
        bool logging{true};
    };

    class InfoListener
    {
    public:
        InfoListener();
        ~InfoListener();

        void start();
        void stop();

        void on_line(const std::string& line);

        void register_axis(char id, Axis* axis);

        void set_mode(InfoMode mode);
        void set_logging(bool en);

        const InfoState& state() const;

    private:
        void handle_line(const std::string& line);
        void log_run();

    private:
        std::atomic<bool> running_{ false };

        std::thread log_worker_;
        std::atomic<bool> log_running_{ false };

        std::mutex log_mutex_;
        std::condition_variable log_cv_;
        std::queue<std::string> log_queue_;
        std::ofstream info_file_;

        std::unordered_map<char, Axis*> axes_;
        std::unordered_map<char, std::string> model_cache_;

        InfoState state_;
        std::mutex state_mutex_;
    };

}
