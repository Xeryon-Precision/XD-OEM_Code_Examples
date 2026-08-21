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
#include <memory>
#include <mutex>
#include <unordered_map>
#include <optional>
#include <chrono>

#include "xeryon/axis/axis.hpp"
#include "xeryon/transport/transport.hpp"
#include "xeryon/command/channel.hpp"
#include "xeryon/protocol/ascii/ascii_protocol.hpp"
#include "xeryon/protocol/ascii/info_listener.hpp"

namespace xeryon
{

    class XController
    {
    public:
        XController(const std::string& port, int baudrate);
        XController(std::shared_ptr<Transport> transport);
        ~XController();

        bool connect();
        void disconnect();

        bool set_info_mode(InfoMode mode);
        void log_info(bool en);
        void restore_info_mode();

        Axis& axis();
        Axis& axis(char id);

        CommandChannel& commands();

        bool send(const std::string& cmd);
        std::string query(const std::string& cmd);

        void update_cache(const std::string& key, int value);
        std::optional<int> cached_value(const std::string& key);

        int strong_value(const std::string& cmd);

    private:

        std::shared_ptr<Transport> transport_;
        std::shared_ptr<AsciiProtocol> protocol_;
        std::shared_ptr<InfoListener> info_;
        std::unique_ptr<CommandChannel> command_;

        std::string port_;
        int baudrate_{ 0 };

        std::unordered_map<char, std::unique_ptr<Axis>> axes_;

        struct CacheEntry
        {
            int value;
            std::chrono::steady_clock::time_point timestamp;
        };

        std::unordered_map<std::string, CacheEntry> info_cache_;
        std::mutex cache_mutex_;
        std::mutex transaction_mutex_;
    };

}
