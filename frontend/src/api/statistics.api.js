import http from "./http"

function serializeStatisticsParams(params = {}) {
    const searchParams = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
        if (value === undefined || value === null) {
            return
        }

        if (Array.isArray(value)) {
            value.forEach((item) => {
                if (item !== undefined && item !== null) {
                    searchParams.append(key, String(item))
                }
            })
            return
        }

        searchParams.append(key, String(value))
    })

    return searchParams.toString()
}

function withStatisticsParams(params = {}) {
    return {
        params,
        paramsSerializer: serializeStatisticsParams,
    }
}

export async function fetchStatisticsOverview(params = {}) {
    return http.get("/history/statistics/overview", withStatisticsParams(params))
}

export async function fetchWaterUsageTrend(params = {}) {
    return http.get("/history/statistics/water-usage-trend", withStatisticsParams(params))
}

export async function fetchOutcomeBreakdown(params = {}) {
    return http.get("/history/statistics/outcome-breakdown", withStatisticsParams(params))
}

export async function fetchZoneCorrectionTrend(params = {}) {
    return http.get("/history/statistics/zone-correction-trend", withStatisticsParams(params))
}

export async function fetchZoneWaterDistribution(params = {}) {
    return http.get("/history/statistics/zone-water-distribution", withStatisticsParams(params))
}
