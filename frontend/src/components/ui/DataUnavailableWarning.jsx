import { Box, HStack, Text, Stack } from "@chakra-ui/react"
import { CloudOff } from "lucide-react"


export default function DataUnavailableWarning({
    message = "Data is currently unavailable.",
    icon: Icon = CloudOff,
    error = undefined,
}) {
    return (
        <HStack gap={4} p={6} bg="rgba(255,193,7,0.05)" borderRadius="md">
            <Box w="32px" h="32px" display="flex" alignItems="center" justifyContent="center" flexShrink={0}>
                <Icon size={20} color="#F59E0B" />
            </Box>
            <Stack gap={2}>
                <Text fontSize="sm" color="fg.muted">
                    {message}
                </Text>
                {error && (
                    <Text fontSize="xs" color="fg.subtle" fontWeight="500">
                        {error}
                    </Text>
                )}
            </Stack>
        </HStack>
    )
}
