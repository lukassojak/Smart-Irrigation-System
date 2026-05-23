import {
    Grid,
    Box,
    Text,
    HStack,
} from "@chakra-ui/react"
import { Activity, Droplet, Clock, CheckCircle } from "lucide-react"

function StatCard({ icon, title, value, helper, bg, border }) {
    return (
        <Box
            position="relative"
            overflow="hidden"
            borderRadius="md"
            bg={bg}
            backdropFilter="blur(18px) saturate(160%)"
            border={border}
            boxShadow="0 10px 24px rgba(15,23,42,0.04)"
            p={4}
        >
            <HStack spacing={3} mb={3} align="center">
                {icon}
                <Text fontWeight="700" fontSize="sm" color="gray.700">
                    {title}
                </Text>
            </HStack>
            <Text fontSize="2xl" fontWeight="800" lineHeight="1" color="gray.800">
                {value}
            </Text>
            <Text fontSize="xs" color="gray.500" mt={2}>
                {helper}
            </Text>
        </Box>
    )
}

export default function HistoryStats({ records = [] }) {
    const successful = records.filter(r => r.outcome === "success").length
    const failed = records.filter(r => r.outcome === "failed").length
    const stopped = records.filter(r => r.outcome === "stopped").length
    const interrupted = records.filter(r => r.outcome === "interrupted").length
    const skipped = records.filter(r => r.outcome === "skipped").length
    const total = records.length

    const totalWaterUsed = records
        .filter(r => r.actual_water_amount)
        .reduce((sum, r) => sum + (r.actual_water_amount || 0), 0)

    const totalTimeSeconds = records
        .filter(r => r.completed_duration)
        .reduce((sum, r) => sum + (r.completed_duration || 0), 0)

    const avgDuration = successful > 0 ? Math.round(totalTimeSeconds / successful) : 0

    const successRate = total > 0 ? Math.round((successful / total) * 100) : 0

    return (
        <Grid templateColumns={{ base: "1fr", md: "repeat(4, 1fr)" }} gap={4}>
            <StatCard
                icon={<CheckCircle size={18} color="rgb(72, 187, 120)" />}
                title="Success rate"
                value={`${successRate}%`}
                helper={`${successful}/${total} successful`}
                bg="rgba(72, 187, 120, 0.08)"
                border="1px solid rgba(72, 187, 120, 0.18)"
            />

            <StatCard
                icon={<Droplet size={18} color="rgb(74, 144, 226)" />}
                title="Total water"
                value={`${totalWaterUsed.toFixed(1)}L`}
                helper="consumed across visible records"
                bg="rgba(74, 144, 226, 0.08)"
                border="1px solid rgba(74, 144, 226, 0.18)"
            />

            <StatCard
                icon={<Clock size={18} color="rgb(237, 137, 54)" />}
                title="Avg duration"
                value={`${avgDuration}s`}
                helper="per completed cycle"
                bg="rgba(237, 137, 54, 0.08)"
                border="1px solid rgba(237, 137, 54, 0.18)"
            />

            <StatCard
                icon={<Activity size={18} color="rgb(237, 100, 166)" />}
                title="Records"
                value={total}
                helper={
                    failed > 0 || stopped > 0 || interrupted > 0 || skipped > 0
                        ? [failed > 0 ? `${failed} failed` : null, stopped > 0 ? `${stopped} stopped` : null, interrupted > 0 ? `${interrupted} interrupted` : null, skipped > 0 ? `${skipped} skipped` : null].filter(Boolean).join(" · ")
                        : "all visible"
                }
                bg="rgba(237, 100, 166, 0.08)"
                border="1px solid rgba(237, 100, 166, 0.18)"
            />
        </Grid>
    )
}
