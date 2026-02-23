import { Box, Heading, Text, Stack, HStack } from "@chakra-ui/react"

export default function GlassPanelSection({
    title,
    description,
    children,
    actions
}) {
    return (
        <Box
            bg="rgba(255,255,255,0.55)"
            backdropFilter="blur(18px) saturate(160%)"
            borderRadius="xl"
            border="1px solid rgba(56,178,172,0.10)"
            boxShadow="
                inset 0 1px 0 rgba(255,255,255,0.8),
                0 12px 30px rgba(15,23,42,0.04)
            "
            p={{ base: 2, md: 6 }}
        >
            {(title || description || actions) && (
                <HStack justify="space-between" align="flex-start" mb={5}>
                    <Stack spacing={1}>
                        {title && (
                            <Heading size="sm" color="teal.600">
                                {title}
                            </Heading>
                        )}
                        {description && (
                            <Text fontSize="sm" color="gray.600">
                                {description}
                            </Text>
                        )}
                    </Stack>
                    {actions}
                </HStack>
            )}

            {children}
        </Box>
    )
}
