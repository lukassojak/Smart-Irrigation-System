import http from "./http"

export function fetchSystemVersion() {
    return http.get("/system/version")
}

export function fetchNodeMetadata(nodeId) {
    return http.get(`/system/nodes/${nodeId}/metadata`)
}