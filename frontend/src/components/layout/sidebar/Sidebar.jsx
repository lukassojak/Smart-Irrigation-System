// components/layout/sidebar/Sidebar.jsx

import { Box, VStack, HStack, Text, Image } from "@chakra-ui/react"
import SidebarSection from "./SidebarSection"
import SidebarItem from "./SidebarItem"
import { useNavigate } from "react-router-dom"


import {
    LayoutDashboard,
    Droplets,
    Bell,
    Activity,
    BarChart3,
    Cloud,
    Settings,
    SlidersHorizontal,
    History,
    ChevronLeft,
    ChevronRight
} from "lucide-react"

export default function Sidebar({ isCollapsed, onToggle }) {
    const navigate = useNavigate()

    return (
        <Box
            w={isCollapsed ? "72px" : "260px"}
            h="100vh"
            position="fixed"
            left="0"
            top="0"
            display="flex"
            flexDirection="column"
            bg="rgba(255,255,255,0.72)"
            backdropFilter="blur(10px) saturate(180%)"
            borderRight="1px solid rgba(56,178,172,0.05)"
            boxShadow="4px 0 24px rgba(15,23,42,0.03)"
            px={isCollapsed ? 2 : 5}
            py={6}
            transition="width 0.2s ease, padding 0.2s ease"
        >
            {/* Branding with link to homepage */}
            <HStack mb={8} align="center" gap={3} cursor="pointer" onClick={() => navigate("/")}>
                <Image
                    src="/logo.png"
                    alt="Smart Irrigation System"
                    boxSize="40px"
                />
                {!isCollapsed && (
                    <VStack align="start" gap={0}>
                        <Text fontSize="sm" fontWeight="600">
                            Smart Irrigation
                        </Text>
                        <Text fontSize="xs" color="gray.500">
                            v0.8.0
                        </Text>
                    </VStack>
                )}
            </HStack>

            {/* Navigation */}
            <VStack align="stretch" spacing={6} flex="1" overflowY="auto">

                {/* Show title only when expanded */}
                <SidebarSection
                    title={!isCollapsed ? "Runtime" : null}
                >
                    <SidebarItem to="/dashboard" icon={LayoutDashboard} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Dashboard" : null}
                    </SidebarItem>
                    <SidebarItem to="/manual" icon={Droplets} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Manual Control" : null}
                    </SidebarItem>
                    <SidebarItem to="/notifications" icon={Bell} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Notifications" : null}
                    </SidebarItem>
                    <SidebarItem to="/runtime/nodes" icon={Activity} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Monitoring" : null}
                    </SidebarItem>
                </SidebarSection>

                <SidebarSection
                    title={!isCollapsed ? "History" : null}
                >
                    <SidebarItem to="/statistics" icon={BarChart3} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Statistics" : null}
                    </SidebarItem>
                    <SidebarItem to="/irrigation-history" icon={History} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Irrigation History" : null}
                    </SidebarItem>
                    <SidebarItem to="/weather" icon={Cloud} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Weather History" : null}
                    </SidebarItem>
                </SidebarSection>

                <SidebarSection
                    title={!isCollapsed ? "Configuration" : null}
                >
                    <SidebarItem to="/configuration/nodes" icon={SlidersHorizontal} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Nodes" : null}
                    </SidebarItem>
                    <SidebarItem to="/configuration/nodes/new" icon={SlidersHorizontal} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Add Node" : null}
                    </SidebarItem>
                </SidebarSection>

                <SidebarSection
                    title={!isCollapsed ? "Settings" : null}
                >
                    <SidebarItem to="/settings" icon={Settings} isCollapsed={isCollapsed}>
                        {!isCollapsed ? "Settings" : null}
                    </SidebarItem>
                </SidebarSection>

                {/* Collapse/Expand Button */}
                <Box
                    mt="auto"
                    p={2}
                    borderRadius="md"
                    cursor="pointer"
                    _hover={{ bg: "rgba(56,178,172,0.06)" }}
                    onClick={onToggle}
                >
                    <HStack justify={isCollapsed ? "center" : "flex-start"} spacing={isCollapsed ? 0 : 3}>
                        {isCollapsed ? (
                            <ChevronRight size={18} strokeWidth={2} color="#4A5568" />
                        ) : (
                            <ChevronLeft size={18} strokeWidth={2} color="#4A5568" />
                        )}

                        {!isCollapsed && (
                            <Text fontSize="sm" fontWeight="500" color="gray.700">
                                {isCollapsed ? "" : "Collapse"}
                            </Text>
                        )}
                    </HStack>
                </Box>

            </VStack>
        </Box >
    )
}
