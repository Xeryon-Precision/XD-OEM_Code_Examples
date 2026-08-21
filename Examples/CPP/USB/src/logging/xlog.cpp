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

#include "xeryon/logging/xlog.hpp"

#include <iostream>
#include <fstream>
#include <mutex>
#include <chrono>
#include <ctime>
#include <filesystem>

namespace xeryon
{
    static std::mutex log_mutex;
    static std::ofstream log_file;
    static bool initialized = false;

    static void init_once()
    {
        if (initialized)
            return;

        initialized = true;

        std::filesystem::create_directories("./logs");

        auto now = std::chrono::system_clock::now();
        auto t = std::chrono::system_clock::to_time_t(now);

        std::tm tm{};
#ifdef _WIN32
        localtime_s(&tm, &t);
#else
        localtime_r(&t, &tm);
#endif

        char filename[64];
        std::strftime(filename, sizeof(filename),
            "log_%Y%m%d_%H%M%S.txt", &tm);

        std::string full_path = std::string("./logs/") + filename;

        log_file.open(full_path, std::ios::out | std::ios::app);

    }

    void xlog_print(const std::string& msg)
    {
#ifdef XERYON_ENABLE_LOG
        std::lock_guard<std::mutex> lock(log_mutex);

        if (!initialized)
            init_once();

        auto now = std::chrono::system_clock::now();
        auto t = std::chrono::system_clock::to_time_t(now);

        std::tm tm{};
#ifdef _WIN32
        localtime_s(&tm, &t);
#else
        localtime_r(&t, &tm);
#endif

        std::cout << msg << std::endl;

        char timebuf[32];
        std::strftime(timebuf, sizeof(timebuf), "%H:%M:%S", &tm);

        std::string final_msg = std::string("[") + timebuf + "] " + msg;

        if (log_file.is_open())
        {
            log_file << final_msg << std::endl;
            log_file.flush();
        }
#endif
    }

}
