import {
    Box,
    HStack,
    VStack,
    Text,
    Badge,
    Button
} from "@chakra-ui/react"
import {
    AlertTriangle,
    XCircle,
    Info
} from "lucide-react"

import { PanelButton } from "../../../components/ui/ActionButtons"

export default function AlertItem({ alert }) {

    const config = {
        error: {
            icon: XCircle,
            color: "red.100",
            badge: "red"
        },
        warning: {
            icon: AlertTriangle,
            color: "orange.100",
            badge: "orange"
        },
        info: {
            icon: Info,
            color: "blue.100",
            badge: "blue"
        }
    }[alert.type]

    const Icon = config.icon

    return (
        <Box
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={4}
            boxShadow="0 4px 14px rgba(15,23,42,0.05)"
        >
            <HStack align="flex-start" justify="space-between">

                <HStack align="flex-start" gap={3}>
                    {/* Add icon with background here if needed */}
                    <VStack align="start" gap={1}>
                        <HStack gap={4}>
                            <HStack gap={2}>
                                <Badge
                                    size="sm"
                                    colorPalette={config.badge}
                                    variant="subtle"
                                >
                                    {alert.type}
                                </Badge>
                                <Text fontWeight="600">
                                    {alert.title}
                                </Text>
                            </HStack>
                            <Text fontSize="xs" color="gray.400">
                                {/* Convert timestamp to human-readable format */}
                                {alert.timestamp.toLocaleString()}
                            </Text>
                        </HStack>

                        <Text fontSize="sm" color="gray.600">
                            {alert.message}
                        </Text>
                    </VStack>
                </HStack>

                <PanelButton size="xs" colorPalette="gray" variant="ghost">
                    Mark as read
                </PanelButton>

            </HStack>
        </Box>
    )
}
