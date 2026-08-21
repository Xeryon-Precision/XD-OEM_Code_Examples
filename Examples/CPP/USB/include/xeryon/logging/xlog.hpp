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
#include <sstream>

namespace xeryon
{
    void xlog_print(const std::string& msg);
}

#define XLOG(msg)                           \
    do {                                    \
        std::ostringstream oss;             \
        oss << msg;                         \
        xeryon::xlog_print(oss.str());      \
    } while (0)
