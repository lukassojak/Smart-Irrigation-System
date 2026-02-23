import http from "./http"

export const getLiveSnapshot = async () => {
    const response = await http.get("/runtime/live")
    return response.data
}