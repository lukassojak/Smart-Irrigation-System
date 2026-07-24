import http from "./http"

export async function fetchHistoryRecords(params = {}) {
    return http.get("/history/irrigation-history/records", { params })
}

export async function fetchAllHistoryRecords(limit = 100, includeDeleted = false, outcome = null) {
    const params = { limit }

    if (includeDeleted) {
        params.include_deleted_zones = true
    }

    if (outcome) {
        params.outcome = outcome
    }

    return http.get("/history/irrigation-history/records", { params })
}

export async function fetchNodeHistory(nodeId, limit = 100, includeDeleted = false, outcome = null) {
    const params = {
        node_id: nodeId,
        limit,
    }

    if (includeDeleted) {
        params.include_deleted_zones = true
    }

    if (outcome) {
        params.outcome = outcome
    }

    return http.get(`/history/irrigation-history/records`, {
        params,
    })
}

export async function fetchCircuitHistory(circuitId, params = {}) {
    return http.get(`/history/irrigation-history/records`, {
        params: {
            circuit_id: circuitId,
            ...params,
        },
    })
}

export async function fetchRecordById(recordId) {
    return http.get(`/history/irrigation-history/record/${recordId}`)
}

export async function deleteRecordById(recordId) {
    return http.delete(`/history/irrigation-history/record/${recordId}`)
}

export async function deleteAllHistory() {
    return http.delete("/history/irrigation-history/records")
}
