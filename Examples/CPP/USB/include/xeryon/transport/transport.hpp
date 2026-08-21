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
#include <mutex>

namespace xeryon
{

    class Transport
    {
    public:
        virtual ~Transport() = default;

        virtual bool open(const std::string& target, int param) = 0;
        virtual void close() = 0;

        virtual bool write(const std::string& data) = 0;
        virtual std::string read() = 0;

        virtual void flush_rx() = 0;

        virtual std::mutex& rx_mutex() = 0;
    };

}
