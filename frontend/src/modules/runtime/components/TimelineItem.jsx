import {
    Box,
    HStack,
    Text
} from "@chakra-ui/react"
import { Clock } from "lucide-react"

export default function TimelineItem({ item }) {

    const isCompleted = item.status === "completed"
    const scheduledTimeUtc = item.scheduledTime.toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
        hour12: false,
        timeZone: "UTC"
    })

    return (
        <HStack align="flex-start" gap={4} position="relative">

            {/* Indicator */}
            <Box
                position="absolute"
                left="-22px"
                top="50%"
                transform="translateY(-50%)"
                w="10px"
                h="10px"
                borderRadius="full"
                bg={isCompleted ? "green.400" : "teal.400"}
                border="2px solid white"
                boxShadow="0 0 0 2px rgba(56,178,172,0.15)"
                zIndex="1"
            />

            <Box
                flex="1"
                minH="40px"
                bg="rgba(255,255,255,0.95)"
                borderWidth="1px"
                borderColor="rgba(56,178,172,0.06)"
                borderRadius="lg"
                p={4}
                boxShadow="0 4px 14px rgba(15,23,42,0.05)"
            >
                <HStack justify="space-between">
                    <HStack gap={6}>
                        <HStack gap={1}>
                            <Clock size={14} />
                            <Text fontSize="sm" color="gray.600">
                                {scheduledTimeUtc}
                            </Text>
                        </HStack>
                        <HStack gap={2} align="center">
                            {/* Zone ID Icon */}
                            <Box
                                bg="teal.50"
                                borderRadius="md"
                                px={2}
                                py={1}
                            >
                                <Text fontSize="sm" color="teal.700" fontWeight="bold">
                                    {item.id}
                                </Text>
                            </Box>
                            <Text fontWeight="600">
                                {item.zoneName}
                            </Text>
                        </HStack>
                    </HStack>

                </HStack>
            </Box>

        </HStack>
    )
}
