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

export function updateNode(nodeId, data) {
    return http.patch(`/nodes/${nodeId}`, data)
}

export function fetchZoneById(nodeId, zoneId) {
    return http.get(`/nodes/${nodeId}/zones/${zoneId}`)
}

export function createZone(nodeId, data) {
    return http.post(`/nodes/${nodeId}/zones`, data)
}

export function updateZone(nodeId, zoneId, data) {
    return http.patch(`/nodes/${nodeId}/zones/${zoneId}`, data)
}

export function deleteNode(nodeId) {
    return http.delete(`/nodes/${nodeId}`)
}

export function forceDeleteNode(nodeId) {
    return http.delete(`/nodes/${nodeId}/force`)
}

export function deleteZone(nodeId, zoneId) {
    return http.delete(`/nodes/${nodeId}/zones/${zoneId}`)
}

export function pushNodeConfig(nodeId) {
    return http.post(`/nodes/${nodeId}/push-config`)
}

export function pushAllPendingNodeConfigs() {
    return http.post("/nodes/push-config-all")
}

export function optimizePerPlant(payload) {
    return http.post("/optimization/per-plant", payload)
}

export function fetchNodeHeader(nodeId) {
    return http.get(`/nodes/${nodeId}/header`)
}
