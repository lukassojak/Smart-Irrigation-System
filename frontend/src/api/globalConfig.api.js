import http from "./http"

export function fetchGlobalConfig() {
    return http.get("/global-config/")
}

export function updateGlobalConfig(data) {
    return http.patch("/global-config/", data)
}
