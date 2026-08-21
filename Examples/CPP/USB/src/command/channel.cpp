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

#include "xeryon/command/channel.hpp"
#include "xeryon/protocol/ascii/ascii_protocol.hpp"
#include "xeryon/logging/xlog.hpp"

#include <chrono>

namespace xeryon
{

    CommandChannel::CommandChannel(std::shared_ptr<AsciiProtocol> protocol)
        : protocol_(protocol)
    {
    }

    bool CommandChannel::send(const std::string& cmd)
    {
        std::lock_guard<std::mutex> lock(channel_mutex_);

        XLOG("CMD >> " << cmd);
        return protocol_->send(cmd);
    }

    std::string CommandChannel::query(const std::string& cmd)
    {
        XLOG("CMD >> " << cmd);
        return protocol_->query(cmd);
    }
}
