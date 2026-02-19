import React from 'react'
import { Button, Box, Heading, Text, HStack, Stack } from '@chakra-ui/react'


export function HeaderActions({ children }) {
    return (
        <HStack
            spacing={3}
            align="center"
        >
            {children}
        </HStack>
    )
}

export default function GlassPageHeader({
    title,
    subtitle,
    actions,
    children
}) {
    return (
        // Reactive Edge Glass visual style
        <Box
            px={8}
            py={6}
            backdropFilter="blur(20px) saturate(160%)"
            bg="rgba(255,255,255,0.36)"
            borderBottom="1px solid"
            borderColor="rgba(56,178,172,0.08)"
            boxShadow="
        inset 0 1.5px 0 rgba(255,255,255,0.8),
        0 8px 30px rgba(15, 23, 42, 0.035)
    "
        >
            <HStack justify="space-between" align="flex-start">
                <Stack>
                    <HStack gap={4} alignItems="baseline">
                        <Heading
                            size="lg"
                            fontWeight="600"
                            letterSpacing="-0.01em"
                            color="gray.800"
                        >
                            {title}
                        </Heading>
                        {subtitle && (
                            <Text
                                fontSize="sm"
                                color="gray.600"
                                fontWeight="500"
                            >
                                {subtitle}
                            </Text>
                        )}
                    </HStack>
                    {children}
                </Stack>
                {actions}
            </HStack>
        </Box>
    )
}
