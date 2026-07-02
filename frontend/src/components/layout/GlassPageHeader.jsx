import React from 'react'
import {
    Box,
    Heading,
    Text,
    HStack,
    Stack,
    Grid,
    useBreakpointValue,
    IconButton
} from "@chakra-ui/react"
import { MoreVertical, LayoutList } from "lucide-react"

import MobileActionsDrawer from "./MobileActionsDrawer"


export function HeaderActions({ children }) {
    return (
        <HStack gap={3} align="center">
            {children}
        </HStack>
    )
}

export default function GlassPageHeader({
    title,
    subtitle,
    actions,
    children,
    showMobileMenuButton = false,
    onMobileMenuClick
}) {

    const isMobile = useBreakpointValue({ base: true, md: false })

    return (
        <Box
            px={{ base: 4, md: 8 }}
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
            <Grid
                templateColumns={
                    isMobile
                        ? "auto 1fr auto"
                        : "1fr auto"
                }
                alignItems="start"
                gap={4}
            >
                {/* LEFT SIDE */}
                {isMobile && (
                    <Box
                        display="flex"
                        alignItems="flex-start"
                        pt={1}
                    >
                        {showMobileMenuButton && (
                            <IconButton
                                aria-label="Open menu"
                                variant="ghost"
                                size="sm"
                                onClick={onMobileMenuClick}
                            >
                                <LayoutList size={24} />
                            </IconButton>
                        )}
                    </Box>
                )}

                <Stack
                    gap={1}
                    align="flex-start"
                >
                    {isMobile ? (
                        <>
                            <Heading
                                size="md"
                                fontWeight="600"
                                letterSpacing="-0.01em"
                                color="gray.800"
                            >
                                {title}
                            </Heading>

                            {subtitle && (
                                <Text
                                    fontSize="xs"
                                    color="gray.600"
                                    fontWeight="500"
                                >
                                    {subtitle}
                                </Text>
                            )}
                        </>
                    ) : (
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
                    )}

                    {children}
                </Stack>

                {/* RIGHT SIDE */}
                {isMobile ? (
                    <Box
                        display="flex"
                        justifyContent="flex-end"
                        pt={1}
                    >
                        {actions && (
                            <MobileActionsDrawer
                                actions={actions}
                            />
                        )}
                    </Box>
                ) : (
                    <HStack gap={3}>
                        {actions}
                    </HStack>
                )}
            </Grid>
        </Box>
    )
}
