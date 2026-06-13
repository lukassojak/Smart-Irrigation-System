import http from "../../../api/http"

export async function getLiveSnapshot() {
    const resp = await http.get("/runtime/statuses/live")
    return resp.data
}

export async function getDiscoveredDevices() {
    const resp = await http.get("/runtime/statuses/discovered")
    return resp.data
}

export async function getNodesSnapshot() {
    const resp = await http.get("/runtime/statuses/nodes")
    return resp.data
}

export async function getNodeDetail(nodeId) {
    const resp = await http.get(`/runtime/statuses/nodes/${nodeId}`)
    return resp.data
}
