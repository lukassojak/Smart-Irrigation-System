import {
    Grid,
    Box,
    Text,
    HStack,
} from "@chakra-ui/react"
import { Activity, Droplet, WandSparkles, CheckCircle } from "lucide-react"

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

export default function HistoryStats({ serverStats }) {
    // serverStats is required by the new UI contract; do not fallback to local computation.
    const successRatePercent = Math.round((serverStats.success_rate ?? 0) * 100)
    const totalWaterUsed = serverStats.total_water ?? 0
    const totalRecordsValue = serverStats.total_records ?? 0
    const avgCorrection = serverStats.avg_correction ?? 0
    const avgCorrectionPercent = Math.round(avgCorrection * 100).toFixed(0)
    const avgCorrectionFormatted = `${avgCorrectionPercent >= 0 ? "+" : ""}${avgCorrectionPercent}%`
    const recordsHelper = `${serverStats.returned_records ?? 0} visible`

    return (
        <Grid templateColumns={{ base: "1fr", md: "repeat(4, 1fr)" }} gap={4}>
            <StatCard
                icon={<CheckCircle size={18} color="rgb(72, 187, 120)" />}
                title="Success rate"
                value={`${successRatePercent}%`}
                helper="successful, skipped, or stopped records"
                bg="rgba(72, 187, 120, 0.08)"
                border="1px solid rgba(72, 187, 120, 0.18)"
            />

            <StatCard
                icon={<Droplet size={18} color="rgb(74, 144, 226)" />}
                title="Total water"
                value={`${(totalWaterUsed || 0).toFixed(1)}L`}
                helper="across matching records"
                bg="rgba(74, 144, 226, 0.08)"
                border="1px solid rgba(74, 144, 226, 0.18)"
            />

            <StatCard
                icon={<WandSparkles size={18} color="rgb(237, 137, 54)" />}
                title="Avg correction"
                value={avgCorrectionFormatted}
                helper="automatically adjusted water amount"
                bg="rgba(237, 137, 54, 0.08)"
                border="1px solid rgba(237, 137, 54, 0.18)"
            />

            <StatCard
                icon={<Activity size={18} color="rgb(237, 100, 166)" />}
                title="Matching records"
                value={totalRecordsValue}
                helper={recordsHelper}
                bg="rgba(237, 100, 166, 0.08)"
                border="1px solid rgba(237, 100, 166, 0.18)"
            />
        </Grid>
    )
}
