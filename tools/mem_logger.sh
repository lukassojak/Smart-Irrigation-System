#!/bin/bash
# CPU and mem usage logger script

LOGFILE="/var/log/mem.log"



# Log the memory usage and top processes consuming memory
{
    echo "===== $(date) ====="
    free -h
    ps -eo pid,comm,%mem,%cpu --sort=-%mem | head -n 10
    echo "Uptime: $(uptime -p)"
    echo
} >> "$LOGFILE"