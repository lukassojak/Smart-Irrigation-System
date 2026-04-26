import http from "./http"

export const getLiveSnapshot = async () => {
    const response = await http.get("/runtime/statuses/live")
    const data = response.data

    return {
        overview: {
            zonesOnline: data.overview.zones_online,
            totalZones: data.overview.total_zones,
            warnings: data.overview.warnings,
            errors: data.overview.errors
        },
        zones: data.zones.map(z => ({
            id: z.id,
            name: z.name,
            status: z.status,
            enabled: z.enabled,
            online: z.online,
            stale: z.stale,
            connectingToNode: z.connecting_to_node,
            lastRun: new Date(z.last_run),
            progress: z.progress_percent
        })),
        alerts: data.alerts.map(a => ({
            id: a.id,
            type: a.type,
            title: a.title,
            message: a.message,
            timestamp: new Date(a.timestamp)
        })),
        currentTasks: data.current_tasks.map(t => ({
            id: t.id,
            zoneName: t.zone_name,
            progress: t.progress_percent,
            currentVolume: t.current_volume,
            targetVolume: t.target_volume,
            remainingMinutes: t.remaining_minutes,
            stale: t.stale
        })),
        lastUpdate: new Date(data.last_update)
    }
}

export const getTodaySnapshot = async () => {
    const response = await http.get("/runtime/statuses/today")
    const data = response.data

    return {
        overview: {
            tasksTotal: data.overview.tasks_total,
            tasksPlanned: data.overview.tasks_planned,
            tasksInProgress: data.overview.tasks_in_progress,
            tasksCompleted: data.overview.tasks_completed,
            totalExpectedVolume: data.overview.total_expected_volume
        },
        tasks: data.tasks.map(t => ({
            id: t.id,
            zoneId: t.zone_id,
            zoneName: t.zone_name,
            scheduledTime: new Date(t.scheduled_time),
            expectedVolume: t.expected_volume_liters,
            expectedAdjustmentPercent: t.expected_adjustment_percent,
            status: t.status
        })),
        lastUpdate: new Date(data.last_update)
    }
}

export const startIrrigation = async ({
    zoneId,
    targetVolume,
    waitForResponse = true,
    timeoutSeconds = 5,
}) => {
    const response = await http.post(
        "/runtime/control/start-irrigation",
        {
            zone_id: Number(zoneId),
            liter_amount: Number(targetVolume),
        },
        {
            params: {
                wait_for_response: waitForResponse,
                timeout_seconds: timeoutSeconds,
            },
        },
    )

    return response.data
}

export const stopZone = async ({
    zoneId,
    waitForResponse = true,
    timeoutSeconds = 5,
}) => {
    const response = await http.post(
        "/runtime/control/stop-zone",
        {
            zone_id: Number(zoneId),
        },
        {
            params: {
                wait_for_response: waitForResponse,
                timeout_seconds: timeoutSeconds,
            },
        },
    )

    return response.data
}

export const stopIrrigation = async ({
    waitForResponse = true,
    timeoutSeconds = 5,
} = {}) => {
    const response = await http.post(
        "/runtime/control/stop-irrigation",
        null,
        {
            params: {
                wait_for_response: waitForResponse,
                timeout_seconds: timeoutSeconds,
            },
        },
    )

    return response.data
}

export const discoverNodes = async () => {
    const response = await http.get("/runtime/discovery/devices")
    return response.data.map((device) => ({
        hardwareUid: device.hardware_uid,
        serialNumber: device.serial_number,
        hostname: device.hostname,
        nodeId: device.node_id,
        firstSeenAt: device.first_seen_at ? new Date(device.first_seen_at) : null,
        lastSeenAt: device.last_seen_at ? new Date(device.last_seen_at) : null,
        claimedAt: device.claimed_at ? new Date(device.claimed_at) : null,
        everSeen: device.ever_seen,
    }))
}

export const pairDiscoveredNode = async ({
    hardwareUid,
    minWaitSeconds = 2,
    timeoutSeconds = 8,
}) => {
    const response = await http.post(
        `/runtime/discovery/devices/${encodeURIComponent(hardwareUid)}/pair`,
        null,
        {
            params: {
                min_wait_seconds: minWaitSeconds,
                timeout_seconds: timeoutSeconds,
            },
        }
    )

    return {
        status: response.data.status,
        hardwareUid: response.data.hardware_uid,
        serialNumber: response.data.serial_number,
        hostname: response.data.hostname,
        lastSeenAt: response.data.last_seen_at ? new Date(response.data.last_seen_at) : null,
    }
}