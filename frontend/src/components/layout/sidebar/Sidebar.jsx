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
} from "lucide-react"

export default function Sidebar() {
    const navigate = useNavigate()

    return (
        <Box
            w="260px"
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
            px={5}
            py={6}
        >
            {/* Branding with link to homepage */}
            <HStack mb={8} align="center" gap={3} cursor="pointer" onClick={() => navigate("/")}>
                <Image
                    src="/logo.png"
                    alt="Smart Irrigation System"
                    boxSize="40px"
                />
                <VStack align="start" gap={0}>
                    <Text fontSize="sm" fontWeight="600">
                        Smart Irrigation
                    </Text>
                    <Text fontSize="xs" color="gray.500">
                        v0.8.0
                    </Text>
                </VStack>
            </HStack>

            {/* Navigation */}
            <VStack align="stretch" spacing={6} flex="1" overflowY="auto">

                <SidebarSection title="Runtime">
                    <SidebarItem to="/dashboard" icon={LayoutDashboard}>
                        Dashboard
                    </SidebarItem>
                    <SidebarItem to="/manual" icon={Droplets}>
                        Manual Control
                    </SidebarItem>
                    <SidebarItem to="/notifications" icon={Bell}>
                        Notifications
                    </SidebarItem>
                    <SidebarItem to="/runtime/nodes" icon={Activity}>
                        Monitoring
                    </SidebarItem>
                </SidebarSection>

                <SidebarSection title="History">
                    <SidebarItem to="/statistics" icon={BarChart3}>
                        Statistics
                    </SidebarItem>
                    <SidebarItem to="/irrigation-history" icon={History}>
                        Irrigation History
                    </SidebarItem>
                    <SidebarItem to="/weather" icon={Cloud}>
                        Weather History
                    </SidebarItem>
                </SidebarSection>

                <SidebarSection title="Configuration">
                    <SidebarItem to="/configuration/nodes" icon={SlidersHorizontal}>
                        Nodes
                    </SidebarItem>
                    <SidebarItem to="/configuration/nodes/new" icon={SlidersHorizontal}>
                        Create Node
                    </SidebarItem>
                </SidebarSection>

                <SidebarSection title="System">
                    <SidebarItem to="/settings" icon={Settings}>
                        Settings
                    </SidebarItem>
                </SidebarSection>

            </VStack>
        </Box>
    )
}
