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

#include <iostream>
#include "test_result.hpp"
#include "mock_transport.hpp"

#include "xeryon/command/channel.hpp"
#include "xeryon/protocol/ascii/ascii_protocol.hpp"
#include "xeryon/protocol/ascii/info_listener.hpp"

using namespace xeryon;

#define TEST_ASSERT(cond) \
    if (cond) result.passed++; \
    else { result.failed++; std::cerr << "[FAIL] " << #cond << "\n"; }

TestResult run_channel_tests()
{
    TestResult result;
    result.name = "Channel";

    auto transport = std::make_shared<MockTransport>();
    transport->open("", 0);

    auto info = std::make_shared<InfoListener>();
    info->start();

    auto protocol = std::make_shared<AsciiProtocol>(transport, info);
    protocol->start();

    CommandChannel channel(protocol);

    channel.send("INFO=2");   // initialize state

    // -------------------------------------------------
    // SEND TEST
    // -------------------------------------------------
    TEST_ASSERT(channel.send("HOME"));
    TEST_ASSERT(transport->last_write().find("HOME") != std::string::npos);

    // -------------------------------------------------
    // QUERY TEST
    // -------------------------------------------------
    transport->script_response("INFO=?", "INFO=2");
    transport->script_response("FREQ=?", "FREQ=85000");

    std::string r1 = channel.query("INFO=?");
    TEST_ASSERT(r1.find("INFO=2") != std::string::npos);

    std::string r2 = channel.query("FREQ=?");
    TEST_ASSERT(r2.find("FREQ=85000") != std::string::npos);

    // -------------------------------------------------
    // cleanup
    // -------------------------------------------------
    protocol->stop();
    info->stop();
    transport->close();

    return result;
}


