import { useEffect, useState } from "react"
import { getNodes, updateStatus } from "../lib/api"
import { RefreshCw, Power, Wifi, Droplets } from "lucide-react"

export default function NodeList() {
    const [nodes, setNodes] = useState({})
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [refreshing, setRefreshing] = useState(false)
    const [lastUpdated, setLastUpdated] = useState(null)

    useEffect(() => {
        fetchNodes()
    }, [])

    async function fetchNodes() {
        setLoading(true)
        setError(null)
        const res = await getNodes()
        if (res.error) {
            setError("Failed to fetch nodes.")
            setNodes({})
        } else {
            setNodes(res.nodes || {})
            setLastUpdated(new Date().toLocaleTimeString())
        }
        setLoading(false)
    }

    async function handleRefresh() {
        setRefreshing(true)
        await updateStatus()
        await fetchNodes()
        setRefreshing(false)
    }

    function parseStatus(statusStr) {
        if (!statusStr) return {}
        const cleaned = statusStr.replace(/^"|"$/g, "")
        const parts = cleaned.split(", ").map(p => p.split(":").map(x => x.trim()))
        const data = {}
        for (const [key, value] of parts) {
            if (key && value !== undefined) data[key] = value
        }

        // Extract zone numbers using regex (handles [1, 2, 4] or any format)
        const zoneMatches =
            data["Currently Irrigating Zones"]?.match(/\d+/g) || []

        return {
            controllerState: data["Controller State"] || "Unknown",
            autoEnabled: data["Auto Enabled"] === "True",
            autoPaused: data["Auto Paused"] === "True",
            zones: zoneMatches,
        }
    }

    function formatDateTime(isoString) {
        if (!isoString) return "—"
        const date = new Date(isoString)
        const time = date.toLocaleTimeString("cs-CZ", {
            hour12: false,
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        })
        const day = String(date.getDate()).padStart(2, "0")
        const month = String(date.getMonth() + 1).padStart(2, "0")
        const year = date.getFullYear()
        return `${time} ${day}.${month}.${year}`
    }

    function renderNodeCard(nodeId, info) {
        const status = parseStatus(info.last_status)
        const lastUpdate = info.last_update ? new Date(info.last_update) : null
        const now = new Date()
        const isOnline = lastUpdate && now - lastUpdate < 1000 * 60 * 1 // 1 min

        return (
            <div
                key={nodeId}
                className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5 hover:shadow-md transition-shadow text-left "
            >
                {/* Header */}
                <div className="flex items-center justify-between mb-3 w-full">
                    <div className="flex items-center gap-2">
                        <Power
                            size={20}
                            className={isOnline ? "text-green-500" : "text-slate-400"}
                        />
                        <h3 className="text-lg font-semibold text-slate-800">{nodeId}</h3>
                    </div>
                    <span
                        className={`text-sm font-medium px-2 py-0.5 rounded-full ${status.controllerState === "IRRIGATING"
                            ? "bg-green-100 text-green-700"
                            : "bg-slate-100 text-slate-600"
                            }`}
                    >
                        {status.controllerState}
                    </span>
                </div>

                {/* Details */}
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm text-slate-700 text-left">
                    <div className="text-slate-500">Auto Mode:</div>
                    <div>
                        {status.autoEnabled ? (
                            <span className="text-green-600 font-medium">Enabled</span>
                        ) : (
                            <span className="text-slate-500">Disabled</span>
                        )}
                        {status.autoPaused && (
                            <span className="ml-2 text-amber-600">(Paused)</span>
                        )}
                    </div>

                    <div className="text-slate-500">Last Update:</div>
                    <div>{formatDateTime(info.last_update)}</div>

                    <div className="text-slate-500">Status:</div>
                    <div className="flex items-center gap-1">
                        <Wifi
                            size={16}
                            className={isOnline ? "text-green-500" : "text-slate-400"}
                        />
                        {isOnline ? "Online" : "Offline"}
                    </div>
                </div>

                {/* Zones */}
                {status.zones.length > 0 && (
                    <div className="mt-3 border-t pt-2 text-left">
                        <div className="flex items-center gap-2 text-slate-600 mb-1">
                            <Droplets size={16} />
                            <span className="font-medium text-sm">
                                Currently Irrigating Zones:
                            </span>
                        </div>
                        <ul className="text-sm text-slate-700 grid grid-cols-3 gap-1 pl-1">
                            {status.zones.map((z, i) => (
                                <li
                                    key={i}
                                    className="bg-green-50 border border-green-100 rounded-md px-2 py-0.5 text-center"
                                >
                                    Zone {z}
                                </li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        )
    }

    return (
        <section>
            {/* Header row stays stable */}
            <div className="flex items-center justify-between mb-4 w-full">
                <h2 className="text-xl font-semibold text-slate-800">Node Overview</h2>
                <button
                    onClick={handleRefresh}
                    disabled={refreshing || loading}
                    className="flex items-center gap-2 text-sm px-3 py-1.5 rounded-md bg-slate-800 text-white hover:bg-slate-700 disabled:opacity-50"
                >
                    <RefreshCw size={16} className={refreshing ? "animate-spin" : ""} />
                    {refreshing ? "Refreshing..." : "Refresh"}
                </button>
            </div>

            {/* Fixed-height container to avoid layout shift */}
            <div className="min-h-[200px]">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                    {loading ? (
                        <p className="col-span-full text-slate-500 italic text-center">
                            Refreshing nodes...
                        </p>
                    ) : error ? (
                        <p className="col-span-full text-red-500 text-center">{error}</p>
                    ) : Object.keys(nodes).length === 0 ? (
                        <p className="col-span-full text-slate-500 italic text-center">
                            No nodes found.
                        </p>
                    ) : (
                        Object.entries(nodes).map(([id, info]) => renderNodeCard(id, info))
                    )}
                </div>
            </div>

            {lastUpdated && !loading && (
                <p className="text-xs text-slate-400 mt-3">Last updated: {lastUpdated}</p>
            )}
        </section>
    )
}
