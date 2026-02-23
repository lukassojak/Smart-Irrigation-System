import {
    Box,
    Grid,
    Stack,
    VStack,
    HStack,
    Text
} from "@chakra-ui/react"
import {
    LayoutDashboard,
    Droplets,
    BarChart3,
    Cloud,
    Settings,
    Bell,
    History,
    SlidersHorizontal,
    Activity
} from "lucide-react"
import { useNavigate } from "react-router-dom"

import GlassPageHeader from "./components/layout/GlassPageHeader"
import GlassPanelSection from "./components/layout/GlassPanelSection"

export default function HomePage() {

    const navigate = useNavigate()

    const sections = [
        {
            title: "Dashboard",
            description: "Live overview of irrigation system status",
            icon: LayoutDashboard,
            path: "/dashboard"
        },
        {
            title: "Manual Control",
            description: "Override automatic irrigation",
            icon: Droplets,
            path: "/manual"
        },
        {
            title: "Notifications",
            description: "System alerts and activity logs",
            icon: Bell,
            path: "/notifications"
        },
        {
            title: "Monitoring",
            description: "Real-time hardware status and system health",
            icon: Activity,
            path: "/runtime/nodes"
        },
        {
            title: "Statistics",
            description: "Water usage and historical analytics",
            icon: BarChart3,
            path: "/statistics"
        },
        {
            title: "Irrigation History",
            description: "Past irrigation events and performance",
            icon: History,
            path: "/irrigation-history"
        },
        {
            title: "Weather history",
            description: "Weather data impacting irrigation",
            icon: Cloud,
            path: "/weather"
        },
        {
            title: "Configuration",
            description: "Device management and zone setup",
            icon: SlidersHorizontal,
            path: "/configuration/nodes"
        },
        {
            title: "System Settings",
            description: "Global configuration and preferences",
            icon: Settings,
            path: "/settings"
        }
    ]

    return (
        <Box>

            <GlassPageHeader
                title="Smart Irrigation System"
                subtitle="Control & Monitoring Interface"
            >
                <Text fontSize="sm" color="gray.600">
                    Select a module to continue.
                </Text>
            </GlassPageHeader>

            <Stack
                gap={8}
                px={{ base: 2, md: 6 }}
                py={{ base: 4, md: 8 }}
            >

                <GlassPanelSection
                    title="Modules"
                    description="System domains and operational tools"
                >
                    <Grid
                        templateColumns={{
                            base: "1fr",
                            md: "1fr 1fr",
                            xl: "1fr 1fr 1fr"
                        }}
                        gap={6}
                    >
                        {sections.map(section => (
                            <ModuleCard
                                key={section.title}
                                section={section}
                                onClick={() => navigate(section.path)}
                            />
                        ))}
                    </Grid>
                </GlassPanelSection>

            </Stack>

        </Box>
    )
}

function ModuleCard({ section, onClick }) {

    const Icon = section.icon

    return (
        <Box
            onClick={onClick}
            cursor="pointer"
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={6}
            boxShadow="0 4px 16px rgba(15,23,42,0.05)"
            transition="all 0.15s ease"
            _hover={{
                borderColor: "rgba(56,178,172,0.18)",
                boxShadow: "0 6px 22px rgba(15,23,42,0.06)",
                transform: "translateY(-2px)"
            }}
        >
            <VStack align="start" spacing={4}>

                <Box
                    bg="teal.50"
                    p={3}
                    borderRadius="md"
                >
                    <Icon size={20} color="#319795" />
                </Box>

                <VStack align="start" spacing={1}>
                    <Text fontWeight="600">
                        {section.title}
                    </Text>
                    <Text fontSize="sm" color="gray.600">
                        {section.description}
                    </Text>
                </VStack>

            </VStack>
        </Box>
    )
}