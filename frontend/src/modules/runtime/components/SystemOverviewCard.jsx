import {
    Box,
    VStack,
    HStack,
    Text,
    Badge
} from "@chakra-ui/react"

export default function SystemOverviewCard({
    icon: Icon,
    title,
    value,
    description,
    status = "neutral", // success | warning | error | neutral
    footer
}) {

    const statusColor = {
        success: "green.400",
        warning: "orange.400",
        error: "red.400",
        neutral: "gray.300"
    }[status]

    return (
        <Box
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={5}
            boxShadow="0 4px 16px rgba(15, 23, 42, 0.05)"
            transition="all 0.15s ease"
            _hover={{
                borderColor: "rgba(56,178,172,0.18)",
                boxShadow: "0 6px 20px rgba(15,23,42,0.06)",
                transform: "translateY(-2px)"
            }}
        >
            <VStack align="start">

                <HStack gap={3}>
                    <Box bg="teal.50" p={2} borderRadius="md">
                        <Icon size={18} color="#319795" />
                    </Box>

                    {/* Title on the left, status dot on the right side of the card */}
                    <HStack justify="space-between" w="full">
                        <Text fontSize="sm" fontWeight="600" color="gray.700">
                            {title}
                        </Text>
                    </HStack>
                </HStack>

                <Text
                    fontSize="2xl"
                    fontWeight="600"
                    color="gray.800"
                >
                    {value}
                </Text>

                {description && (
                    <Text fontSize="sm" color="gray.500">
                        {description}
                    </Text>
                )}

                {footer && (
                    <HStack gap={2} pt={2}>
                        {footer}
                    </HStack>
                )}

            </VStack>
        </Box>
    )
}
