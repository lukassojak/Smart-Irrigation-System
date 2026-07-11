import { useEffect, useState } from "react"
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
    const [compact, setCompact] = useState(false)

    useEffect(() => {
        const onScroll = () => {
            setCompact(window.scrollY > 40)
        }

        window.addEventListener("scroll", onScroll)
        return () => window.removeEventListener("scroll", onScroll)
    }, [])

    return (
        <Box
            px={{ base: 4, md: 8 }}
            py={compact ? 3 : 6}
            backdropFilter="blur(20px) saturate(180%)"
            bg="rgba(255,255,255,0.72)"
            borderBottom="1px solid"
            borderColor="rgba(56,178,172,0.08)"
            boxShadow="
                inset 0 1.5px 0 rgba(255,255,255,0.8),
                0 8px 30px rgba(15, 23, 42, 0.035)
            "
            /* if on mobile viewport, position is sticky, otherwise, position is relative */
            position={isMobile ? "sticky" : "relative"}
            top={0}
            zIndex={isMobile ? "sticky" : "relative"}
            transition="all 0.18s ease"
        >
            <Grid
                templateColumns={
                    isMobile
                        ? "auto 1fr auto"
                        : "1fr auto"
                }
                alignItems={compact && isMobile ? "center" : "start"}
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
                                size={compact ? "sm" : "md"}
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
                                    opacity={compact ? 0 : 1}
                                    maxHeight={compact ? 0 : "40px"}
                                    overflow="hidden"
                                    transition="opacity .18s ease, max-height .18s ease"
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

                    {!compact && children}
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
