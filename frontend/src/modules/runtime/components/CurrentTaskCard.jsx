import {
    Box,
    VStack,
    HStack,
    Text,
    Badge
} from "@chakra-ui/react"
import { Droplets } from "lucide-react"
import { Progress } from "@chakra-ui/react"

import { PanelButtonDanger } from "../../../components/ui/ActionButtons"
import useRuntimeControlState from "../../../hooks/useRuntimeControlState"

export default function CurrentTaskCard({ task, isStopping, onStop }) {
    const {
        taskState,
    } = useRuntimeControlState({
        task,
        isStopping,
    })

    const progressValue = taskState?.progressValue ?? 0
    const progressLabel = taskState?.progressLabel ?? "0"
    const isStale = taskState?.isStale === true

    return (
        <Box
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.12)"
            borderRadius="lg"
            p={5}
            boxShadow="0 4px 18px rgba(15, 23, 42, 0.06)"
            opacity={isStale ? 0.6 : 1}
            filter={isStale ? "grayscale(0.3)" : "grayscale(0)"}
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
                            {isStale ? (
                                <Badge
                                    size="sm"
                                    colorPalette={taskState?.statusColorPalette ?? "gray"}
                                    variant="subtle"
                                >
                                    {taskState?.statusLabel ?? "Stopped"}
                                </Badge>
                            ) : (
                                <Badge
                                    size="sm"
                                    colorPalette="blue"
                                    variant="subtle"
                                >
                                    Irrigating
                                </Badge>
                            )}
                        </HStack>
                    </HStack>
                    {!task.stale && (
                        <PanelButtonDanger
                            size="sm"
                            variant="subtle"
                            onClick={() => onStop?.(task.id)}
                            isDisabled={taskState?.isStopDisabled}
                            loading={taskState?.isStopLoading}
                        >
                            Stop
                        </PanelButtonDanger>
                    )}
                </HStack>

                <Progress.Root
                    value={progressValue}
                    borderRadius="md"
                    height="8px"
                >
                    <Progress.Track bg="gray.100">
                        <Progress.Range bg="teal.400" />
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
                        {progressLabel}%
                    </Text>
                </HStack>

            </VStack>
        </Box>
    )
}
