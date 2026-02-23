import http from "./http"

export function fetchNodes() {
    return http.get("/nodes/")
}

export function fetchNodeById(nodeId) {
    return http.get(`/nodes/${nodeId}`)
}

export function createNode(data) {
    return http.post("/nodes/", data)
}

export function fetchZoneById(nodeId, zoneId) {
    return http.get(`/nodes/${nodeId}/zones/${zoneId}`)
}

export function createZone(nodeId, data) {
    return http.post(`/nodes/${nodeId}/zones`, data)
}

export function deleteNode(nodeId) {
    return http.delete(`/nodes/${nodeId}`)
}

export function deleteZone(nodeId, zoneId) {
    return http.delete(`/nodes/${nodeId}/zones/${zoneId}`)
}

export function optimizePerPlant(payload) {
    return http.post("/optimization/per-plant", payload)
}
