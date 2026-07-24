import { Box, Heading, Text, Stack, HStack, Button, Spinner } from "@chakra-ui/react"

function RangeFilterToggle({ rangeFilter }) {
    if (!rangeFilter?.options?.length) {
        return null
    }

    return (
        <HStack
            gap={1}
            p={1}
            borderRadius="full"
            bg="rgba(255,255,255,0.72)"
            border="1px solid rgba(56,178,172,0.16)"
            boxShadow="0 10px 24px rgba(15,23,42,0.04)"
        >
            {rangeFilter.options.map((option) => {
                const isActive = rangeFilter.value === option.value

                return (
                    <Button
                        key={option.value}
                        size="2xs"
                        variant={isActive ? "solid" : "ghost"}
                        borderRadius="full"
                        colorPalette="teal"
                        onClick={() => rangeFilter.onChange?.(option.value)}
                    >
                        {option.label}
                    </Button>
                )
            })}
        </HStack>
    )
}

export default function GlassPanelSection({
    title,
    description,
    children,
    actions,
    headerActions,
    rangeFilter,
    isLoading = false,
    ...props
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
            p={{ base: 4, md: 6 }}
            {...props}
        >
            {(title || description || actions || headerActions || rangeFilter) && (
                <HStack justify="space-between" align="flex-start" mb={5}>
                    <Stack spacing={1}>
                        {title && (
                            <HStack spacing={2} align="center">
                                <Heading size="sm" color="teal.600">
                                    {title}
                                </Heading>
                                {isLoading && (
                                    <Spinner
                                        size="xs"
                                        borderWidth="1px"
                                        animationDuration="0.8s"
                                        color="teal.600"
                                    />
                                )}
                            </HStack>
                        )}
                        {description && (
                            <Text fontSize="sm" color="gray.600">
                                {description}
                            </Text>
                        )}
                    </Stack>
                    <HStack gap={2} align="center">
                        <RangeFilterToggle rangeFilter={rangeFilter} />
                        {headerActions}
                        {actions}
                    </HStack>
                </HStack>
            )}

            {children}
        </Box>
    )
}
