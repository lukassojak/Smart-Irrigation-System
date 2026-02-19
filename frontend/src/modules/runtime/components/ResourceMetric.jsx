import {
    VStack,
    HStack,
    Text,
    Progress
} from "@chakra-ui/react"

export default function ResourceMetric({
    label,
    value,
    color = "teal.500"
}) {
    return (
        <VStack align="stretch" spacing={2}>
            <HStack justify="space-between">
                <Text fontSize="sm" color="gray.600">
                    {label}
                </Text>
                <Text fontSize="sm" fontWeight="600">
                    {value}%
                </Text>
            </HStack>

            <Progress.Root value={value} height="6px" borderRadius="md">
                <Progress.Track bg="gray.100">
                    <Progress.Range bg={color} />
                </Progress.Track>
            </Progress.Root>
        </VStack>
    )
}
