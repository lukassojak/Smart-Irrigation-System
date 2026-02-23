import {
    Box,
    VStack,
    HStack,
    Text
} from "@chakra-ui/react"

export default function InfrastructureOverviewCard({
    icon: Icon,
    title,
    value,
    description,
    accentColor = "teal.500"
}) {
    return (
        <Box
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={5}
            boxShadow="0 4px 16px rgba(15,23,42,0.05)"
        >
            <VStack align="stretch" spacing={3}>

                <HStack justify="space-between">
                    <Text
                        fontSize="sm"
                        fontWeight="600"
                        color="gray.700"
                    >
                        {title}
                    </Text>

                    {Icon && (
                        <Box color={accentColor}>
                            <Icon size={16} />
                        </Box>
                    )}
                </HStack>

                <Text
                    fontSize="2xl"
                    fontWeight="600"
                    letterSpacing="-0.02em"
                >
                    {value}
                </Text>

                {description && (
                    <Text
                        fontSize="xs"
                        color="gray.500"
                    >
                        {description}
                    </Text>
                )}

            </VStack>
        </Box>
    )
}