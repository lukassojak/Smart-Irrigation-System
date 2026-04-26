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
import useRuntimeControlState from "../../../hooks/useRuntimeControlState"


export default function ZoneRuntimeCard({ zone, isStopping, onStop }) {
    const {
        zoneState,
    } = useRuntimeControlState({
        zone,
        isStopping,
    })

    const isStale = zoneState?.isStale === true
    const accentColor = zoneState?.accentColor ?? "green.400"
    const badgeConfig = zoneState?.badgeConfig ?? { label: zone.status, color: "gray" }
    const isIrrigating = zoneState?.isIrrigating === true

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
            opacity={zone.stale ? 0.6 : 1}
            filter={zone.stale ? "grayscale(0.3)" : "grayscale(0)"}
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
                                isDisabled={zoneState?.isStopDisabled}
                                onClick={() => onStop?.(zone.id)}
                                loading={zoneState?.isStopLoading}
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
                                isDisabled={zoneState?.isStartDisabled}
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
                            isDisabled={zoneState?.isInfoDisabled}
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
                            isDisabled={zoneState?.isInfoDisabled}
                        >
                            <Info size={14} />
                        </Button>
                    )}
                </HStack>

                {/* Meta Info */}
                <HStack justify="space-between">
                    <Text fontSize="xs" color="gray.500">
                        {zoneState?.statusLabel ?? (zone.online ? (zone.stale ? "Disconnected" : "Online") : "Offline")}
                    </Text>
                    {/* Display zone.lastRun */}
                    <Text fontSize="xs" color="gray.500">
                        Last run: {zoneState?.lastRunLabel ?? "-"}
                    </Text>
                </HStack>

            </VStack>
        </Box>
    )
}
