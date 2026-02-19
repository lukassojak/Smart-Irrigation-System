import {
    Box,
    VStack,
    HStack,
    Text,
    Badge,
    IconButton,
    Button
} from "@chakra-ui/react"
import {
    Play,
    Square,
    Info,
} from "lucide-react"

export default function ZoneRuntimeCard({ zone }) {

    // ---- Accent color logic ----
    let accentColor = "green.400"

    if (zone.status === "error") {
        accentColor = "red.500"
    } else if (!zone.online) {
        accentColor = "gray.400"
    }

    // ---- Badge config ----
    const badgeConfig = {
        idle: { label: "Idle", color: "gray" },
        irrigating: { label: "Irrigating", color: "green" },
        stopping: { label: "Stopping", color: "orange" },
        error: { label: "Error", color: "red" },
    }[zone.status]

    const isIrrigating = zone.status === "irrigating"

    return (
        <Box
            position="relative"
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={5}
            boxShadow="0 4px 16px rgba(15,23,42,0.05)"
            transition="all 0.15s ease"
            _hover={{
                borderColor: "rgba(56,178,172,0.18)",
                boxShadow: "0 6px 22px rgba(15,23,42,0.06)",
                transform: "translateY(-2px)"
            }}
        >
            {/* Left Accent */}
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

                {/* Header */}
                <HStack justify="space-between">

                    <HStack gap={2} align="center">
                        {/* Zone ID Icon */}
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

                    {/* Action Button */}
                    {zone.online && zone.status !== "error" && (
                        isIrrigating ? (
                            <Button
                                size="xs"
                                variant="subtle"
                                colorPalette="red"
                                aria-label="Stop irrigation"
                                p={1}
                            >
                                <Square size={14} />
                            </Button>
                        ) : (
                            <Button
                                size="xs"
                                variant="subtle"
                                colorPalette="green"
                                aria-label="Start irrigation"
                                p={1}
                            >
                                <Play size={14} />
                            </Button>
                        )
                    )}
                    {/* If online but in error, show button to view error details */}
                    {zone.online && zone.status === "error" && (
                        <Button
                            size="xs"
                            variant="subtle"
                            colorPalette="gray"
                            aria-label="View error details"
                            p={1}
                        >
                            <Info size={14} />
                        </Button>
                    )}
                    {/* If offline, show button to view reconnection options */}
                    {!zone.online && (
                        <Button
                            size="xs"
                            variant="subtle"
                            colorPalette="gray"
                            aria-label="View reconnection options"
                            p={1}
                        >
                            <Info size={14} />
                        </Button>
                    )}
                </HStack>

                {/* Meta Info */}
                <HStack justify="space-between">
                    <Text fontSize="xs" color="gray.500">
                        {zone.online ? "Online" : "Offline"}
                    </Text>
                    <Text fontSize="xs" color="gray.500">
                        Last run: {zone.lastRun || "-"}
                    </Text>
                </HStack>

            </VStack>
        </Box>
    )
}
