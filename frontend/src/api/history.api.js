import http from "./http"

export function fetchHistoryRecords(nodeId, circuitId, limit = 100) {
    const params = new URLSearchParams()
    if (nodeId !== null && nodeId !== undefined) {
        params.append("node_id", nodeId)
    }
    if (circuitId !== null && circuitId !== undefined) {
        params.append("circuit_id", circuitId)
    }
    params.append("limit", limit)

    return http.get(`/runtime/history/records?${params.toString()}`)
}

export function fetchAllHistoryRecords(limit = 100) {
    return fetchHistoryRecords(undefined, undefined, limit)
}

export function fetchNodeHistory(nodeId, limit = 100) {
    return http.get(`/runtime/history/records?node_id=${nodeId}&limit=${limit}`)
}

export function fetchCircuitHistory(nodeId, circuitId, limit = 100) {
    return http.get(`/runtime/history/records?node_id=${nodeId}&circuit_id=${circuitId}&limit=${limit}`)
}

export function deleteAllHistory() {
    return http.delete(`/runtime/history/records`)
}
