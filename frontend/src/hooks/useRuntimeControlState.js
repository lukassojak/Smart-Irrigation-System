import { useCallback, useMemo, useState } from "react"
import { stopIrrigation as stopIrrigationApi, stopZone as stopZoneApi } from "../api/runtime.api"

const clampProgress = (value) => Math.max(0, Math.min(100, value))

const toNumber = (value) => {
    const numericValue = Number(value)
    return Number.isFinite(numericValue) ? numericValue : 0
}

const formatTimeValue = (value) => {
    if (!value) {
        return "-"
    }

    const dateValue = new Date(value)
    if (Number.isNaN(dateValue.getTime())) {
        return String(value)
    }

    return dateValue.toLocaleTimeString()
}

const getZoneBadgeConfig = (status) => ({
    idle: { label: "Idle", color: "gray" },
    irrigating: { label: "Irrigating", color: "blue" },
    stopping: { label: "Stopping", color: "orange" },
    error: { label: "Error", color: "red" },
    offline: { label: "Offline", color: "gray" },
}[status] ?? { label: status ?? "Unknown", color: "gray" })

const buildErrorDetail = (error, fallbackMessage) => {
    const detail = error?.response?.data?.detail

    if (typeof detail === "string") {
        return {
            message: detail,
            retryable: false,
        }
    }

    if (detail && typeof detail === "object") {
        return {
            ...detail,
            message: detail.message ?? fallbackMessage,
            retryable: Boolean(detail.retryable),
        }
    }

    return {
        message: error?.message ?? fallbackMessage,
        retryable: false,
    }
}

export default function useRuntimeControlState({
    tasks = [],
    task = null,
    zone = null,
    isStopping = false,
} = {}) {
    const [stoppingZoneIds, setStoppingZoneIds] = useState({})
    const [isStoppingAll, setIsStoppingAll] = useState(false)

    const activeTaskIds = useMemo(() => {
        if (!Array.isArray(tasks)) {
            return []
        }

        return tasks.map(entry => String(entry.id))
    }, [tasks])

    const hasActiveTasks = activeTaskIds.length > 0

    const handleStopZone = useCallback(async (zoneId, { waitForResponse = true, timeoutSeconds = 5 } = {}) => {
        const zoneKey = String(zoneId)

        setStoppingZoneIds(previousState => ({
            ...previousState,
            [zoneKey]: true,
        }))

        try {
            const response = await stopZoneApi({
                zoneId,
                waitForResponse,
                timeoutSeconds,
            })

            return {
                ok: true,
                action: "stop-zone",
                zoneId,
                response,
            }
        } catch (error) {
            console.error(`Failed to stop zone ${zoneId}:`, error)

            return {
                ok: false,
                action: "stop-zone",
                zoneId,
                error: buildErrorDetail(error, `Failed to stop zone ${zoneId}`),
            }
        } finally {
            setStoppingZoneIds(previousState => {
                const nextState = { ...previousState }
                delete nextState[zoneKey]
                return nextState
            })
        }
    }, [])

    const handleStopAll = useCallback(async ({ waitForResponse = true, timeoutSeconds = 5 } = {}) => {
        if (!hasActiveTasks || isStoppingAll) {
            return {
                ok: false,
                action: "stop-all",
                error: {
                    message: "No active irrigation tasks to stop.",
                    retryable: false,
                },
            }
        }

        setIsStoppingAll(true)
        setStoppingZoneIds(previousState => {
            const nextState = { ...previousState }
            activeTaskIds.forEach(zoneId => {
                nextState[zoneId] = true
            })
            return nextState
        })

        try {
            const response = await stopIrrigationApi({
                waitForResponse,
                timeoutSeconds,
            })

            return {
                ok: true,
                action: "stop-all",
                response,
            }
        } catch (error) {
            console.error("Failed to stop all irrigation:", error)

            return {
                ok: false,
                action: "stop-all",
                error: buildErrorDetail(error, "Failed to stop all irrigation"),
            }
        } finally {
            setStoppingZoneIds(previousState => {
                const nextState = { ...previousState }
                activeTaskIds.forEach(zoneId => {
                    delete nextState[zoneId]
                })
                return nextState
            })
            setIsStoppingAll(false)
        }
    }, [activeTaskIds, hasActiveTasks, isStoppingAll])

    const taskState = useMemo(() => {
        if (!task) {
            return null
        }

        const rawProgressValue = clampProgress(toNumber(task.displayProgress ?? task.progress ?? 0))
        const isTaskStale = task.stale === true
        const currentVolume = toNumber(task.currentVolume)
        const targetVolume = toNumber(task.targetVolume)
        const remainingMinutes = toNumber(task.remainingMinutes)

        // When a task disappears from snapshots after normal completion,
        // infer completion from stale + near-finished runtime metrics.
        const isCompletedHeuristically = isTaskStale
            && !task.isDisconnected
            && (
                rawProgressValue >= 95
                || (targetVolume > 0 && currentVolume >= targetVolume)
                || remainingMinutes <= 0
            )

        const progressValue = isCompletedHeuristically ? 100 : rawProgressValue

        return {
            progressValue,
            progressLabel: Number.isInteger(progressValue) ? progressValue.toString() : progressValue.toFixed(1),
            isStale: isTaskStale,
            statusLabel: isTaskStale
                ? (task.isDisconnected ? "Disconnected" : isCompletedHeuristically ? "Completed" : "Stopped")
                : "Irrigating",
            statusColorPalette: isTaskStale ? "gray" : "blue",
            showStopButton: !isTaskStale,
            isStopDisabled: isStopping === true,
            isStopLoading: isStopping === true,
        }
    }, [isStopping, task])

    const zoneState = useMemo(() => {
        if (!zone) {
            return null
        }

        const isZoneStale = zone.stale === true
        const isZoneSelectable = zone.online && zone.status !== "error"
        const badgeConfig = getZoneBadgeConfig(zone.status)

        return {
            isStale: isZoneStale,
            accentColor: zone.status === "error" ? "red.500" : !zone.online ? "gray.400" : "green.400",
            badgeConfig,
            isIrrigating: zone.status === "irrigating",
            isSelectable: isZoneSelectable,
            statusLabel: zone.online ? (isZoneStale ? "Disconnected" : "Online") : "Offline",
            lastRunLabel: formatTimeValue(zone.last_run ?? zone.lastRun),
            isStopDisabled: isZoneStale || isStopping === true,
            isStopLoading: isStopping === true,
            isStartDisabled: isZoneStale,
            isInfoDisabled: isZoneStale,
        }
    }, [isStopping, zone])

    return {
        stoppingZoneIds,
        isStoppingAll,
        hasActiveTasks,
        handleStopZone,
        handleStopAll,
        taskState,
        zoneState,
    }
}