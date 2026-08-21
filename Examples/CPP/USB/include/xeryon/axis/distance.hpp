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

enum class Unit
{
    MM,
    UM,
    NM,
    DEG,
    RAD
};

class UnitConverter
{
public:

    explicit UnitConverter(long double value)
        : UnitConverter(value, Unit::MM)
    {
    }

    UnitConverter(long double value, Unit unit)
        : value_(toCanonical(value, unit))
        , unit_(unit)
    {
    }

    long double canonical() const
    {
        return value_;
    }

    long double to(Unit unit) const
    {
        return value_ / factor(unit);
    }

    bool isAngular() const
    {
        return unit_ == Unit::DEG ||
            unit_ == Unit::RAD;
    }

    Unit unit() const
    {
        return unit_;
    }

    UnitConverter operator-() const
    {
        return UnitConverter(-to(unit_), unit_);
    }

private:

    static constexpr long double PI =
        3.141592653589793238462643383279502884L;

    long double value_;
    Unit unit_;

    static long double toCanonical(long double value,
        Unit unit)
    {
        return value * factor(unit);
    }

    static long double factor(Unit unit)
    {
        switch (unit)
        {
        case Unit::MM:
            return 1'000'000.0L;

        case Unit::UM:
            return 1'000.0L;

        case Unit::NM:
            return 1.0L;

        case Unit::DEG:
            return 1.0L;

        case Unit::RAD:
            return 180.0L / PI;
        }

        return 1.0L;
    }
};

inline UnitConverter operator"" _mm(long double v)
{
    return UnitConverter(v, Unit::MM);
}

inline UnitConverter operator"" _mm(unsigned long long v)
{
    return UnitConverter(static_cast<long double>(v), Unit::MM);
}

inline UnitConverter operator"" _um(long double v)
{
    return UnitConverter(v, Unit::UM);
}

inline UnitConverter operator"" _um(unsigned long long v)
{
    return UnitConverter(static_cast<long double>(v), Unit::UM);
}

inline UnitConverter operator"" _nm(long double v)
{
    return UnitConverter(v, Unit::NM);
}

inline UnitConverter operator"" _nm(unsigned long long v)
{
    return UnitConverter(static_cast<long double>(v), Unit::NM);
}

inline UnitConverter operator"" _deg(long double v)
{
    return UnitConverter(v, Unit::DEG);
}

inline UnitConverter operator"" _deg(unsigned long long v)
{
    return UnitConverter(static_cast<long double>(v), Unit::DEG);
}

inline UnitConverter operator"" _rad(long double v)
{
    return UnitConverter(v, Unit::RAD);
}

inline UnitConverter operator"" _rad(unsigned long long v)
{
    return UnitConverter(static_cast<long double>(v), Unit::RAD);
}