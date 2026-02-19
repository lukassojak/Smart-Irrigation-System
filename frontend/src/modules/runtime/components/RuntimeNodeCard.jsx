import {
    Box,
    VStack,
    HStack,
    Text,
    Badge
} from "@chakra-ui/react"
import {
    Server,
    Wifi,
    EthernetPort,
    Activity
} from "lucide-react"

export default function RuntimeNodeCard({ node, onClick }) {

    const statusColor = node.online
        ? "green.400"
        : "red.400"

    const controllerColor = {
        running: "green",
        idle: "gray",
        error: "red",
        offline: "red"
    }[node.controllerStatus]

    return (
        <Box
            onClick={onClick}
            cursor="pointer"
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
            <VStack align="stretch" spacing={4}>

                {/* Header */}
                <HStack justify="space-between">
                    <HStack spacing={3}>
                        <Server size={18} />
                        <Text fontWeight="600">
                            {node.name}
                        </Text>
                    </HStack>

                    <Box
                        w="8px"
                        h="8px"
                        borderRadius="full"
                        bg={statusColor}
                    />
                </HStack>

                {/* Connection */}
                <HStack spacing={2}>
                    {node.connection === "wifi" ? (
                        <Wifi size={14} />
                    ) : (
                        <EthernetPort size={14} />
                    )}
                    <Text fontSize="sm" color="gray.600">
                        {node.connection === "wifi"
                            ? `WiFi (${node.signal} dBm)`
                            : "Ethernet"}
                    </Text>
                </HStack>

                {/* Zones */}
                <Text fontSize="sm" color="gray.600">
                    Zones: {node.zonesCount}
                </Text>

                {/* Controller status */}
                <HStack justify="space-between">
                    <Badge
                        size="sm"
                        colorPalette={controllerColor}
                        variant="subtle"
                    >
                        {node.controllerStatus}
                    </Badge>

                    {(node.errors > 0 || node.warnings > 0) && (
                        <HStack spacing={2}>
                            {node.warnings > 0 && (
                                <Badge
                                    size="sm"
                                    colorPalette="orange"
                                    variant="subtle"
                                >
                                    {node.warnings} W
                                </Badge>
                            )}
                            {node.errors > 0 && (
                                <Badge
                                    size="sm"
                                    colorPalette="red"
                                    variant="subtle"
                                >
                                    {node.errors} E
                                </Badge>
                            )}
                        </HStack>
                    )}
                </HStack>

            </VStack>
        </Box>
    )
}
