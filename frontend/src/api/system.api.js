import http from "./http"

export function fetchSystemVersion() {
    return http.get("/system/version")
}