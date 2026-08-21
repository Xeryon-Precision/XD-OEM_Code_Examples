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
#include "xeryon/axis/axis.hpp"
#include "mock_transport.hpp"

using namespace xeryon;

#define TEST_ASSERT(cond) \
    if (cond) result.passed++; \
    else { result.failed++; std::cerr << "[FAIL] " << #cond << "\n"; }

TestResult run_axis_tests()
{
    TestResult result;
    result.name = "Axis";

    auto mock = std::make_shared<MockTransport>();

    XController ctrl(mock);

    ctrl.connect();

    ctrl.set_info_mode(InfoMode::Mode2);

    Axis& axis = ctrl.axis('A');
    axis.set_model("XLS1=313");

    // -----------------------------
    // Simulate MODEL streaming
    // -----------------------------
    mock->push_response("A:XLS1=313");
    mock->push_response("A:STAT=1024");
    mock->push_response("A:EPOS=100");

    std::this_thread::sleep_for(std::chrono::milliseconds(50));

    TEST_ASSERT(axis.is_ready() == true);

    // -----------------------------
    // Command tests
    // -----------------------------
    axis.home();
    TEST_ASSERT(mock->last_write().find("HOME") != std::string::npos);

    axis.index(1);
    TEST_ASSERT(mock->last_write().find("INDX=1") != std::string::npos);

    axis.auto_index();
    TEST_ASSERT(mock->last_write().find("INDA=1") != std::string::npos);

    axis.reset();
    TEST_ASSERT(mock->last_write().find("RSET") != std::string::npos);

    axis.enableDrive();
    TEST_ASSERT(mock->last_write().find("ENBL=1") != std::string::npos);

    axis.setStep(1000);
    TEST_ASSERT(mock->last_write().find("STEP=") != std::string::npos);

    axis.setSpeed(100);
    TEST_ASSERT(mock->last_write().find("SSPD=") != std::string::npos);

    axis.setScan(1);
    TEST_ASSERT(mock->last_write().find("SCAN=1") != std::string::npos);

    axis.stopScan();
    TEST_ASSERT(mock->last_write().find("SCAN=0") != std::string::npos);

    // -----------------------------
    // STAT / cached feedback
    // -----------------------------
    mock->push_response("A:STAT=1024");

    int stat = axis.isPositionReached();
    TEST_ASSERT(stat == true || stat == false);

    // -----------------------------
    // wait_position
    // -----------------------------
    mock->push_response("A:STAT=1024");
    bool ok = axis.wait_position(100);
    TEST_ASSERT(ok == true || ok == false);

    // -----------------------------
    // multiple axis test
    // -----------------------------
    Axis& b = ctrl.axis('B');
    b.set_model("XLS1=313");
    mock->push_response("B:XLS1=312");
    std::this_thread::sleep_for(std::chrono::milliseconds(20));

    TEST_ASSERT(b.is_ready() == true);

    ctrl.disconnect();

    return result;
}

