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

#include <filesystem>

#include "xeryon/protocol/ascii/info_listener.hpp"
#include "xeryon/logging/xlog.hpp"

namespace xeryon
{

    InfoListener::InfoListener() = default;

    InfoListener::~InfoListener()
    {
        stop();
    }

    void InfoListener::start()
    {
        if (running_)
            return;

        running_ = true;
        log_running_ = true;

        std::filesystem::create_directories("./logs");
        info_file_.open("./logs/info.log", std::ios::out | std::ios::trunc);

        log_worker_ = std::thread(&InfoListener::log_run, this);

        XLOG("INFO listener started");
    }

    void InfoListener::stop()
    {
        running_ = false;

        {
            std::lock_guard<std::mutex> lock(log_mutex_);
            log_running_ = false;
        }

        log_cv_.notify_all();

        if (log_worker_.joinable())
            log_worker_.join();

        if (info_file_.is_open())
        {
            info_file_.flush();
            info_file_.close();
        }

    }

    void InfoListener::set_mode(InfoMode mode)
    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        state_.previous = state_.current;
        state_.current = mode;
    }

    void InfoListener::set_logging(bool en)
    {
        std::lock_guard<std::mutex> lock(state_mutex_);
        state_.logging = en;
    }

    const InfoState& InfoListener::state() const
    {
        return state_;
    }

    void InfoListener::on_line(const std::string& line)
    {
        if (!running_ || !log_running_)
            return;

        if (state_.logging)
        {
            if(line.rfind("EPOS", 0) == 0 ||
               line.rfind("TIME", 0) == 0)
            {
                std::lock_guard<std::mutex> lock(log_mutex_);
                log_queue_.push(line);
            }
            log_cv_.notify_one();
        }

        if (state_.current == InfoMode::Off)
            return;

        handle_line(line);
    }

    void InfoListener::handle_line(const std::string& line)
    {
        if (line.empty())
            return;

        size_t eq = line.find('=');
        if (eq == std::string::npos)
            return;

        std::string lhs = line.substr(0, eq);
        std::string rhs = line.substr(eq + 1);

        char axis_id = 'A';

        size_t colon = lhs.find(':');
        if (colon != std::string::npos)
        {
            axis_id = lhs[0];
            lhs = lhs.substr(colon + 1);
        }

        std::string key = lhs;

        int value = 0;
        try
        {
            value = std::stoi(rhs);
        }
        catch (...)
        {
            return;
        }

        if (key.rfind("XLS", 0) == 0 ||
            key.rfind("XLA", 0) == 0 ||
            key.rfind("XRT", 0) == 0)
        {
            if (model_cache_.find(axis_id) == model_cache_.end())
            {
                model_cache_[axis_id] = key + "=" + rhs;

                auto it = axes_.find(axis_id);
                if (it != axes_.end() && !it->second->is_ready())
                    it->second->set_model(model_cache_[axis_id]);
            }
            return;
        }

        auto it = axes_.find(axis_id);
        if (it == axes_.end())
            return;

        it->second->update(key, value);
    }

    void InfoListener::register_axis(char id, Axis* axis)
    {
        axes_[id] = axis;

        auto it = model_cache_.find(id);
        if (it != model_cache_.end() && !axis->is_ready())
            axis->set_model(it->second);
    }

    void InfoListener::log_run()
    {
        std::vector<std::string> buffer;
        buffer.reserve(1024);

        std::unique_lock<std::mutex> lock(log_mutex_);

        while (true)
        {
            log_cv_.wait(lock, [this]
                {
                    return !log_queue_.empty() || !log_running_;
                });

            if (!log_running_ && log_queue_.empty())
            {
                lock.unlock();

                if (info_file_.is_open())
                    info_file_.flush();

                break;
            }

            while (!log_queue_.empty())
            {
                buffer.push_back(std::move(log_queue_.front()));
                log_queue_.pop();
            }

            lock.unlock();

            for (const auto& line : buffer)
            {
                info_file_ << line << '\n';
            }

            info_file_.flush();
            buffer.clear();

            lock.lock();
        }
    }

}
