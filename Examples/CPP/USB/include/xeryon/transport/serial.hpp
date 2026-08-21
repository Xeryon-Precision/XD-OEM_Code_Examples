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
#include "xeryon/transport/transport.hpp"

namespace xeryon
{

    class SerialTransport : public Transport
    {
    public:
        SerialTransport();
        ~SerialTransport();

        bool open(const std::string& port, int baudrate) override;
        void close() override;

        bool write(const std::string& data) override;
        std::string read() override;
        void flush_rx() override;
        std::mutex& rx_mutex() override { return rx_mutex_; }
    private:
        void* handle_;
        std::string rx_buffer_;
        std::mutex rx_mutex_;
        std::chrono::milliseconds timeout_{ 1000 };
    };

}
