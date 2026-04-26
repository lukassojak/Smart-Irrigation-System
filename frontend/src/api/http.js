import axios from "axios"

const API_URL = import.meta.env.VITE_API_URL?.trim() || ""
const baseURL = API_URL ? `${API_URL}/api/v1` : "/api/v1"

const http = axios.create({
    baseURL,
})

export default http