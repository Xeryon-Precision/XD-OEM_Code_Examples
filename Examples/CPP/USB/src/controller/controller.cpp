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

#include "xeryon/controller/controller.hpp"
#include "xeryon/transport/serial.hpp"
#include "xeryon/logging/xlog.hpp"

namespace xeryon
{

    XController::XController(const std::string& port, int baudrate)
    {
        transport_ = std::make_shared<SerialTransport>();
        port_ = port;
        baudrate_ = baudrate;
    }

    XController::XController(std::shared_ptr<Transport> transport)
    {
        transport_ = transport;
    }

    XController::~XController()
    {
        disconnect();
    }

    bool XController::connect()
    {
        if (!transport_)
            transport_ = std::make_shared<SerialTransport>();

        if (!transport_->open(port_, baudrate_))
        {
            XLOG("Failed to open port");
            transport_.reset();
            return false;
        }

        info_ = std::make_shared<InfoListener>();
        info_->start();

        protocol_ = std::make_shared<AsciiProtocol>(transport_, info_);
        protocol_->start();

        command_ = std::make_unique<CommandChannel>(protocol_);

        set_info_mode(InfoMode::Mode2); //to register initial mode

        XLOG("XController connected");

        return true;
    }

    void XController::disconnect()
    {
        if (!transport_)
            return;

        {
            std::lock_guard<std::mutex> lock(transaction_mutex_);

            if (command_)
            {
                command_->send("ZERO=0");
                command_->send("STOP=0");
            }
        }

        if (protocol_)
            protocol_->stop();

        if (info_)
            info_->stop();

        transport_->close();

        command_.reset();
        protocol_.reset();
        info_.reset();
        transport_.reset();

        XLOG("XController disconnected");
    }

    void XController::log_info(bool en)
    {
        if (!info_)
            return;

        info_->set_logging(en);

        if (en)
        {
            set_info_mode(InfoMode::Mode4);
        }
        else
        {
            set_info_mode(InfoMode::Off);
        }
    }

    bool XController::set_info_mode(InfoMode mode)
    {
        bool rtn = false;
        std::lock_guard<std::mutex> lock(transaction_mutex_);

        if (!command_)
            return rtn;

        rtn = command_->send("INFO=" + std::to_string(static_cast<int>(mode)));

        if (info_)
            info_->set_mode(mode);
        return rtn;
    }

    void XController::restore_info_mode()
    {
        if (!info_)
            return;

        set_info_mode(info_->state().previous);
    }

    Axis& XController::axis()
    {
        return axis('A');
    }

    Axis& XController::axis(char id)
    {
        auto it = axes_.find(id);

        if (it == axes_.end())
        {
            auto axis = std::make_unique<Axis>(id, this);
            Axis* ptr = axis.get();

            axes_[id] = std::move(axis);

            if (info_)
                info_->register_axis(id, ptr);

            return *ptr;
        }

        return *(it->second);
    }

    CommandChannel& XController::commands()
    {
        return *command_;
    }

    bool XController::send(const std::string& cmd)
    {
        if (!command_)
            return false;

        auto pos = cmd.find('=');

        if (cmd.rfind("INFO", 0) == 0 && pos != std::string::npos)
        {
            int value = std::stoi(cmd.substr(pos + 1));
            return set_info_mode(static_cast<InfoMode>(value));
        }

        std::lock_guard<std::mutex> lock(transaction_mutex_);
        return command_->send(cmd);
    }

    std::string XController::query(const std::string& cmd)
    {
        if (!command_)
            return {};

        std::lock_guard<std::mutex> lock(transaction_mutex_);
        return command_->query(cmd);
    }

    void XController::update_cache(const std::string& key, int value)
    {
        std::lock_guard<std::mutex> lock(cache_mutex_);
        info_cache_[key] = { value, std::chrono::steady_clock::now() };
    }

    std::optional<int> XController::cached_value(const std::string& key)
    {
        std::lock_guard<std::mutex> lock(cache_mutex_);

        auto it = info_cache_.find(key);
        if (it == info_cache_.end())
            return std::nullopt;

        return it->second.value;
    }

    int XController::strong_value(const std::string& cmd)
    {
        if (!command_)
            return 0;

        auto rsp = command_->query(cmd);

        if (rsp.empty())
            return 0;

        auto eq = rsp.find('=');
        if (eq == std::string::npos || eq + 1 >= rsp.size())
            return 0;

        std::string value = rsp.substr(eq + 1);

        while (!value.empty() &&
            (value.back() == '\n' || value.back() == '\r' || value.back() == ' '))
            value.pop_back();

        while (!value.empty() &&
            (value.front() == ' ' || value.front() == '\t'))
            value.erase(value.begin());

        size_t space_pos = value.find_first_of(" \t");
        if (space_pos != std::string::npos)
            value = value.substr(0, space_pos);

        try
        {
            return std::stoi(value);
        }
        catch (...)
        {
            XLOG("stoi failed for: '" << value << "' raw=" << rsp);
            return 0;
        }
    }

}
