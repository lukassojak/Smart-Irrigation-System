import http from "./http"

export async function fetchHistoryRecords(params = {}) {
    return http.get("/history/irrigation-history/records", { params })
}

export async function fetchAllHistoryRecords() {
    return http.get("/history/irrigation-history/records", { params: { limit: 1000 } })
}

export async function fetchNodeHistory(nodeId, params = {}) {
    return http.get(`/history/irrigation-history/records`, {
        params: {
            node_id: nodeId,
            ...params,
        },
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
