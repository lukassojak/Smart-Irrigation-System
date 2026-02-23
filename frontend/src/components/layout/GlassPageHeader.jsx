import React from 'react'
import {
    Box,
    Heading,
    Text,
    HStack,
    Stack,
    Grid,
    useBreakpointValue
} from "@chakra-ui/react"
import { MoreVertical } from "lucide-react"
import { useOutletContext } from "react-router-dom"


export function HeaderActions({ children }) {
    const { isMobile, openMobileSidebar } = useOutletContext() || {}
    return isMobile ? (
        <Stack align="stretch">
            {children}
        </Stack>
    ) : (
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
                templateColumns={isMobile ? "1fr auto" : "1fr auto"}
                alignItems="start"
                gap={4}
            >
                {/* LEFT SIDE */}
                <Stack
                    spacing={isMobile ? 1 : 0}
                >
                    {isMobile ? (
                        <>
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
                <Stack
                    direction={isMobile ? "column" : "row"}
                    gap={3}
                    align={isMobile ? "stretch" : "center"}
                >
                    {showMobileMenuButton && (
                        <Box
                            cursor="pointer"
                            onClick={onMobileMenuClick}
                            alignSelf={isMobile ? "stretch" : "center"}
                            textAlign="center"
                        >
                            <MoreVertical size={20} />
                        </Box>
                    )}

                    {actions}
                </Stack>
            </Grid>
        </Box>
    )
}
