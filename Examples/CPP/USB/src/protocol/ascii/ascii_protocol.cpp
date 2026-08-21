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

#include "xeryon/protocol/ascii/ascii_protocol.hpp"
#include "xeryon/logging/xlog.hpp"

#include <chrono>

namespace xeryon
{

    AsciiProtocol::AsciiProtocol(std::shared_ptr<Transport> transport,
        std::shared_ptr<InfoListener> info)
        : transport_(transport),
        info_(info)
    {
    }

    void AsciiProtocol::start()
    {
        running_ = true;
        reader_thread_ = std::thread(&AsciiProtocol::reader_loop, this);

        XLOG("ASCII protocol started");
    }

    void AsciiProtocol::stop()
    {
        running_ = false;

        if (reader_thread_.joinable())
            reader_thread_.join();
    }

    bool AsciiProtocol::send(const std::string& cmd)
    {
        std::lock_guard<std::mutex> lock(write_mutex_);
        return transport_->write(cmd + "\n");
    }

    std::string AsciiProtocol::query(const std::string& cmd)
    {
        std::promise<std::string> promise;
        auto future = promise.get_future();

        {
            std::lock_guard<std::mutex> lock(cmd_mutex_);
            pending_command_ = {
                normalize_key(cmd),
                std::move(promise)
            };
        }

        send(cmd);

        if (future.wait_for(timeout_) == std::future_status::timeout)
        {
            XLOG("CMD TIMEOUT >> " << cmd);
            return "";
        }

        return future.get();
    }

    void AsciiProtocol::reader_loop()
    {
        while (running_)
        {
            std::string line;

            try
            {
                line = transport_->read();
            }
            catch (...)
            {
                continue;
            }

            if (line.empty())
                continue;

            dispatch(line);
        }
    }

    void AsciiProtocol::dispatch(const std::string& line)
    {
        if (handle_command_response(line))
            return;

        if (info_)
            info_->on_line(line);
    }

    bool AsciiProtocol::handle_command_response(const std::string& line)
    {
        std::lock_guard<std::mutex> lock(cmd_mutex_);

        if (!pending_command_.has_value())
            return false;

        auto& pending = pending_command_.value();

        if (normalize_key(line) == pending.key)
        {
            XLOG("RSP << " << line);

            pending.promise.set_value(line);
            pending_command_.reset();
            return true;
        }

        return false;
    }


    std::string AsciiProtocol::normalize_key(const std::string& input)
    {
        std::string result = input;

        auto colon = result.find(':');
        if (colon != std::string::npos)
            result = result.substr(colon + 1);

        auto eq = result.find('=');
        if (eq != std::string::npos)
            result = result.substr(0, eq);

        auto start = result.find_first_not_of(" \t");
        auto end = result.find_last_not_of(" \t");

        if (start == std::string::npos)
            return "";

        return result.substr(start, end - start + 1);
    }

}
