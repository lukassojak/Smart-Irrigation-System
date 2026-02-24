import http from "./http"

export const getLiveSnapshot = async () => {
    const response = await http.get("/runtime/live")
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
            remainingMinutes: t.remaining_minutes
        })),
        lastUpdate: new Date(data.last_update)
    }
}

export const getTodaySnapshot = async () => {
    const response = await http.get("/runtime/today")
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