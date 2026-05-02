import {
    Badge,
    Box,
    Grid,
    Heading,
    Text,
    HStack,
    Stack,
    useBreakpointValue,
} from "@chakra-ui/react"
import { Droplet, Clock, AlertCircle, MapPinned } from "lucide-react"

function getOutcomeMeta(outcome) {
    switch (outcome) {
        case "success":
            return {
                label: "Success",
                palette: "green",
                accent: "linear-gradient(180deg, rgba(72,187,120,0.95) 0%, rgba(56,161,105,0.85) 100%)",
                cardBg: "rgba(72,187,120,0.08)",
            }
        case "failed":
            return {
                label: "Failed",
                palette: "red",
                accent: "linear-gradient(180deg, rgba(245,101,101,0.95) 0%, rgba(229,62,62,0.85) 100%)",
                cardBg: "rgba(245,101,101,0.08)",
            }
        case "stopped":
            return {
                label: "Stopped",
                palette: "orange",
                accent: "linear-gradient(180deg, rgba(237,137,54,0.95) 0%, rgba(217,119,6,0.85) 100%)",
                cardBg: "rgba(237,137,54,0.08)",
            }
        case "interrupted":
            return {
                label: "Interrupted",
                palette: "yellow",
                accent: "linear-gradient(180deg, rgba(251,182,206,0.95) 0%, rgba(245,120,150,0.85) 100%)",
                cardBg: "rgba(251,182,206,0.08)",
            }
        case "skipped":
            return {
                label: "Skipped",
                palette: "gray",
                accent: "linear-gradient(180deg, rgba(160,174,192,0.95) 0%, rgba(113,128,150,0.85) 100%)",
                cardBg: "rgba(160,174,192,0.10)",
            }
        default:
            return {
                label: outcome,
                palette: "blue",
                accent: "linear-gradient(180deg, rgba(66,153,225,0.95) 0%, rgba(49,130,206,0.85) 100%)",
                cardBg: "rgba(66,153,225,0.08)",
            }
    }
}

function formatDateTime(isoString) {
    try {
        const date = new Date(isoString)
        return date.toLocaleString('cs-CZ', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        })
    } catch {
        return isoString
    }
}

function formatDuration(value) {
    if (!value && value !== 0) {
        return "-"
    }

    if (value < 60) {
        return `${value}s`
    }

    const minutes = Math.floor(value / 60)
    const seconds = value % 60
    return `${minutes}m ${seconds}s`
}

function formatWater(value) {
    if (value === null || value === undefined) {
        return "-"
    }

    return `${Number(value).toFixed(2)} L`
}

function getZoneName(record, nodes) {
    if (record.zone_deleted) {
        return undefined
    }

    const node = nodes.find(n => n.id === record.node_id)
    if (!node || !node.zones) return undefined
    const zone = node.zones.find(z => z.id === record.circuit_id)
    return zone?.name
}

function getZoneLabel(record, nodes) {
    const zoneName = getZoneName(record, nodes)

    if (record.zone_deleted) {
        return `Deleted zone #${record.circuit_id}`
    }

    return zoneName ? `${zoneName} | Zone #${record.circuit_id}` : `Zone #${record.circuit_id}`
}

export default function HistoryRecordsTable({ records = [], nodes = [] }) {
    const isMobile = useBreakpointValue({ base: true, md: false })

    if (records.length === 0) {
        return (
            <Box
                py={10}
                px={6}
                textAlign="center"
                borderRadius="xl"
                bg="rgba(255,255,255,0.45)"
                border="1px dashed rgba(56,178,172,0.18)"
            >
                <Text fontWeight="600" color="gray.700" mb={1}>
                    No records to display
                </Text>
                <Text fontSize="sm" color="gray.500">
                    Try a different node scope or filter.
                </Text>
            </Box>
        )
    }

    return (
        <Stack spacing={3}>
            {records.map((record, idx) => {
                const outcomeMeta = getOutcomeMeta(record.outcome)
                const dateStr = formatDateTime(record.start_time)
                const duration = formatDuration(record.completed_duration)
                const waterUsed = formatWater(record.actual_water_amount)

                return (
                    <Box
                        key={`${record.node_id}-${record.circuit_id}-${record.start_time}-${idx}`}
                        position="relative"
                        overflow="hidden"
                        borderRadius="2xl"
                        bg="rgba(255,255,255,0.58)"
                        backdropFilter="blur(18px) saturate(160%)"
                        border="1px solid rgba(56,178,172,0.10)"
                        boxShadow="0 10px 28px rgba(15,23,42,0.05)"
                        transition="transform 0.14s ease, box-shadow 0.14s ease, border-color 0.14s ease"
                        _hover={{
                            transform: "translateY(-1px)",
                            borderColor: "rgba(56,178,172,0.20)",
                            boxShadow: "0 16px 34px rgba(15,23,42,0.08)",
                        }}
                    >
                        <Box
                            position="absolute"
                            insetY={0}
                            left={0}
                            w="6px"
                            bg={outcomeMeta.accent}
                        />

                        <Grid
                            templateColumns={{ base: "1fr", xl: "minmax(0, 1.4fr) minmax(280px, 0.9fr)" }}
                            gap={4}
                            p={{ base: 4, md: 5 }}
                            pl={{ base: 6, md: 7 }}
                            alignItems="start"
                        >
                            <Stack spacing={3} minW={0}>
                                <HStack spacing={2} flexWrap="wrap">
                                    <Badge colorPalette={outcomeMeta.palette} variant="subtle">
                                        {outcomeMeta.label}
                                    </Badge>
                                    {record.zone_deleted && (
                                        <Badge colorPalette="gray" variant="solid">
                                            Deleted zone
                                        </Badge>
                                    )}
                                </HStack>

                                <Stack spacing={1}>
                                    <Heading size="sm" fontWeight="600" color="gray.800">
                                        {getZoneLabel(record, nodes)}
                                    </Heading>
                                    <HStack spacing={2} color="gray.600" fontSize="sm" flexWrap="wrap">
                                        <HStack spacing={1.5}>
                                            <Clock size={15} />
                                            <Text>{dateStr}</Text>
                                        </HStack>
                                        <Text color="gray.400">•</Text>
                                        <HStack spacing={1.5}>
                                            <MapPinned size={15} />
                                            <Text>Node {record.node_id}</Text>
                                        </HStack>
                                    </HStack>
                                </Stack>

                                {record.reason && (
                                    <Box
                                        mt={1}
                                        px={3}
                                        py={2}
                                        borderRadius="lg"
                                        bg="rgba(245,101,101,0.08)"
                                        border="1px solid rgba(245,101,101,0.16)"
                                    >
                                        <HStack spacing={2} color="red.500" fontSize="sm" align="start">
                                            <AlertCircle size={15} style={{ marginTop: 2 }} />
                                            <Text lineHeight="1.45">{record.reason}</Text>
                                        </HStack>
                                    </Box>
                                )}
                            </Stack>

                            {isMobile ? (
                                <Stack spacing={1} fontSize="sm" color="gray.600">
                                    <Text>
                                        <Text as="span" fontWeight="600" color="gray.700">
                                            Duration:
                                        </Text>{" "}
                                        {duration}
                                    </Text>
                                    <Text>
                                        <Text as="span" fontWeight="600" color="gray.700">
                                            Water used:
                                        </Text>{" "}
                                        {waterUsed}
                                    </Text>
                                    <Text>
                                        <Text as="span" fontWeight="600" color="gray.700">
                                            Target water:
                                        </Text>{" "}
                                        {formatWater(record.target_water_amount)}
                                    </Text>
                                </Stack>
                            ) : (
                                <Grid templateColumns={{ base: "repeat(2, minmax(0, 1fr))", md: "repeat(3, minmax(0, 1fr))" }} gap={3}>
                                    <Box
                                        p={3}
                                        borderRadius="xl"
                                        bg="rgba(56,178,172,0.03)"
                                        border="1px solid rgba(56,178,172,0.08)"
                                    >
                                        <Text fontSize="xs" color="gray.500" mb={1}>
                                            Duration
                                        </Text>
                                        <Text fontSize="lg" fontWeight="700" color="gray.800">
                                            {duration}
                                        </Text>
                                    </Box>

                                    <Box
                                        p={3}
                                        borderRadius="xl"
                                        bg="rgba(56,178,172,0.03)"
                                        border="1px solid rgba(56,178,172,0.08)"
                                    >
                                        <Text fontSize="xs" color="gray.500" mb={1}>
                                            Water used
                                        </Text>
                                        <HStack spacing={1.5} align="center">
                                            <Text fontSize="lg" fontWeight="700" color="gray.800">
                                                {waterUsed}
                                            </Text>
                                        </HStack>
                                    </Box>

                                    <Box
                                        p={3}
                                        borderRadius="xl"
                                        bg="rgba(56,178,172,0.03)"
                                        border="1px solid rgba(56,178,172,0.08)"
                                        gridColumn={{ base: "span 2", md: "auto" }}
                                    >
                                        <Text fontSize="xs" color="gray.500" mb={1}>
                                            Target water
                                        </Text>
                                        <Text fontSize="lg" fontWeight="700" color="gray.800">
                                            {formatWater(record.target_water_amount)}
                                        </Text>
                                    </Box>
                                </Grid>
                            )}
                        </Grid>
                    </Box>
                )
            })}
        </Stack>
    )
}
