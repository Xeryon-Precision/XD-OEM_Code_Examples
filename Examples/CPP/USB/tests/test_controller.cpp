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
#include "xeryon/controller/controller.hpp"
#include "mock_transport.hpp"

using namespace xeryon;

#define TEST_ASSERT(cond) \
    if (cond) result.passed++; \
    else { result.failed++; std::cerr << "[FAIL] " << #cond << "\n"; }

TestResult run_controller_tests()
{
    TestResult result;
    result.name = "XController";

    auto mock = std::make_shared<MockTransport>();
    XController ctrl(mock);

    // -------------------------------------------------
    // CONNECT TEST
    // -------------------------------------------------
    TEST_ASSERT(ctrl.connect() == true);

    // INFO Mode2 should be sent during connect
    TEST_ASSERT(mock->last_write().find("INFO=2") != std::string::npos);

    // -------------------------------------------------
    // SEND NORMAL COMMAND
    // -------------------------------------------------
    ctrl.send("HOME");
    TEST_ASSERT(mock->last_write().find("HOME") != std::string::npos);

    ctrl.send("INDX=1");
    TEST_ASSERT(mock->last_write().find("INDX=1") != std::string::npos);

    // -------------------------------------------------
    // INFO special handling via send()
    // -------------------------------------------------
    ctrl.send("INFO=4");
    TEST_ASSERT(mock->last_write().find("INFO=4") != std::string::npos);

    // -------------------------------------------------
    // QUERY
    // -------------------------------------------------
    std::string resp = ctrl.query("INFO=?");
    TEST_ASSERT(resp.find("INFO=") != std::string::npos);

    // -------------------------------------------------
    // strong_value parsing
    // -------------------------------------------------
    mock->script_response("FREQ=?", "FREQ=85000");

    int value = ctrl.strong_value("FREQ=?");
    TEST_ASSERT(value == 85000);

    // malformed case
    mock->script_response("BAD=?", "BAD=abc");
    int bad = ctrl.strong_value("BAD=?");
    TEST_ASSERT(bad == 0);

    // -------------------------------------------------
    // AXIS MANAGEMENT
    // -------------------------------------------------
    Axis& a = ctrl.axis('A');
    Axis& b = ctrl.axis('B');

    TEST_ASSERT(&a != &b);

    // same axis must return same instance
    Axis& a2 = ctrl.axis('A');
    TEST_ASSERT(&a == &a2);

    // -------------------------------------------------
    // LOG INFO toggling
    // -------------------------------------------------
    ctrl.log_info(true);
    TEST_ASSERT(mock->last_write().find("INFO=7") != std::string::npos ||
                mock->last_write().find("INFO=7\n") != std::string::npos);

    ctrl.log_info(false);
    TEST_ASSERT(mock->last_write().find("INFO=0") != std::string::npos ||
                mock->last_write().find("INFO=0\n") != std::string::npos);

    // -------------------------------------------------
    // DISCONNECT
    // -------------------------------------------------
    ctrl.disconnect();

    std::string last = mock->last_write();

    TEST_ASSERT(
        last.find("ZERO=0") != std::string::npos ||
        last.find("STOP=0") != std::string::npos
    );


    return result;
}

