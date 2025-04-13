# Distributed Load Balancer

Developed a distributed load balancer using a Flask web application integrated with Redis on WSL, facilitating dynamic task scheduling across multiple server controllers.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
  - [1. Setting Up WSL and VS Code](#1-setting-up-wsl-and-vs-code)
  - [2. Installing Docker in WSL](#2-installing-docker-in-wsl)
  - [3. Installing Redis in WSL](#3-installing-redis-in-wsl)
  - [4. Updating WSL Configuration](#4-updating-wsl-configuration)
  - [5. Cloning the Repository](#5-cloning-the-repository)
  - [6. Installing Python Dependencies](#6-installing-python-dependencies)
  - [7. Running the Services](#7-running-the-services)
- [Monitoring and Logs](#monitoring-and-logs)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

This project implements a distributed load balancer that dynamically schedules tasks across three server controllers. The system leverages:

- **Flask Web Application:** Offers a real-time Windows dashboard that displays up to 50 logs stored in Redis and provides start/stop controls for individual backend servers.
- **Redis for Centralized Logging:** Stores all logs and facilitates real-time monitoring.
- **Round-Robin Queue:** Distributes operations (prime checking, palindrome validation, reverse computation, Fibonacci calculation, and word count) evenly across servers.
- **Automated Health Checks:** Every second, the system checks server performance to ensure high availability and resilience.

## Features

- **Distributed Scheduling:** Dynamically assigns tasks among multiple backend servers.
- **Real-Time Monitoring:** Visualizes the latest 50 log entries from Redis in the Windows dashboard.
- **Dynamic Control:** Start or stop individual backend servers through the dashboard UI.
- **Periodic Health Checks:** Continuously monitors server performance with automated checks.
- **Centralized Logging:** Uses Redis to manage logs for streamlined real-time data tracking.

## Prerequisites

- **Windows 10/11** with [WSL](https://docs.microsoft.com/en-us/windows/wsl/install)
- **Visual Studio Code (VS Code)**
- **Docker** (installed on WSL)
- **Python 3.x**

## Installation and Setup

### 1. Setting Up WSL and VS Code

- **Install WSL:**  
  Follow the [Microsoft WSL installation guide](https://docs.microsoft.com/en-us/windows/wsl/install) to enable and configure WSL.
- **Install VS Code:**  
  Download and install [Visual Studio Code](https://code.visualstudio.com/).

### 2. Installing Docker in WSL

- Open your WSL terminal.
- Follow the official Docker installation guide for Ubuntu:  
  [Install Docker on Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

### 3. Installing Redis in WSL

- In your WSL terminal, run:
  ```bash
    docker pull redis
  ```
  This downloads the latest Redis Docker image.

### 4. Updating WSL Configuration

- Open (or create) the `/etc/wsl.conf` file in your WSL environment and add:
  ```bash
  [network]
  generateResolvConf = false
  ```
- Save the file and restart WSL:
  ```bash
  wsl --shutdown
  ```
  Then launch WSL again.

### 5. Cloning the Repository

- In your WSL terminal or Windows Command Prompt, run:
  ```bash
  git init  
  git pull https://github.com/Harsh971/Distributed-Load-Balancer.git
  ```
  This clones the project repository to your machine.

### 6. Installing Python Dependencies

- Open VS Code and navigate to your project folder.
- Open the integrated terminal in VS Code and run:
  ```bash
  pip install flask  
  pip install redis  
  pip install psutil
  ```
  These commands install the required libraries.

### 7. Running the Services

#### a. Start Redis in WSL

- In your WSL terminal, start Redis:
  ```bash
  sudo service redis-server start
  ```
- Verify the status:
  ```bash
  sudo service redis-server status
    ```

#### b. Start the Dashboard

- In VS Code's terminal, run:
  ```bash
  python dashboard.py
  ```
- This starts the Flask dashboard on `http://127.0.0.1:5000/`.

#### c. Start the Load Balancer

- Open a new terminal in VS Code or another instance and run:
  ```bash
  python load_balancer_async.py
  ```
- The load balancer listens on port `12000` and distributes tasks to the backend servers.

#### d. Access the Dashboard

- Open your browser and navigate to:
  ```bash
  http://127.0.0.1:5000/
  ```
- Use the dashboard to:
  - View server statuses
  - Start/stop individual servers
  - Submit operations for distributed processing
  - Monitor the latest 50 log entries from Redis

## Monitoring and Logs

- **Viewing Logs via Redis CLI:**
  - Open your WSL terminal and run:
    ```bash
    redis-cli
    ```
  - In the Redis CLI, view logs by executing:
    ```bash
    LRANGE lb_logs 0 49
    ```
- **Dashboard Logs:**  
  The dashboard UI displays the latest 50 log entries in real time.

## Project Structure

- **dashboard.py:**  
  Implements the Flask dashboard for monitoring and controlling servers.
- **server.py:**  
  Contains backend server logic for executing operations.
- **load_balancer_async.py:**  
  Manages task distribution to backend servers with a round-robin algorithm.
- **client.py:**  
  A simple client to test the load balancer's operation.

## Troubleshooting

- **Port Binding Issues:**  
  If you see permission errors or port conflicts, run your terminal as an Administrator and verify with netstat:
  ```bash
  netstat -ano | findstr :<port>
  ```
- **WSL Networking:**  
  Ensure your WSL IP remains current. Update any port proxy settings if the WSL IP changes.
- **Dependency Issues:**  
  Confirm all Python dependencies are installed with:
  ```bash
  pip install flask redis psutil
  ```
- **Service Startup:**  
  Run Redis, the dashboard, and the load balancer in separate terminals to ensure they start correctly.

## License

This project is licensed under the MIT License. See the LICENSE file for more information.
