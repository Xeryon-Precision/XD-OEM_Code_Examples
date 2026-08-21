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
#include <future>
#include <optional>
#include <memory>
#include <atomic>

#include "xeryon/transport/transport.hpp"
#include "xeryon/protocol/ascii/info_listener.hpp"

namespace xeryon
{

    class AsciiProtocol
    {
    public:
        AsciiProtocol(std::shared_ptr<Transport> transport,
            std::shared_ptr<InfoListener> info);

        ~AsciiProtocol() = default;

        void start();
        void stop();

        bool send(const std::string& cmd);
        std::string query(const std::string& cmd);

    private:

        void reader_loop();
        void dispatch(const std::string& line);

        bool handle_command_response(const std::string& line);

        std::string normalize_key(const std::string& input);

    private:

        std::shared_ptr<Transport> transport_;

        std::shared_ptr<InfoListener> info_;

        std::thread reader_thread_;
        std::atomic<bool> running_{ false };

        std::mutex write_mutex_;

        struct PendingCommand
        {
            std::string key;
            std::promise<std::string> promise;
        };

        std::mutex cmd_mutex_;
        std::optional<PendingCommand> pending_command_;

        std::chrono::milliseconds timeout_{ 2000 };
    };

}
