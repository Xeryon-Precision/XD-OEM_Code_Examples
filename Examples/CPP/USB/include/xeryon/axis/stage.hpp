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

#include <cmath>
#include <vector>

constexpr double PI = 3.14159265358979323846;

namespace
{
    struct StageInfo
    {
        const char* model;
        double units_per_count;
        double speed;
        double counts_per_rev;
        bool is_rotary;
    };

    static const std::vector<StageInfo> stage_table = {

        {"XLS1=312",      312.5, 1000.0, 0, false},
        {"XLS1=313",      312.5, 1000.0, 0, false},
        {"XLS1=1251",     1250.0, 1000.0, 0, false},
        {"XLS1=1250",     1250.0, 1000.0, 0, false},
        {"XLS1=78",       78.125, 1000.0, 0, false},
        {"XLS1=5",        5.0,    1000.0, 0, false},
        {"XLS1=1",        1.0,    1000.0, 0, false},

        {"XLS3=312",      312.5, 1000.0, 0, false},
        {"XLS3=313",      312.5, 1000.0, 0, false},
        {"XLS3=1251",     1250.0, 1000.0, 0, false},
        {"XLS3=1250",     312.5, 1000.0, 0, false},
        {"XLS3=78",       78.125, 1000.0, 0, false},
        {"XLS3=5",        5.0,    1000.0, 0, false},
        {"XLS3=1",        1.0,    1000.0, 0, false},

        {"XLS3=1000",     1000.0,  1000.0, 0, false},
        {"XLS3=250",      250.0,   1000.0, 0, false},
        {"XLS3=25",       25.0,    1000.0, 0, false},

        {"XLA1=312",      312.5, 1000.0, 0, false},
        {"XLA1=313",      312.5, 1000.0, 0, false},
        {"XLA1=1250",     1250.0, 1000.0, 0, false},
        {"XLA1=78",       78.125, 1000.0, 0, false},
        {"XLA1=0",        1.0,    1000.0, 0, false},

        {"XLA3=0",        1.0,    1000.0, 0, false},
        {"XLA3=312",      312.5, 1000.0, 0, false},
        {"XLA3=1250",     1250.0, 1000.0, 0, false},
        {"XLA3=78",       78.125, 1000.0, 0, false},

        {"XLA3=312_5N",   312.5, 1000.0, 0, false},
        {"XLA3=1250_5N",  1250.0, 1000.0, 0, false},
        {"XLA3=78_5N",    78.125, 1000.0, 0, false},

        {"XLA3=312_10N",  312.5, 1000.0, 0, false},
        {"XLA3=1250_10N", 1250.0, 1000.0, 0, false},
        {"XLA3=78_10N",   78.125, 1000.0, 0, false},

        {"XLA=312",       312.5, 1000.0, 0, false},
        {"XLA=1250",      1250.0, 1000.0, 0, false},
        {"XLA=78",        78.125, 1000.0, 0, false},

        {"XRTA=109",      (2 * PI * 1e6) / 57600.0, 100.0, 57600, true},

        {"XRT1=2",        (2 * PI * 1e6) / 2764800.0, 100.0, 2764800, true},
        {"XRT1=18",       (2 * PI * 1e6) / 345600.0,  100.0, 345600, true},
        {"XRT1=47",       (2 * PI * 1e6) / 135000.0,  100.0, 135000, true},
        {"XRT1=73",       (2 * PI * 1e6) / 86400.0,   100.0, 86400, true},

        {"XRT3=3",        (2 * PI * 1e6) / 2073600.0, 100.0, 2073600, true},
        {"XRT3=19",       (2 * PI * 1e6) / 324000.0,  100.0, 324000, true},
        {"XRT3=49",       (2 * PI * 1e6) / 129600.0,  100.0, 129600, true},
        {"XRT3=109",      (2 * PI * 1e6) / 64800.0,   100.0, 64800, true},

        {"XRTU=109",      (2 * PI * 1e6) / 57600.0, 100.0, 57600, true},
        {"XRTU=73",       (2 * PI * 1e6) / 86400.0, 100.0, 86400, true},
        {"XRTU=3",        (2 * PI * 1e6) / 1800000.0, 100.0, 1800000, true},

        {"XRT3=5",        (2 * PI * 1e6) / 2088000.0, 100.0, 2088000, true},
        {"XRT3=100",        (2 * PI * 1e6) / 57600.0, 100.0, 57600, true},
        {"XRT3=250",        (2 * PI * 1e6) / 28800.0, 100.0, 28800, true},

        {"XRT3=6",          (2 * PI * 1e6) / 2093280, 100.0, 2093280, true},
        {"XRT3=101",        (2 * PI * 1e6) / 64080, 100.0, 64080, true},
        {"XRT3=251",        (2 * PI * 1e6) / 21360, 100.0, 21360, true},

    };
}

