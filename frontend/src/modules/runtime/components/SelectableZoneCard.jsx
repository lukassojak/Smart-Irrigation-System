import {
    Box,
    VStack,
    HStack,
    Text,
    Badge
} from "@chakra-ui/react"

export default function SelectableZoneCard({
    zone,
    selected,
    onClick
}) {
    const isStale = zone.stale === true
    const lastRunValue = zone.last_run ?? zone.lastRun

    const badgeConfig = {
        idle: { label: "Idle", color: "gray" },
        irrigating: { label: "Irrigating", color: "blue" },
        stopping: { label: "Stopping", color: "orange" },
        error: { label: "Error", color: "red" },
        offline: { label: "Offline", color: "gray" }
    }[zone.status]

    let accentColor = "green.400"

    if (zone.status === "error") {
        accentColor = "red.500"
    } else if (!zone.online) {
        accentColor = "gray.400"
    }

    const isSelectable = zone.online && zone.status !== "error"

    return (
        <Box
            position="relative"
            onClick={onClick}
            cursor={isSelectable ? "pointer" : "default"}
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor={selected ? "teal.400" : "rgba(56,178,172,0.06)"}
            borderRadius="lg"
            p={5}
            boxShadow={selected ? "0 0 0 2px rgba(56,178,172,0.25)" : "0 4px 16px rgba(15,23,42,0.05)"}
            transition="all 0.15s ease"
            _hover={{
                borderColor: isSelectable ? "rgba(56,178,172,0.18)" : "rgba(56,178,172,0.06)",
                boxShadow: isSelectable ? "0 6px 22px rgba(15,23,42,0.06)" : "0 4px 16px rgba(15,23,42,0.05)",
                transform: isSelectable ? "translateY(-2px)" : "none"
            }}
            opacity={isStale ? 0.6 : 1}
            filter={isStale ? "grayscale(0.3)" : "grayscale(0)"}
        >
            <Box
                position="absolute"
                left="0"
                top="0"
                bottom="0"
                width="4px"
                bg={accentColor}
                borderTopLeftRadius="lg"
                borderBottomLeftRadius="lg"
            />

            <VStack align="stretch" spacing={4}>
                <HStack justify="space-between">
                    <HStack gap={2} align="center">
                        <Box
                            bg="teal.50"
                            borderRadius="md"
                            px={2}
                            py={1}
                        >
                            <Text fontSize="sm" color="teal.700" fontWeight="bold">
                                {zone.id}
                            </Text>
                        </Box>

                        <HStack gap={4}>
                            <Text fontWeight="600">
                                {zone.name}
                            </Text>
                            {zone.online && (
                                <Badge
                                    size="sm"
                                    colorPalette={badgeConfig.color}
                                    variant="subtle"
                                >
                                    {badgeConfig.label}
                                </Badge>
                            )}
                        </HStack>
                    </HStack>

                    <Box width="28px" height="28px" />
                </HStack>

                <HStack justify="space-between">
                    <Text fontSize="xs" color="gray.500">
                        {zone.online ? (zone.stale ? "Disconnected" : "Online") : "Offline"}
                    </Text>

                    <Text fontSize="xs" color="gray.500">
                        Last run: {lastRunValue ? new Date(lastRunValue).toLocaleTimeString() : "-"}
                    </Text>
                </HStack>
            </VStack>
        </Box>
    )
}
