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

#include "xeryon/transport/transport.hpp"

#include <string>
#include <queue>
#include <mutex>
#include <unordered_map>
#include <vector>
#include <chrono>
#include <thread>
#include <algorithm>

namespace xeryon
{

    class MockTransport : public Transport
    {
    public:
        MockTransport() = default;
        ~MockTransport() override = default;

        // =====================================================
        // LIFECYCLE
        // =====================================================

        bool open(const std::string& target, int param) override
        {
            (void)target;
            (void)param;
            opened_ = true;
            return true;
        }

        void close() override
        {
            opened_ = false;
        }

        // =====================================================
        // WRITE
        // =====================================================

        bool write(const std::string& data) override
        {
            if (!opened_)
                return false;

            std::lock_guard<std::mutex> lock(mutex_);

            last_write_ = data;
            write_history_.push_back(data);

            std::this_thread::sleep_for(std::chrono::milliseconds(delay_ms_));

            process_command_(data);
            return true;
        }

        // =====================================================
        // READ
        // =====================================================

        std::string read() override
        {
            auto start = std::chrono::steady_clock::now();

            while (opened_)
            {
                {
                    std::lock_guard<std::mutex> lock(mutex_);

                    if (!rx_queue_.empty())
                    {
                        std::string msg = rx_queue_.front();
                        rx_queue_.pop();
                        return msg;
                    }
                }

                if (std::chrono::steady_clock::now() - start > timeout_)
                    return "";

                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }

            return "";
        }

        void flush_rx() override
        {
            std::lock_guard<std::mutex> lock(mutex_);
            while (!rx_queue_.empty())
                rx_queue_.pop();
        }

        std::mutex& rx_mutex() override
        {
            return mutex_;
        }

        // =====================================================
        // TEST CONTROL API
        // =====================================================

        void push_response(const std::string& msg)
        {
            std::lock_guard<std::mutex> lock(mutex_);
            rx_queue_.push(msg + "\n");
        }

        void push_responses(const std::vector<std::string>& msgs)
        {
            std::lock_guard<std::mutex> lock(mutex_);
            for (const auto& m : msgs)
                rx_queue_.push(m + "\n");
        }

        void clear()
        {
            std::lock_guard<std::mutex> lock(mutex_);
            while (!rx_queue_.empty())
                rx_queue_.pop();
        }

        // =====================================================
        // ASSERTION HELPERS
        // =====================================================

        std::string last_write() const
        {
            return last_write_;
        }

        bool contains_write(const std::string& cmd) const
        {
            return std::find(write_history_.begin(),
                write_history_.end(),
                cmd) != write_history_.end();
        }

        const std::vector<std::string>& history() const
        {
            return write_history_;
        }

        // =====================================================
        // CONFIG
        // =====================================================

        void set_delay(int ms)
        {
            delay_ms_ = ms;
        }

        void set_timeout(std::chrono::milliseconds t)
        {
            timeout_ = t;
        }

        void script_response(const std::string& cmd, const std::string& response)
        {
            std::lock_guard<std::mutex> lock(mutex_);
            scripted_[normalize_(cmd)] = response + "\n";
        }

        void set_stat(int v)
        {
            std::lock_guard<std::mutex> lock(mutex_);
            stat_value_ = v;
        }

    private:

        // =====================================================
        // COMMAND ROUTING
        // =====================================================

        void process_command_(const std::string& cmd)
        {
            if (!rx_queue_.empty())
                return;

            std::string base = normalize_(cmd);

            auto it = scripted_.find(base);
            if (it != scripted_.end())
            {
                rx_queue_.push(it->second);
                return;
            }

            if (cmd.find("=?") != std::string::npos)
                handle_query_(cmd);
            else
                handle_command_(cmd);
        }

        void handle_query_(const std::string& cmd)
        {
            std::string prefix = extract_prefix_(cmd);

            if (cmd.find("STAT") != std::string::npos)
                rx_queue_.push(prefix + "STAT=" + std::to_string(stat_value_) + "\n");

            else if (cmd.find("EPOS") != std::string::npos)
                rx_queue_.push(prefix + "EPOS=100\n");

            else if (cmd.find("FREQ") != std::string::npos)
                rx_queue_.push("FREQ=85000\n");

            else if (cmd.find("INFO") != std::string::npos)
                rx_queue_.push("INFO=2\n");

            else
                rx_queue_.push(prefix + "ERR=UNKNOWN_QUERY\n");
        }

        void handle_command_(const std::string& cmd)
        {
            std::string prefix = extract_prefix_(cmd);

            if (cmd.find("HOME") != std::string::npos ||
                cmd.find("INDX") != std::string::npos ||
                cmd.find("SCAN") != std::string::npos ||
                cmd.find("DPOS") != std::string::npos ||
                cmd.find("STEP") != std::string::npos ||
                cmd.find("ENBL") != std::string::npos ||
                cmd.find("ZERO") != std::string::npos ||
                cmd.find("STOP") != std::string::npos)
            {
                rx_queue_.push(prefix + "OK\n");
            }
            else if (cmd.find("INFO") != std::string::npos)
            {
                rx_queue_.push("INFO=2\n");
            }
            else
            {
                rx_queue_.push(prefix + "OK\n");
            }
        }

        std::string normalize_(const std::string& cmd)
        {
            auto pos = cmd.find('=');
            if (pos != std::string::npos)
                return cmd.substr(0, pos + 1);
            return cmd;
        }

        std::string extract_prefix_(const std::string& cmd)
        {
            auto pos = cmd.find(':');
            if (pos != std::string::npos)
                return cmd.substr(0, pos + 1);
            return "";
        }

    private:
        bool opened_ = false;

        std::queue<std::string> rx_queue_;
        std::unordered_map<std::string, std::string> scripted_;

        std::string last_write_;
        std::vector<std::string> write_history_;

        mutable std::mutex mutex_;

        std::chrono::milliseconds timeout_{ 1000 };
        int delay_ms_ = 0;

        int stat_value_ = 0;
    };

}
