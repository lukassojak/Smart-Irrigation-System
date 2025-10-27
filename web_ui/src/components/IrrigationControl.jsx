import { useState } from "react"
import { startIrrigation, stopIrrigation } from "../lib/api"
import { Play, Square, Droplets } from "lucide-react"

export default function IrrigationControl() {
    const [zoneId, setZoneId] = useState("")
    const [liters, setLiters] = useState("")
    const [loading, setLoading] = useState(false)
    const [message, setMessage] = useState(null)
    const [error, setError] = useState(null)

    async function handleStart() {
        setMessage(null)
        setError(null)

        if (zoneId === "" || isNaN(zoneId)) {
            setError("Please enter a valid zone ID.")
            return
        }

        const literValue = liters === "" ? 0 : parseFloat(liters)
        setLoading(true)

        const res = await startIrrigation(Number(zoneId), literValue)
        if (res.error) {
            setError(`Failed to start irrigation (status ${res.status})`)
        } else {
            setMessage(res.message || "Irrigation started successfully.")
        }
        setLoading(false)
    }

    async function handleStop() {
        setMessage(null)
        setError(null)
        setLoading(true)

        const res = await stopIrrigation()
        if (res.error) {
            setError(`Failed to stop irrigation (status ${res.status})`)
        } else {
            setMessage(res.message || "All irrigation stopped.")
        }
        setLoading(false)
    }

    return (
        <section className="bg-white border border-slate-200 rounded-2xl shadow-sm p-5 mb-6 text-left">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Droplets size={20} className="text-blue-500" />
                    <h2 className="text-xl font-semibold text-slate-800">
                        Irrigation Control
                    </h2>
                </div>
            </div>

            {/* Form */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-4">
                <div>
                    <label className="block text-sm text-slate-600 mb-1">Zone ID</label>
                    <input
                        type="number"
                        value={zoneId}
                        onChange={e => setZoneId(e.target.value)}
                        placeholder="e.g. 1"
                        className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    />
                </div>

                <div>
                    <label className="block text-sm text-slate-600 mb-1">
                        Water Amount (liters)
                    </label>
                    <input
                        type="number"
                        value={liters}
                        onChange={e => setLiters(e.target.value)}
                        placeholder="e.g. 25"
                        className="w-full border border-slate-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
                    />
                </div>

                <div className="flex items-end gap-2">
                    <button
                        onClick={handleStart}
                        disabled={loading}
                        className="flex items-center justify-center gap-2 flex-1 bg-green-100 text-green-800 border border-green-800 px-3 py-2 rounded-md hover:bg-green-200 disabled:opacity-50"
                    >
                        <Play size={16} />
                        Start
                    </button>
                    <button
                        onClick={handleStop}
                        disabled={loading}
                        className="flex items-center justify-center gap-2 flex-1 bg-red-100 text-red-800 border border-red-800 px-3 py-2 rounded-md hover:bg-red-200 disabled:opacity-50"
                    >
                        <Square size={16} />
                        Stop All
                    </button>
                </div>
            </div>

            {/* Messages */}
            {message && (
                <p className="text-sm text-green-600 font-medium">{message}</p>
            )}
            {error && <p className="text-sm text-red-500 font-medium">{error}</p>}
        </section>
    )
}
