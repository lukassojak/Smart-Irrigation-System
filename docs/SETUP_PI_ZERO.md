# Raspberry Pi Zero 2 W – Setup Guide

## 1. Flashing the OS
- Download Raspberry Pi OS Lite (64-bit).
- Flash it using Raspberry Pi Imager.
- Create a file named `ssh` in the boot partition to enable SSH.
- Setup WiFi connection in Raspberry Pi Imager.
- Name the device `irrigationX` (where `X` is the number of the irrigation node, e.g., `irrigation1`).

## 2. First login
```bash
ssh irrigationX@<IP_ADDRESS>
passwd
```

> When you expect the ssh session to be long-running, use `ssh -o ServerAliveInterval=60 irrigationX@<IP_ADDRESS>` to prevent disconnection.

## 3. Basic package installation
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv git screen
```

## 4. Clone the repository
```bash
git clone https://github.com/lukassojak/Smart-Irrigation-System.git
cd Smart-Irrigation-System
```

## 5. Install requirements
- The project requirements are defined in `requirements.txt`.
- For now, virtual environment is not used, but it is recommended to use one in the future.
```bash
pip3 install -r requirements.txt
```

## 6. WiFi watchdog
- The WiFi watchdog script is used to **monitor the WiFi connection and restart it if it goes down**. It helps to ensure that the irrigation system remains connected to the network, especially in case of temporary WiFi outages.
- Copy the [wifi_watchdog.sh](../tools/wifi_watchdog.sh) script to `/usr/local/bin/`.
- Add the script to the crontab to run regularly:
```bash
crontab -e
* * * * * /usr/local/bin/wifi_watchdog.sh
```

## 7. Run the irrigation system
- See [RUNNING.md](docs/RUNNING.md) for details on how to run the irrigation system.

