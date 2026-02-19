import {
    Box,
    VStack,
    HStack,
    Text,
    Badge
} from "@chakra-ui/react"
import { Activity } from "lucide-react"

export default function ThreadCard({ thread }) {

    return (
        <Box
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={4}
            boxShadow="0 4px 14px rgba(15,23,42,0.05)"
        >
            <VStack align="stretch" spacing={3}>

                <HStack justify="space-between">
                    <HStack>
                        <Activity size={14} />
                        <Text fontSize="sm" fontWeight="500">
                            {thread.name}
                        </Text>
                    </HStack>

                    <Badge
                        size="sm"
                        colorPalette={thread.alive ? "green" : "red"}
                        variant="subtle"
                    >
                        {thread.alive ? "alive" : "stopped"}
                    </Badge>
                </HStack>

                <HStack justify="space-between">
                    <Text fontSize="xs" color="gray.500">
                        Started: {thread.startedAt}
                    </Text>
                    <Text fontSize="xs" color="gray.500">
                        Runtime: {thread.runtime}
                    </Text>
                </HStack>

            </VStack>
        </Box>
    )
}
