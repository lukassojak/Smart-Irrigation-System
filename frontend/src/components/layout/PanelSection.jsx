import { Box, Heading, Text, Stack } from "@chakra-ui/react"

export default function PanelSection({
    title,
    description,
    children,
    borderColor = "border", // Default border color
}) {
    return (
        // Reactive Edge Glass visual style - Solid Surface variant
        <Box
            bg="rgba(255,255,255,0.92)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={5}
            boxShadow="0 4px 16px rgba(15, 23, 42, 0.05)"
            textAlign="left"
        >
            {(title || description) && (
                <Stack mb={4}>
                    {title && (
                        <Heading size="sm" color="teal.600">
                            {title}
                        </Heading>
                    )}

                    {description && (
                        <Text fontSize="sm" color="fg.muted">
                            {description}
                        </Text>
                    )}
                </Stack>
            )}

            {children}
        </Box>
    )
}
