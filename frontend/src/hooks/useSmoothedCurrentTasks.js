import { useEffect, useRef, useState } from "react"

const TICK_MS = 100
const DEFAULT_FINISH_GRACE_MS = 600
const DEFAULT_FINISH_DURATION_MS = 900
const RAW_CHANGE_EPSILON = 0.01

const clampProgress = (value) => Math.max(0, Math.min(100, value))

const easeOutCubic = (value) => 1 - Math.pow(1 - value, 3)

const toNumber = (value) => {
    const numericValue = Number(value)
    return Number.isFinite(numericValue) ? numericValue : 0
}

const buildZoneStatusMap = (zones) => {
    const statusMap = new Map()

    for (const zone of zones ?? []) {
        statusMap.set(zone.id, {
            status: zone.status,
            online: zone.online,
        })
    }

    return statusMap
}

const ema = (previousValue, nextValue, factor) => {
    if (previousValue == null) {
        return nextValue
    }

    return (previousValue * (1 - factor)) + (nextValue * factor)
}

const getLeadLimitMs = (entry, pollIntervalMs) => {
    const learnedGapMs = entry.avgGapMs ?? pollIntervalMs
    const lowerBound = Math.max(600, pollIntervalMs)
    const upperBound = Math.max(lowerBound, learnedGapMs * 0.9)

    return Math.min(upperBound, Math.max(lowerBound, learnedGapMs))
}

const buildDisplayTasks = (entries) => {
    return Array.from(entries.values())
        .filter(entry => entry.phase !== "done")
        .sort((a, b) => {
            if (a.phase !== b.phase) {
                return a.phase === "finishing" ? 1 : -1
            }

            return a.order - b.order
        })
        .map(entry => ({
            id: entry.id,
            zoneName: entry.zoneName,
            progress: entry.displayProgress,
            displayProgress: entry.displayProgress,
            currentVolume: entry.currentVolume,
            targetVolume: entry.targetVolume,
            remainingMinutes: entry.remainingMinutes,
            stale: entry.stale,
            isDisconnected: entry.isDisconnected,
            isFinishing: entry.phase === "finishing",
        }))
}

const createEntry = (task, now, order) => {
    const progress = toNumber(task.progress)

    return {
        id: task.id,
        order,
        phase: "active",
        zoneName: task.zoneName,
        currentVolume: task.currentVolume,
        targetVolume: task.targetVolume,
        remainingMinutes: task.remainingMinutes,
        stale: task.stale ?? false,
        isDisconnected: false,
        lastRawProgress: progress,
        lastRawChangeAt: now,
        lastSnapshotAt: now,
        avgRatePerMs: null,
        avgGapMs: null,
        displayProgress: progress,
        missingSince: null,
        finishStartAt: null,
        finishStartProgress: progress,
        finishDurationMs: DEFAULT_FINISH_DURATION_MS,
        doneAt: null,
    }
}

export default function useSmoothedCurrentTasks(rawTasks = [], zones = [], pollIntervalMs = 2500) {
    const [displayTasks, setDisplayTasks] = useState([])
    const entriesRef = useRef(new Map())
    const zoneStatusRef = useRef(new Map())

    useEffect(() => {
        const now = performance.now()
        const entries = entriesRef.current
        const incomingTasks = Array.isArray(rawTasks) ? rawTasks : []
        const incomingZoneStatus = buildZoneStatusMap(zones)
        zoneStatusRef.current = incomingZoneStatus

        const seenIds = new Set()

        incomingTasks.forEach((task, order) => {
            const existingEntry = entries.get(task.id)
            const nextProgress = toNumber(task.progress)
            const zoneInfo = incomingZoneStatus.get(task.id)
            seenIds.add(task.id)

            if (!existingEntry) {
                entries.set(task.id, createEntry(task, now, order))
                return
            }

            const rawChanged = Math.abs(nextProgress - existingEntry.lastRawProgress) >= RAW_CHANGE_EPSILON

            if (rawChanged) {
                const elapsedSinceRawChangeMs = Math.max(now - existingEntry.lastRawChangeAt, 1)
                const observedDelta = nextProgress - existingEntry.lastRawProgress
                const observedRate = observedDelta / elapsedSinceRawChangeMs

                existingEntry.avgRatePerMs = ema(existingEntry.avgRatePerMs, observedRate, 0.35)
                existingEntry.avgGapMs = ema(existingEntry.avgGapMs, elapsedSinceRawChangeMs, 0.35)
                existingEntry.lastRawChangeAt = now
            }

            existingEntry.order = order
            existingEntry.zoneName = task.zoneName
            existingEntry.currentVolume = task.currentVolume
            existingEntry.targetVolume = task.targetVolume
            existingEntry.remainingMinutes = task.remainingMinutes
            existingEntry.stale = task.stale ?? false
            existingEntry.isDisconnected = existingEntry.stale && zoneInfo?.online === false
            existingEntry.phase = "active"
            existingEntry.missingSince = null
            existingEntry.finishStartAt = null
            existingEntry.doneAt = null
            existingEntry.lastSnapshotAt = now
            existingEntry.lastRawProgress = nextProgress

            if (rawChanged) {
                existingEntry.displayProgress = Math.max(0, Math.min(100, Math.min(existingEntry.displayProgress, nextProgress)))
            } else {
                existingEntry.displayProgress = Math.max(existingEntry.displayProgress, nextProgress)
            }
        })

        for (const [taskId, entry] of entries) {
            if (seenIds.has(taskId)) {
                continue
            }

            if (entry.missingSince == null) {
                entry.missingSince = now
            }

            const zoneInfo = zoneStatusRef.current.get(taskId)
            const zoneIsIrrigating = zoneInfo?.status === "irrigating"
            const missingForMs = now - entry.missingSince

            if (!zoneIsIrrigating && entry.phase === "active" && missingForMs >= DEFAULT_FINISH_GRACE_MS) {
                entry.phase = "finishing"
                entry.finishStartAt = now
                entry.finishStartProgress = entry.displayProgress
                entry.finishDurationMs = DEFAULT_FINISH_DURATION_MS
            }
        }

        setDisplayTasks(buildDisplayTasks(entries))
    }, [rawTasks, zones, pollIntervalMs])

    useEffect(() => {
        const updateDisplay = () => {
            const now = performance.now()
            let changed = false

            for (const [taskId, entry] of entriesRef.current) {
                if (entry.phase === "active") {
                    const elapsedSinceRawChangeMs = Math.max(now - entry.lastRawChangeAt, 0)
                    const leadLimitMs = getLeadLimitMs(entry, pollIntervalMs)
                    const predictedProgress = entry.lastRawProgress + ((entry.avgRatePerMs ?? 0) * Math.min(elapsedSinceRawChangeMs, leadLimitMs))
                    const nextProgress = clampProgress(Math.max(entry.lastRawProgress, predictedProgress))

                    const delta = nextProgress - entry.displayProgress
                    if (Math.abs(delta) >= 0.05) {
                        const smoothingFactor = delta >= 0 ? 0.22 : 0.45
                        entry.displayProgress = clampProgress(entry.displayProgress + (delta * smoothingFactor))
                        changed = true
                    }

                    const zoneInfo = zoneStatusRef.current.get(taskId)
                    if (entry.missingSince != null && zoneInfo?.status !== "irrigating") {
                        const missingForMs = now - entry.missingSince
                        if (missingForMs >= DEFAULT_FINISH_GRACE_MS) {
                            entry.phase = "finishing"
                            entry.finishStartAt = now
                            entry.finishStartProgress = entry.displayProgress
                            entry.finishDurationMs = DEFAULT_FINISH_DURATION_MS
                            changed = true
                        }
                    }
                    continue
                }

                if (entry.phase === "finishing") {
                    const elapsedMs = Math.max(now - entry.finishStartAt, 0)
                    const completionProgress = clampProgress(
                        entry.finishStartProgress + ((100 - entry.finishStartProgress) * easeOutCubic(Math.min(elapsedMs / entry.finishDurationMs, 1)))
                    )

                    if (Math.abs(completionProgress - entry.displayProgress) >= 0.05) {
                        entry.displayProgress = completionProgress
                        changed = true
                    }

                    if (elapsedMs >= entry.finishDurationMs) {
                        entry.displayProgress = 100
                        entry.phase = "done"
                        entry.doneAt = now
                        changed = true
                    }
                    continue
                }

                if (entry.phase === "done") {
                    if (now - entry.doneAt >= 450) {
                        entriesRef.current.delete(taskId)
                        changed = true
                    }
                }
            }

            if (changed) {
                setDisplayTasks(buildDisplayTasks(entriesRef.current))
            }
        }

        const intervalId = window.setInterval(updateDisplay, TICK_MS)
        updateDisplay()

        return () => {
            window.clearInterval(intervalId)
        }
    }, [])

    return displayTasks
}