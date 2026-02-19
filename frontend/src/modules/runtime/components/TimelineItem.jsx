import {
    Box,
    HStack,
    VStack,
    Text,
    Badge
} from "@chakra-ui/react"
import { Clock } from "lucide-react"

export default function TimelineItem({ item }) {

    const isCompleted = item.status === "completed"

    return (
        <HStack align="flex-start" gap={4} position="relative">

            {/* Indicator */}
            <Box
                position="absolute"
                left="-22px"
                top="10px"
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
                                {item.time}
                            </Text>
                        </HStack>
                        <Text fontWeight="600">
                            {item.zoneName}
                        </Text>
                    </HStack>

                    <Badge
                        size="sm"
                        colorPalette={isCompleted ? "green" : "teal"}
                        variant="subtle"
                    >
                        {item.status}
                    </Badge>

                </HStack>
            </Box>

        </HStack>
    )
}
