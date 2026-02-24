import { useEffect, useState, useRef } from "react"
import { getLiveSnapshot } from "../api/runtime.api"

export default function useLiveRuntime(pollInterval = 3000) {

    const [data, setData] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const intervalRef = useRef(null)

    const fetchLive = async () => {
        try {
            const snapshot = await getLiveSnapshot()
            setData(snapshot)
            setError(null)
        } catch (err) {
            console.error("Live runtime fetch failed:", err)
            setError(err)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchLive()
        intervalRef.current = setInterval(fetchLive, pollInterval)

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current)
            }
        }
    }, [pollInterval])

    return { data, loading, error, refresh: fetchLive }
}