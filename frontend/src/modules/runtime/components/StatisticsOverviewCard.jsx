import {
    Box,
    VStack,
    HStack,
    Text
} from "@chakra-ui/react"

export default function StatisticsOverviewCard({
    icon: Icon,
    label,
    value,
    description,
    footer
}) {
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
            <VStack align="start" spacing={3}>

                <HStack gap={3}>
                    {Icon && (
                        <Box bg="teal.50" p={2} borderRadius="md">
                            <Icon size={18} color="#319795" />
                        </Box>
                    )}

                    <Text
                        fontSize="sm"
                        fontWeight="600"
                        color="gray.700"
                    >
                        {label}
                    </Text>
                </HStack>

                <Text
                    fontSize="2xl"
                    fontWeight="600"
                    color="gray.800"
                    letterSpacing="-0.02em"
                >
                    {value}
                </Text>

                {description && (
                    <Text fontSize="sm" color="gray.500">
                        {description}
                    </Text>
                )}

                {footer && (
                    <Box pt={2}>
                        {footer}
                    </Box>
                )}

            </VStack>
        </Box>
    )
}