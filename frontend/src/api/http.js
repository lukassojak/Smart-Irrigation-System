import axios from "axios"

const API_URL = import.meta.env.VITE_API_URL

const http = axios.create({
    baseURL: `${API_URL}/api/v1`,
})

export default http