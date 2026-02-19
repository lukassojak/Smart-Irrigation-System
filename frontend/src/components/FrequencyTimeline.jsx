import { Box, Text, HStack, SimpleGrid, Badge } from '@chakra-ui/react'


export default function FrequencyTimeline({ settings }) {
    const {
        min_interval_days,
        max_interval_days,
        carry_over_volume,
        irrigation_volume_threshold_percent,
    } = settings

    // Determine timeline range
    let timelineDays = 30
    if (max_interval_days <= 6) timelineDays = 7
    else if (max_interval_days <= 13) timelineDays = 14

    const minPos = (min_interval_days / timelineDays) * 100
    const maxPos = (max_interval_days / timelineDays) * 100

    return (
        <Box mt={6}>
            <Text fontSize="sm" fontWeight="semibold" mb={3}>
                Irrigation Decision Timeline
            </Text>

            {/* Timeline */}
            <Box position="relative" h="20px">
                {/* Base line */}
                <Box
                    position="absolute"
                    top="9px"
                    left="0"
                    right="0"
                    h="2px"
                    bg="bg.subtle"
                    borderRadius="full"
                />

                {/* Day ticks */}
                {Array.from({ length: timelineDays + 1 }).map((_, day) => {
                    const left = (day / timelineDays) * 100
                    return (
                        <Box
                            key={day}
                            position="absolute"
                            left={`${left}%`}
                            top="6px"
                            w="1px"
                            h={day % 7 === 0 ? "10px" : "6px"}
                            bg={day % 7 === 0 ? "gray.400" : "gray.300"}
                        />
                    )
                })}

                {/* Allowed irrigation window */}
                <Box
                    position="absolute"
                    left={`${minPos}%`}
                    width={`${maxPos - minPos}%`}
                    top="8px"
                    h="4px"
                    bg="teal.600"
                    borderRadius="full"
                />

                {/* Min marker */}
                <Box
                    position="absolute"
                    left={`${minPos}%`}
                    top="2px"
                    w="2px"
                    h="16px"
                    bg="teal.600"
                />

                {/* Max marker */}
                <Box
                    position="absolute"
                    left={`${maxPos}%`}
                    top="2px"
                    w="2px"
                    h="16px"
                    bg="teal.600"
                />
            </Box>

            {/* Day labels */}
            <HStack justify="space-between" mt={2}>
                <Text fontSize="xs" color="fg.muted">Day 0</Text>
                <Text fontSize="xs" color="fg.muted">Day {timelineDays}</Text>
            </HStack>

            {/* Legend */}
            <SimpleGrid columns={{ base: 1, md: 3 }} gap={4} mt={4}>
                <Box>
                    <Text fontSize="xs" color="fg.muted">Allowed window</Text>
                    <Text fontSize="sm">
                        Day {min_interval_days} – {max_interval_days}
                    </Text>
                </Box>

                <Box>
                    <Text fontSize="xs" color="fg.muted">Carry-over volume</Text>
                    {carry_over_volume ? (
                        <Badge colorPalette="green" variant="subtle">
                            Enabled
                        </Badge>
                    ) : (
                        <Badge variant="subtle">
                            Disabled
                        </Badge>
                    )}
                </Box>

                <Box>
                    <Text fontSize="xs" color="fg.muted">Irrigation threshold</Text>
                    <Text fontSize="sm">
                        {irrigation_volume_threshold_percent} %
                    </Text>
                </Box>
            </SimpleGrid>
        </Box>
    )
}