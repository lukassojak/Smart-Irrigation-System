import React from 'react'
import { Box, Heading, Text, HStack, Stack } from '@chakra-ui/react'

export default function PageHeader({
    title,
    subtitle,
    actions,
    children
}) {
    return (
        <Box
            px={8}
            py={6}
            backdropFilter="blur(14px)"
            bg="rgba(255,255,255,0.45)"
            borderBottom="1px solid"
            borderColor="rgba(56,178,172,0.15)" // jemný teal nádech
        >
            <HStack justify="space-between" align="flex-start">
                <Stack>
                    <HStack gap={4} alignItems="baseline">
                        <Heading size="lg">{title}</Heading>
                        {subtitle && (
                            <Text fontSize="sm" opacity={0.8}>
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
