#!/bin/bash

# Watchdog script to reconnect WiFi after disconnection


# IP address of the router (Access Point) to ping
ROUTER_IP="192.168.50.95"

# Try to ping the router twice with a timeout of 2 seconds
ping -c2 -W2 $ROUTER_IP > /dev/null 2>&1


# If the ping fails, log the event and restart wlan0
if [ $? -ne 0 ]; then
    echo "$(date): Wi-Fi disconnected, restarting wlan0..." | sudo tee -a /var/log/wifi-watchdog.log > /dev/null
    sudo ifconfig wlan0 down
    sleep 5
    sudo ifconfig wlan0 up
fi