#pragma once

#include <string>
#include <fstream>
#include <regex>
#include <filesystem>
#include <cstdlib>
#include <climits>

namespace plot
{

    static double extractUnitsPerCount(const std::string& file)
    {
        std::ifstream in(file);
        std::string line;

        while (std::getline(in, line))
        {
            if (line.find("XLS") != std::string::npos ||
                line.find("XLA") != std::string::npos ||
                line.find("XRT") != std::string::npos)
            {
                auto pos = line.find('=');
                if (pos != std::string::npos)
                    return std::stod(line.substr(pos + 1));
            }
        }

        return 0.0;
    }

    inline bool buildCsv(double enc_resolution, const std::string& logFile, const std::string& csvFile)
    {
        std::ifstream in(logFile);
        if (!in.is_open())
            return false;

        double scale = (enc_resolution > 0.0) ? enc_resolution : extractUnitsPerCount(logFile);

        std::ofstream out(csvFile);
        out << "sample,epos_mm\n";

        std::string line;
        std::regex r_epos(R"(EPOS=([-]?\d+))");

        long long sample = 0;

        long long prev_raw = LLONG_MIN;
        double filtered = 0.0;

        const double alpha = 0.1; // keep sharp steps

        while (std::getline(in, line))
        {
            std::smatch m;

            if (std::regex_search(line, m, r_epos))
            {
                long long raw = std::stoll(m[1]);
                double epos_mm = (raw * scale) / 1000.0;

                if (prev_raw == LLONG_MIN)
                {
                    filtered = epos_mm;
                }
                else
                {
                    long long diff = std::llabs(raw - prev_raw);

                    if (diff < 50)
                        filtered = alpha * epos_mm + (1.0 - alpha) * filtered;
                    else
                        filtered = epos_mm;
                }

                prev_raw = raw;

                out << sample++ << "," << filtered << "\n";
            }
        }

        return true;
    }

    inline void plot(const std::string& csvFile)
    {
        std::ofstream gp("plot.gp");

        gp <<
            "set datafile separator ','\n"
            "set terminal pngcairo size 1400,800\n"
            "set output 'epos_sample.png'\n"
            "set title 'EPOS vs Sample'\n"
            "set xlabel 'Sample'\n"
            "set ylabel 'EPOS (mm)'\n"
            "set grid\n"
            "plot '" << csvFile << "' using 1:2 with lines title 'EPOS'\n"
            "set output\n";

        gp.close();

        system("\"C:\\Program Files\\gnuplot\\bin\\gnuplot.exe\" plot.gp");
    }

}
