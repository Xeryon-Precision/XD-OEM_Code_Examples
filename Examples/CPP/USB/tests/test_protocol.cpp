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
#include "xeryon/protocol/ascii/ascii_protocol.hpp"
#include "xeryon/command/channel.hpp"

using namespace xeryon;

#define TEST_ASSERT(cond) \
    if (cond) result.passed++; \
    else { result.failed++; std::cerr << "[FAIL] " << #cond << "\n"; }

TestResult run_protocol_tests()
{
    TestResult result;
    result.name = "AsciiProtocol";

    auto transport = std::make_shared<MockTransport>();

    auto info = std::make_shared<InfoListener>();

    AsciiProtocol protocol(transport, info);
    protocol.start();

    transport->open("", 0);

    // -------------------------------------------------
    // QUERY TEST
    // -------------------------------------------------

    transport->script_response("INFO=?", "INFO=2");
    transport->script_response("FREQ=?", "FREQ=85000");

    std::string r1 = protocol.query("INFO=?");
    TEST_ASSERT(r1.find("INFO=2") != std::string::npos);

    std::string r2 = protocol.query("FREQ=?");
    TEST_ASSERT(r2.find("85000") != std::string::npos);

    transport->script_response("BAD=?", "BAD=abc");

    std::string r3 = protocol.query("BAD=?");
    TEST_ASSERT(r3.find("abc") != std::string::npos);

    protocol.stop();

    return result;
}
