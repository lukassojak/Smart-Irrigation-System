import { Box, HStack, Text } from "@chakra-ui/react"
import { CloudOff } from "lucide-react"


export default function DataUnavailableWarning({
    message = "Data is currently unavailable. Please try again.",
    icon: Icon = CloudOff,
}) {
    return (
        <HStack gap={4} p={6} bg="rgba(255,193,7,0.05)" borderRadius="md">
            <Box w="32px" h="32px" display="flex" alignItems="center" justifyContent="center" flexShrink={0}>
                <Icon size={20} color="#F59E0B" />
            </Box>
            <Text fontSize="sm" color="fg.muted">
                {message}
            </Text>
        </HStack>
    )
}
