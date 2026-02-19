import { Box, Stack, Text } from '@chakra-ui/react'

export function FullCorrectionIndicator({ label, value }) {
    return (
        <Stack spacing={2} align="center">
            <Text fontSize="xs" color="fg.subtle">
                {label}
            </Text>

            <Box
                w="72px"
                h="6px"
                bg="teal.100"
                borderRadius="full"
                position="relative"
            >
                <Box
                    position="absolute"
                    left="50%"
                    transform={`translateX(${value * 30}px)`}
                    w="6px"
                    h="6px"
                    bg="teal.500"
                    borderRadius="full"
                />
            </Box>
            <Stack>
                {/* Display percentage with +/- sign */}
                <Text fontSize="xs" color="fg.muted" fontWeight="semibold">
                    {value > 0 ? `+${(value * 100).toFixed(0)}%` : `${(value * 100).toFixed(0)}%`}
                </Text>
            </Stack>
        </Stack>
    )
}


export function LimitedCorrectionIndicator({ label, value }) {
    return (
        <Stack spacing={1} align="center">
            <Text fontSize="xs" color="fg.subtle">
                {label}
            </Text>
            <Box
                w="60px"
                h="6px"
                bg="bg.subtle"
                borderRadius="full"
                position="relative"
            >
                <Box
                    position="absolute"
                    left="50%"
                    transform={`translateX(${value * 30}px)`}
                    w="6px"
                    h="6px"
                    bg="teal.500"
                    borderRadius="full"
                />
            </Box>
        </Stack>
    )
}