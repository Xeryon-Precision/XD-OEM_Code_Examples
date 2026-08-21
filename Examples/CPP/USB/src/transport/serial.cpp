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

#include "xeryon/transport/serial.hpp"
#include "xeryon/logging/xlog.hpp"
#include "xeryon/transport/transport.hpp"

#ifdef _WIN32
#include <windows.h>
#else
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <thread>
#endif

namespace xeryon
{

    SerialTransport::SerialTransport()
        : handle_(nullptr)
    {
        rx_buffer_.reserve(1024);
    }

    SerialTransport::~SerialTransport()
    {
        close();
    }

    bool SerialTransport::open(const std::string& port, int baudrate)
    {
#ifdef _WIN32

        std::string fullPort = port;

        if (port.rfind("COM", 0) == 0 && port.size() > 4) {
            fullPort = "\\\\.\\" + port;
        }

        HANDLE h = CreateFileA(
            fullPort.c_str(),
            GENERIC_READ | GENERIC_WRITE,
            0,
            nullptr,
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL,
            0);

        if (h == INVALID_HANDLE_VALUE)
            return false;

        SetupComm(h, 4096, 4096);

        COMMTIMEOUTS timeouts = { 0 };
        timeouts.ReadIntervalTimeout = 10;
        timeouts.ReadTotalTimeoutConstant = 50;
        timeouts.ReadTotalTimeoutMultiplier = 0;
        timeouts.WriteTotalTimeoutConstant = 50;
        timeouts.WriteTotalTimeoutMultiplier = 0;

        if (!SetCommTimeouts(h, &timeouts)) {
            CloseHandle(h);
            return false;
        }

        DCB dcb = { 0 };
        dcb.DCBlength = sizeof(dcb);

        if (!GetCommState(h, &dcb)) {
            CloseHandle(h);
            return false;
        }

        dcb.BaudRate = baudrate;
        dcb.ByteSize = 8;
        dcb.StopBits = ONESTOPBIT;
        dcb.Parity = NOPARITY;
        dcb.fOutxCtsFlow = FALSE;
        dcb.fOutxDsrFlow = FALSE;
        dcb.fDtrControl = DTR_CONTROL_DISABLE;
        dcb.fRtsControl = RTS_CONTROL_DISABLE;
        dcb.fOutX = FALSE;
        dcb.fInX = FALSE;

        if (!SetCommState(h, &dcb)) {
            CloseHandle(h);
            return false;
        }

        PurgeComm(h, PURGE_RXCLEAR | PURGE_TXCLEAR);

        //Sleep(100);

        handle_ = h;

        XLOG("Serial opened: " << fullPort << " at baudrate: " << baudrate);

#else // LINUX

        int fd = ::open(port.c_str(), O_RDWR | O_NOCTTY | O_SYNC);

        if (fd < 0)
            return false;

        struct termios tty = {};
        if (tcgetattr(fd, &tty) != 0) {
            ::close(fd);
            return false;
        }

        // Set baudrate
        speed_t speed;
        switch (baudrate) {
        case 9600: speed = B9600; break;
        case 19200: speed = B19200; break;
        case 38400: speed = B38400; break;
        case 57600: speed = B57600; break;
        case 115200: speed = B115200; break;
        default:
            ::close(fd);
            return false;
        }

        cfsetospeed(&tty, speed);
        cfsetispeed(&tty, speed);

        tty.c_cflag = (tty.c_cflag & ~CSIZE) | CS8; // 8-bit chars
        tty.c_iflag &= ~IGNBRK;         // disable break processing
        tty.c_lflag = 0;                // no signaling chars, no echo
        tty.c_oflag = 0;                // no remapping, no delays
        tty.c_cc[VMIN] = 0;    // read doesn't block forever
        tty.c_cc[VTIME] = 5;    // 0.5 seconds read timeout
        tty.c_iflag &= ~(IXON | IXOFF | IXANY); // software flow control
        tty.c_cflag &= ~(PARENB | PARODD);      // no parity
        tty.c_cflag &= ~CSTOPB;                 // 1 stop bit
        tty.c_cflag &= ~CRTSCTS;                // no hardware flow control
        tty.c_cflag |= (CLOCAL | CREAD);

        if (tcsetattr(fd, TCSANOW, &tty) != 0) {
            ::close(fd);
            return false;
        }

        tcflush(fd, TCIOFLUSH);

        handle_ = reinterpret_cast<void*>((intptr_t)fd);

        XLOG("Serial opened: " << port << " at baudrate: " << baudrate);

#endif

        return true;
    }


    void SerialTransport::close()
    {
#ifdef _WIN32
        if (handle_)
        {
            CloseHandle((HANDLE)handle_);
            handle_ = nullptr;
            XLOG("Serial closed\n");
        }
#else
        if (handle_)
        {
            ::close((intptr_t)handle_);
            handle_ = nullptr;
            XLOG("Serial closed\n");
        }
#endif   
    }

    bool SerialTransport::write(const std::string& data)
    {
        if (!handle_)
            return false;

#ifdef _WIN32
        DWORD written;
        bool result = WriteFile(
            (HANDLE)handle_,
            data.c_str(),
            (DWORD)data.size(),
            &written,
            nullptr);
#else
        bool result = ::write(
            (intptr_t)handle_,
            data.c_str(),
            data.size()) > 0;
#endif
        return result;
    }

    std::string SerialTransport::read()
    {
        char buffer[1024]{};

        auto start = std::chrono::steady_clock::now();

        while (handle_)
        {
            if (std::chrono::steady_clock::now() - start > timeout_)
                return {};

#ifdef _WIN32
            DWORD readBytes = 0;

            if (ReadFile((HANDLE)handle_, buffer, sizeof(buffer), &readBytes, nullptr) && readBytes > 0)
            {
                rx_buffer_.append(buffer, readBytes);
            }
#else
            int n = ::read((intptr_t)handle_, buffer, sizeof(buffer));

            if (n > 0)
            {
                rx_buffer_.append(buffer, n);
            }
#endif

            while (true)
            {
                auto pos = rx_buffer_.find('\n');

                if (pos == std::string::npos)
                    break;

                std::string line = rx_buffer_.substr(0, pos);
                rx_buffer_.erase(0, pos + 1);

                if (!line.empty() && line.back() == '\r')
                    line.pop_back();

                if (!line.empty())
                    return line;
            }

            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }

        return {};
    }


    void SerialTransport::flush_rx()
    {
        std::lock_guard<std::mutex> lock(rx_mutex_);
        rx_buffer_.clear();

        char dump[256] = {0};

#ifdef _WIN32
        DWORD readBytes = 0;
        while (ReadFile((HANDLE)handle_, dump, sizeof(dump), &readBytes, nullptr)
            && readBytes > 0)
        {
            // discard
        }
#else
        while (::read((intptr_t)handle_, dump, sizeof(dump)) > 0)
        {
            // discard
        }
#endif
    }


}
