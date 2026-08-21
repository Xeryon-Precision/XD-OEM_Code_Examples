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
#include <vector>
#include "test_result.hpp"

// test modules
TestResult run_controller_tests();
TestResult run_protocol_tests();
TestResult run_channel_tests();
TestResult run_axis_tests();

static void print_result(const TestResult& r)
{
    std::cout << "\n============================\n";
    std::cout << "TEST SUITE: " << r.name << "\n";
    std::cout << "Passed: " << r.passed << "\n";
    std::cout << "Failed: " << r.failed << "\n";
    std::cout << "Total : " << r.total() << "\n";
    std::cout << "Coverage: " << r.coverage() << "%\n";
    std::cout << "============================\n";
}

int main()
{
    std::cout << "XERYON SDK TEST SUITE START\n";

    std::vector<TestResult> results;

    results.push_back(run_controller_tests());
    results.push_back(run_channel_tests());
    results.push_back(run_protocol_tests());
    results.push_back(run_axis_tests());


    int total_pass = 0;
    int total_fail = 0;

    for (const auto& r : results)
    {
        print_result(r);
        total_pass += r.passed;
        total_fail += r.failed;
    }

    std::cout << "\n============================\n";
    std::cout << "GLOBAL SUMMARY\n";
    std::cout << "Passed: " << total_pass << "\n";
    std::cout << "Failed: " << total_fail << "\n";
    std::cout << "Coverage: "
        << (100.0 * total_pass / (total_pass + total_fail))
        << "%\n";
    std::cout << "============================\n";

    return (total_fail == 0) ? 0 : -1;
}
