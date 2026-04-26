import {
    Box,
    Text,
    HStack,
    Badge,
    Stack,
    Progress,
} from "@chakra-ui/react"

const EMITTER_ICONS = {
    dripper: "💧",
    soaker_hose: "〰️",
    micro_spray: "🌫️",
}

export default function EmitterOverviewCard({ emitter, totalFlow = 0 }) {
    const flow =
        emitter.type === "soaker_hose"
            ? emitter.flow_rate_lph || 0
            : (emitter.flow_rate_lph || 0) * (emitter.count || 0)

    const share = totalFlow > 0 ? Math.round((flow / totalFlow) * 100) : 0

    return (
        <Box
            p={5}
            borderRadius="xl"
            borderWidth="1px"
            borderColor="border.subtle"
            bg="bg.panel"
            boxShadow="sm"
        >
            <HStack justify="space-between" mb={3}>
                <HStack>
                    <Box fontSize="xl">{EMITTER_ICONS[emitter.type] || "🫗"}</Box>
                    <Badge variant="subtle">{emitter.type}</Badge>
                </HStack>
                {emitter.type !== "soaker_hose" && (
                    <Badge colorPalette="teal" variant="subtle">
                        {emitter.count || 0}×
                    </Badge>
                )}
            </HStack>

            <Stack>
                <HStack justify="space-between">
                    <Text fontSize="sm" color="fg.muted">
                        Flow rate
                    </Text>
                    <Text fontSize="sm" fontWeight="medium">
                        {(emitter.flow_rate_lph || 0).toFixed(1)} L/h
                    </Text>
                </HStack>

                {emitter.type !== "soaker_hose" && (
                    <HStack justify="space-between">
                        <Text fontSize="sm" color="fg.muted">
                            Count
                        </Text>
                        <Text fontSize="sm" fontWeight="medium">
                            {emitter.count || 0} pcs
                        </Text>
                    </HStack>
                )}

                <Box>
                    <Text fontSize="xs" color="fg.muted" mb={1}>
                        Share of zone flow
                    </Text>
                    <Progress.Root value={share} size="sm" colorPalette="teal">
                        <Progress.Track>
                            <Progress.Range />
                        </Progress.Track>
                    </Progress.Root>
                    <Text fontSize="xs" color="fg.subtle" mt={1}>
                        {flow.toFixed(1)} L/h ({share}%)
                    </Text>
                </Box>
            </Stack>
        </Box>
    )
}
