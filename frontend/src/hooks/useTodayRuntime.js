import { useEffect, useState, useRef } from "react"
import { getTodaySnapshot } from "../api/runtime.api"

export default function useTodayRuntime(pollInterval = 180000) {

    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const intervalRef = useRef(null)

    const fetchToday = async () => {
        try {
            const snapshot = await getTodaySnapshot()
            setData(snapshot)
            setError(null)
        } catch (err) {
            console.error("Today fetch failed:", err)
            setError(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchToday()
        intervalRef.current = setInterval(fetchToday, pollInterval)

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [pollInterval])

    return { data, loading, error, refresh: fetchToday }
}