import {
    Box,
    Grid,
    Stack,
    VStack,
    HStack,
    Text,
    Badge,
    Progress
} from "@chakra-ui/react"
import {
    Server,
    Cpu,
    MemoryStick,
    Wifi,
    Activity,
    ShieldCheck,
    Network,
    ArrowUpFromDot

} from "lucide-react"
import { useParams } from "react-router-dom"
import { useOutletContext } from "react-router-dom"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import ThreadCard from "../components/ThreadCard"
import ResourceMetric from "../components/ResourceMetric"

export default function RuntimeNodeDetailPage() {

    const { nodeId } = useParams()

    // --- Fake Data ---
    const node = {
        id: nodeId,
        name: "Garden Main Controller",
        hardware: "Raspberry Pi Zero 2 W",
        online: true,
        ip: "192.168.1.25",
        connection: "wifi",
        signal: -58,
        uptime: "3 days 12h",
        cpu: 42,
        memory: 63,
        serviceStatus: "running", // running | stopped | error
        controllerStatus: "running"
    }

    const threads = [
        { name: "scheduler-task-scheduler", type: "scheduler", alive: true, startedAt: "06:00:12", runtime: "13h 21m" },
        { name: "scheduler-auto-irrigation-service", type: "scheduler", alive: true, startedAt: "19:20:03", runtime: "0h 1m" },
        { name: "irrigation-1", type: "irrigation", alive: true, startedAt: "19:00:00", runtime: "0h 20m" },
        { name: "irrigation-2", type: "irrigation", alive: true, startedAt: "19:00:00", runtime: "0h 20m" },
        { name: "general-weather-fetcher", type: "general", alive: true, startedAt: "05:45:00", runtime: "14h 30m" },
        { name: "general-flow-monitor", type: "general", alive: true, startedAt: "07:15:30", runtime: "12h 0m" },
        { name: "general-mqtt-publisher", type: "general", alive: true, startedAt: "18:00:00", runtime: "26h 0m" },
        { name: "general-ota-updater", type: "general", alive: false, startedAt: "18:00:00", runtime: "26h 0m" },
        { name: "executor-auto_irrigation_cycle", type: "executor", alive: false, startedAt: "18:00:00", runtime: "26h 0m" },
    ]

    const groupedThreads = threads.reduce((acc, t) => {
        acc[t.type] = acc[t.type] || []
        acc[t.type].push(t)
        return acc
    }, {})

    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    return (
        <Box>

            <GlassPageHeader
                title={node.name}
                subtitle="Node runtime detail"
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <Stack gap={8} p={8}>

                {/* SECTION 1 + 2 – Overview & Service */}
                <Grid
                    templateColumns={{ base: "1fr", xl: "1fr 1fr" }}
                    gap={8}
                >

                    {/* Node Overview */}
                    <GlassPanelSection
                        title="Node Overview"
                        description="Hardware and connectivity information"
                    >
                        <Stack gap={6}>

                            <VStack align="start" gap={2}>
                                <HStack mb={2}>
                                    <Server size={16} />
                                    <Text fontWeight="600">{node.hardware}</Text>
                                </HStack>
                                <HStack>
                                    <Network size={14} color="#319795" />
                                    <Text fontSize="sm" color="gray.600">
                                        IP: {node.ip}
                                    </Text>
                                </HStack>

                                <HStack>
                                    <ArrowUpFromDot size={14} color="#319795" />
                                    <Text fontSize="sm" color="gray.600">
                                        Uptime: {node.uptime}
                                    </Text>
                                </HStack>

                                <HStack>
                                    <Wifi size={14} color="#319795" />
                                    <Text fontSize="sm" color="gray.600">
                                        {node.connection} ({node.signal} dBm)
                                    </Text>
                                </HStack>
                            </VStack>

                            <Stack gap={5}>
                                <ResourceMetric
                                    label="CPU Usage"
                                    value={node.cpu}
                                    color="teal.500"
                                />
                                <ResourceMetric
                                    label="Memory Usage"
                                    value={node.memory}
                                    color="orange.400"
                                />
                            </Stack>

                        </Stack>
                    </GlassPanelSection>

                    {/* Service Section */}
                    <GlassPanelSection
                        title="Smart Irrigation Node Process"
                        description="Systemd service and controller status"
                    >
                        <Stack gap={6}>

                            <HStack justify="space-between">
                                <VStack align="start" gap={1}>
                                    <Text fontSize="sm" color="gray.600">
                                        Service Name
                                    </Text>
                                    <Text fontWeight="600">
                                        smart-irrigation-node.service
                                    </Text>
                                </VStack>

                                <Badge
                                    size="sm"
                                    colorPalette={
                                        node.serviceStatus === "running"
                                            ? "green"
                                            : "red"
                                    }
                                    variant="subtle"
                                >
                                    {node.serviceStatus}
                                </Badge>
                            </HStack>

                            <HStack justify="space-between">
                                <VStack align="start" gap={1}>
                                    <Text fontSize="sm" color="gray.600">
                                        Controller Status
                                    </Text>
                                    <Text fontWeight="600">
                                        {node.controllerStatus}
                                    </Text>
                                </VStack>

                                <Badge
                                    size="sm"
                                    colorPalette={
                                        node.controllerStatus === "running"
                                            ? "green"
                                            : "gray"
                                    }
                                    variant="subtle"
                                >
                                    active
                                </Badge>
                            </HStack>

                            <VStack align="start" gap={1}>
                                <Text fontSize="sm" color="gray.600">
                                    Started At
                                </Text>
                                <Text fontSize="sm">
                                    2026-02-17 06:00:12
                                </Text>
                            </VStack>

                        </Stack>
                    </GlassPanelSection>

                </Grid>


                {/* SECTION 3 – Active Threads */}
                <GlassPanelSection
                    title="Active Worker Threads"
                    description="Processes and threads managed by the Smart Irrigation Node service"
                >
                    <Stack gap={6}>
                        {Object.entries(groupedThreads).map(([type, items]) => (
                            <Box key={type}>
                                <Text
                                    fontSize="sm"
                                    fontWeight="600"
                                    color="teal.600"
                                    mb={2}
                                >
                                    {type.toUpperCase()}
                                </Text>

                                <Grid
                                    templateColumns={{ base: "1fr", md: "1fr 1fr" }}
                                    gap={4}
                                >
                                    {items.map(thread => (
                                        <ThreadCard key={thread.name} thread={thread} />
                                    ))}
                                </Grid>

                            </Box>
                        ))}
                    </Stack>
                </GlassPanelSection>

            </Stack>
        </Box>
    )
}
