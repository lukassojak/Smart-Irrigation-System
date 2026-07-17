import React, { useMemo } from "react"
import { useParams, useNavigate } from "react-router-dom"
import {
    Box,
    Heading,
    Text,
    Grid,
    Stack,
    HStack,
    Badge,
    Button,
    Separator,
} from "@chakra-ui/react"
import { Clock, MapPinned } from "lucide-react"

import { fetchRecordByKey } from "../../../api/history.api"

function safeDiv(a, b) {
    if (a == null || b == null) return null
    if (b === 0) return null
    return a / b
}

function computeCorrection(base, standard, actual, label) {
    if (base == null || standard == null || actual == null) return null
    const factor = safeDiv(actual, standard)
    if (factor == null) return null
    const adjusted = base * factor
    const delta = adjusted - base
    return {
        label,
        factor,
        adjusted,
        delta,
    }
}

export default function IrrigationRecordDetailPage() {
    const { nodeId, circuitId, startTime } = useParams()
    const navigate = useNavigate()

    // We attempt to read a record from window state or fetch from API.
    // For simplicity we call an API helper; if not available, show guidance.
    const [record, setRecord] = React.useState(null)
    const [loading, setLoading] = React.useState(true)
    const [error, setError] = React.useState(null)

    React.useEffect(() => {
        let mounted = true
        async function load() {
            setLoading(true)
            setError(null)
            try {
                // The server API currently offers listing endpoints.
                // We try to call a helper `fetchRecordByKey(nodeId, circuitId, startTime)`
                if (typeof fetchRecordByKey === "function") {
                    const resp = await fetchRecordByKey(nodeId, circuitId, decodeURIComponent(startTime))
                    if (!mounted) return
                    setRecord(resp.data)
                } else {
                    // Fallback: instruct user to implement fetchRecordByKey helper
                    setError("Record fetch helper not implemented. Provide `fetchRecordByKey` in frontend API.")
                }
            } catch (err) {
                setError(err.message || String(err))
            } finally {
                if (mounted) setLoading(false)
            }
        }
        load()
        return () => { mounted = false }
    }, [nodeId, circuitId, startTime])

    const computed = useMemo(() => {
        if (!record) return {}
        const solar = computeCorrection(record.base_water_amount, record.standard_conditions_solar, record.actual_solar, "solar")
        const rain = computeCorrection(record.base_water_amount, record.standard_conditions_rain, record.actual_rain, "rain")
        const temp = computeCorrection(record.base_water_amount, record.standard_conditions_temp, record.actual_temp, "temperature")

        // special-case: skipped due to dynamic interval => carry_over_volume
        let carryOverVolume = null
        if (record.outcome === "skipped" && record.dynamic_interval_enabled) {
            carryOverVolume = record.target_water_amount ?? null
        }

        return { solar, rain, temp, carryOverVolume }
    }, [record])

    if (loading) {
        return (
            <Box p={6}>
                <Text>Loading record details…</Text>
            </Box>
        )
    }

    if (error) {
        return (
            <Box p={6}>
                <Text color="red.500">{error}</Text>
                <Button mt={4} onClick={() => navigate(-1)}>Back</Button>
            </Box>
        )
    }

    if (!record) {
        return (
            <Box p={6}>
                <Text>No record found.</Text>
                <Button mt={4} onClick={() => navigate(-1)}>Back</Button>
            </Box>
        )
    }

    const startStr = record.start_time
        ? new Date(record.start_time).toLocaleString('cs-CZ', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        })
        : "-"

    return (
        <Box p={{ base: 4, md: 6 }}>
            <HStack justify="space-between" mb={4}>
                <Stack>
                    <Heading size="md">Irrigation record</Heading>
                    <HStack spacing={3} color="gray.600">
                        <Clock size={14} />
                        <Text>{startStr}</Text>
                        <MapPinned size={14} />
                        <Text>Node {record.node_id} • Zone {record.circuit_id}</Text>
                    </HStack>
                </Stack>
                <Button onClick={() => navigate(-1)} variant="ghost">Back</Button>
            </HStack>

            <Box mb={4} p={4} borderRadius="xl" bg="rgba(255,255,255,0.6)" border="1px solid rgba(0,0,0,0.04)">
                <HStack justify="space-between">
                    <Stack>
                        <HStack>
                            <Badge colorScheme={record.outcome === "success" ? "green" : "red"}>{record.outcome}</Badge>
                            {record.zone_deleted && <Badge>Deleted zone</Badge>}
                            {record.was_manual_run && <Badge>Manual run</Badge>}
                        </HStack>
                        {record.reason && <Text color="red.600">{record.reason}</Text>}
                    </Stack>
                    <Stack textAlign="right">
                        <Text fontSize="sm" color="gray.500">Duration</Text>
                        <Text fontWeight="700">{record.completed_duration ?? "-"} s</Text>
                    </Stack>
                </HStack>
            </Box>

            <Grid templateColumns={{ base: "1fr", md: "1fr 1fr" }} gap={4}>
                <Box p={4} borderRadius="lg" bg="rgba(255,255,255,0.5)" border="1px solid rgba(0,0,0,0.04)">
                    <Heading size="sm" mb={3}>Water</Heading>
                    <Stack spacing={2}>
                        {record.outcome === "skipped" && record.dynamic_interval_enabled ? (
                            <Box>
                                <Text fontSize="xs" color="gray.500">Carry-over volume</Text>
                                <Text fontWeight="700">{record.target_water_amount ?? "-"} L</Text>
                            </Box>
                        ) : (
                            <>
                                <Box>
                                    <Text fontSize="xs" color="gray.500">Target water</Text>
                                    <Text fontWeight="700">{record.target_water_amount ?? "-"} L</Text>
                                </Box>
                                <Box>
                                    <Text fontSize="xs" color="gray.500">Actual water</Text>
                                    <Text fontWeight="700">{record.actual_water_amount ?? "-"} L</Text>
                                </Box>
                            </>
                        )}

                        {record.even_area_mode && (
                            <Box>
                                <Text fontSize="xs" color="gray.500">Target mm</Text>
                                <Text fontWeight="700">{record.target_mm ?? "-"} mm</Text>
                                <Text fontSize="xs" color="gray.500">Actual mm</Text>
                                <Text fontWeight="700">{record.actual_mm ?? "-"} mm</Text>
                            </Box>
                        )}

                        <Separator />

                        <Box>
                            <Text fontSize="xs" color="gray.500">Carry over applied</Text>
                            <Text fontWeight="700">{record.carry_over_applied ? "Yes" : "No"}</Text>
                        </Box>
                    </Stack>
                </Box>

                <Box p={4} borderRadius="lg" bg="rgba(255,255,255,0.5)" border="1px solid rgba(0,0,0,0.04)">
                    <Heading size="sm" mb={3}>Corrections</Heading>
                    <Stack spacing={3}>
                        <Box>
                            <Text fontSize="xs" color="gray.500">Base water amount</Text>
                            <Text fontWeight="700">{record.base_water_amount ?? "-"} L</Text>
                        </Box>

                        <Box>
                            <Text fontSize="sm" fontWeight="600">Solar correction</Text>
                            {computed.solar ? (
                                <Stack spacing={1}>
                                    <Text fontSize="xs">Factor: {Number(computed.solar.factor).toFixed(2)}</Text>
                                    <Text fontWeight="700">Adjusted target: {Number(computed.solar.adjusted).toFixed(2)} L</Text>
                                    <Text color="gray.500">Delta: {Number(computed.solar.delta).toFixed(2)} L</Text>
                                </Stack>
                            ) : (
                                <Text color="gray.500">Not enough data to compute solar correction</Text>
                            )}
                        </Box>

                        <Box>
                            <Text fontSize="sm" fontWeight="600">Rain correction</Text>
                            {computed.rain ? (
                                <Stack spacing={1}>
                                    <Text fontSize="xs">Factor: {Number(computed.rain.factor).toFixed(2)}</Text>
                                    <Text fontWeight="700">Adjusted target: {Number(computed.rain.adjusted).toFixed(2)} L</Text>
                                    <Text color="gray.500">Delta: {Number(computed.rain.delta).toFixed(2)} L</Text>
                                </Stack>
                            ) : (
                                <Text color="gray.500">Not enough data to compute rain correction</Text>
                            )}
                        </Box>

                        <Box>
                            <Text fontSize="sm" fontWeight="600">Temperature correction</Text>
                            {computed.temp ? (
                                <Stack spacing={1}>
                                    <Text fontSize="xs">Factor: {Number(computed.temp.factor).toFixed(2)}</Text>
                                    <Text fontWeight="700">Adjusted target: {Number(computed.temp.adjusted).toFixed(2)} L</Text>
                                    <Text color="gray.500">Delta: {Number(computed.temp.delta).toFixed(2)} L</Text>
                                </Stack>
                            ) : (
                                <Text color="gray.500">Not enough data to compute temperature correction</Text>
                            )}
                        </Box>

                        {computed.carryOverVolume != null && (
                            <Box>
                                <Text fontSize="sm" fontWeight="600">Carry-over volume (dynamic interval)</Text>
                                <Text fontWeight="700">{computed.carryOverVolume} L</Text>
                            </Box>
                        )}
                    </Stack>
                </Box>
            </Grid>

            <Box mt={6} p={4} borderRadius="lg" bg="rgba(255,255,255,0.5)">
                <Heading size="sm" mb={3}>Raw data</Heading>
                <pre style={{ whiteSpace: "pre-wrap", fontSize: 12 }}>{JSON.stringify(record, null, 2)}</pre>
            </Box>
        </Box>
    )
}
