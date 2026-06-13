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
import { useEffect, useState } from "react"
import { getNodeDetail } from "../api/live.api"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import ThreadCard from "../components/ThreadCard"
import ResourceMetric from "../components/ResourceMetric"

export default function RuntimeNodeDetailPage() {

    const { nodeId } = useParams()
    const [node, setNode] = useState(null)
    const [zones, setZones] = useState([])

    useEffect(() => {
        let mounted = true
        async function load() {
            try {
                const nid = Number(nodeId)
                const data = await getNodeDetail(nid)
                if (!mounted) return

                const n = data?.node
                setNode(n ? {
                    id: String(n.id),
                    name: n.name || `Node ${n.id}`,
                    hardware: null,
                    online: !!n.online,
                    ip: null,
                    connection: "unknown",
                    signal: null,
                    uptime: null,
                    cpu: null,
                    memory: null,
                    serviceStatus: n.online ? "running" : "stopped",
                    controllerStatus: n.online ? "running" : "offline"
                } : null)

                const nodeZones = (data?.zones || []).map(z => ({
                    name: z.name,
                    alive: !!z.online,
                    startedAt: z.last_run ? new Date(z.last_run).toLocaleString() : "-",
                    runtime: z.progress_percent != null ? `${z.progress_percent}%` : "-"
                }))
                setZones(nodeZones)
            } catch (e) {
                // ignore
            }
        }

        load()
        const iv = setInterval(load, 2500)
        return () => {
            mounted = false
            clearInterval(iv)
        }
    }, [nodeId])

    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    return (
        <Box>

            <GlassPageHeader
                title={node ? node.name : `Node ${nodeId}`}
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
                                    <Text fontWeight="600">{node ? node.hardware || "-" : "-"}</Text>
                                </HStack>
                                <HStack>
                                    <Network size={14} color="#319795" />
                                    <Text fontSize="sm" color="gray.600">
                                        IP: {node ? node.ip || "-" : "-"}
                                    </Text>
                                </HStack>

                                <HStack>
                                    <ArrowUpFromDot size={14} color="#319795" />
                                    <Text fontSize="sm" color="gray.600">
                                        Uptime: {node ? node.uptime || "-" : "-"}
                                    </Text>
                                </HStack>

                                <HStack>
                                    <Wifi size={14} color="#319795" />
                                    <Text fontSize="sm" color="gray.600">
                                        {node ? node.connection : "-"} {node && node.signal !== null ? `(${node.signal} dBm)` : ""}
                                    </Text>
                                </HStack>
                            </VStack>

                            <Stack gap={5}>
                                <ResourceMetric
                                    label="CPU Usage"
                                    value={node ? node.cpu : null}
                                    color="teal.500"
                                />
                                <ResourceMetric
                                    label="Memory Usage"
                                    value={node ? node.memory : null}
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
                                        node?.serviceStatus === "running"
                                            ? "green"
                                            : "red"
                                    }
                                    variant="subtle"
                                >
                                    {node?.serviceStatus ?? "-"}
                                </Badge>
                            </HStack>

                            <HStack justify="space-between">
                                <VStack align="start" gap={1}>
                                    <Text fontSize="sm" color="gray.600">
                                        Controller Status
                                    </Text>
                                    <Text fontWeight="600">
                                        {node?.controllerStatus ?? "-"}
                                    </Text>
                                </VStack>

                                <Badge
                                    size="sm"
                                    colorPalette={
                                        node?.controllerStatus === "running"
                                            ? "green"
                                            : "gray"
                                    }
                                    variant="subtle"
                                >
                                    {node?.controllerStatus ?? "-"}
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
                    title="Zones"
                    description="Zones assigned to this node"
                >
                    <Stack gap={6}>
                        <Grid
                            templateColumns={{ base: "1fr", md: "1fr 1fr" }}
                            gap={4}
                        >
                            {zones.map((z, idx) => (
                                <ThreadCard key={`${z.name}-${idx}`} thread={z} />
                            ))}
                        </Grid>
                    </Stack>
                </GlassPanelSection>

            </Stack>
        </Box>
    )
}
