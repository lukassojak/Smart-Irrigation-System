import {
    Box,
    VStack,
    HStack,
    Text,
    Badge
} from "@chakra-ui/react"
import { Droplets } from "lucide-react"

export default function SelectableZoneCard({
    zone,
    selected,
    onClick
}) {

    // ---- Badge config ----
    const badgeConfig = {
        idle: { label: "Idle", color: "gray" },
        irrigating: { label: "Irrigating", color: "green" },
        stopping: { label: "Stopping", color: "orange" },
        error: { label: "Error", color: "red" },
    }[zone.status]

    // ---- Accent color logic ----
    let accentColor = "green.400"

    if (zone.status === "error") {
        accentColor = "red.500"
    } else if (!zone.online) {
        accentColor = "gray.400"
    }

    return (
        <Box
            position="relative"
            onClick={onClick}
            cursor={zone.online && zone.status !== "error" ? "pointer" : "default"}
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor={
                selected
                    ? "teal.400"
                    : "rgba(56,178,172,0.06)"
            }
            borderRadius="lg"
            p={4}
            boxShadow={
                selected
                    ? "0 0 0 2px rgba(56,178,172,0.25)"
                    : "0 4px 14px rgba(15,23,42,0.05)"
            }
            transition="all 0.15s ease"
            _hover={{
                borderColor: (zone.online && zone.status !== "error")
                    ? "rgba(56,178,172,0.18)"
                    : "rgba(56,178,172,0.06)",
                transform: (zone.online && zone.status !== "error")
                    ? "translateY(-2px)"
                    : "none"
            }}
            opacity={!zone.online ? 0.6 : 1}
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

            <HStack spacing={3}>
                <Box bg="teal.50" p={2} borderRadius="md">
                    <Droplets size={14} color="#319795" />
                </Box>

                <VStack align="start" spacing={0}>
                    <Text fontWeight="600" fontSize="sm">
                        {zone.name}
                    </Text>
                    {zone.online && (<Badge
                        size="sm"
                        colorPalette={badgeConfig.color}
                        variant="subtle"
                    >
                        {badgeConfig.label}
                    </Badge>
                    )}
                </VStack>
            </HStack>
        </Box>
    )
}
