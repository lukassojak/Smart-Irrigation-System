import {
    Box,
    VStack,
    HStack,
    Text,
    Badge,
    Button
} from "@chakra-ui/react"
import { Droplets } from "lucide-react"
import { Progress } from "@chakra-ui/react"

import { PanelButtonDanger } from "../../../components/ui/ActionButtons"

export default function CurrentTaskCard({ task }) {

    return (
        <Box
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.12)"
            borderRadius="lg"
            p={5}
            boxShadow="0 4px 18px rgba(15, 23, 42, 0.06)"
        >
            <VStack align="stretch" gap={3}>

                <HStack justify="space-between">

                    <HStack gap={3}>
                        <Box bg="teal.50" p={2} borderRadius="md">
                            <Droplets size={18} color="#319795" />
                        </Box>

                        <HStack gap={4}>
                            <Text fontWeight="600">
                                {task.zoneName}
                            </Text>

                            <Badge
                                size="sm"
                                colorPalette="green"
                                variant="subtle"
                            >
                                Irrigating
                            </Badge>
                        </HStack>
                    </HStack>

                    <PanelButtonDanger
                        size="sm"
                        variant="subtle"
                    >
                        Stop
                    </PanelButtonDanger>
                </HStack>

                <Progress.Root
                    value={task.progress}
                    borderRadius="md"
                    height="8px"
                >
                    <Progress.Track bg="gray.100">
                        <Progress.Range bg="teal.500" />
                    </Progress.Track>
                </Progress.Root>


                <HStack justify="space-between">
                    <HStack gap={4}>
                        <Text fontSize="sm" color="gray.600">
                            {task.currentVolume} / {task.targetVolume} L
                        </Text>

                        <Text fontSize="xs" color="gray.500">
                            {task.remainingMinutes} min remaining
                        </Text>
                    </HStack>

                    <Text
                        fontSize="sm"
                        fontWeight="600"
                    >
                        {task.progress}%
                    </Text>
                </HStack>

            </VStack>
        </Box>
    )
}
