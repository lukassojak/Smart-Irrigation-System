import http from "./http"

export function fetchHistoryRecords(nodeId, circuitId, limit = 100, includeDeleted = false, outcome = null) {
    const params = new URLSearchParams()
    if (nodeId !== null && nodeId !== undefined) {
        params.append("node_id", nodeId)
    }
    if (circuitId !== null && circuitId !== undefined) {
        params.append("circuit_id", circuitId)
    }
    if (limit !== null && limit !== undefined) {
        params.append("limit", limit)
    }
    // include_deleted_zones is expected by the API as boolean string
    if (includeDeleted !== null && includeDeleted !== undefined) {
        params.append("include_deleted_zones", String(Boolean(includeDeleted)))
    }
    if (outcome !== null && outcome !== undefined && outcome !== "all") {
        params.append("outcome", outcome)
    }

    return http.get(`/history/irrigation-history/records?${params.toString()}`)
}

export function fetchAllHistoryRecords(limit = 100, includeDeleted = false, outcome = null) {
    return fetchHistoryRecords(undefined, undefined, limit, includeDeleted, outcome)
}

export function fetchNodeHistory(nodeId, limit = 100, includeDeleted = false, outcome = null) {
    return fetchHistoryRecords(nodeId, undefined, limit, includeDeleted, outcome)
}

export function fetchCircuitHistory(nodeId, circuitId, limit = 100) {
    return http.get(`/history/irrigation-history/records?node_id=${nodeId}&circuit_id=${circuitId}&limit=${limit}`)
}

export function deleteAllHistory() {
    return http.delete(`/history/irrigation-history/records`)
}
