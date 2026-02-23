import {
    Box,
    Grid,
    Stack,
    Text,
    Badge,
    HStack
} from "@chakra-ui/react"

import {
    Server,
    Wifi,
    Signal,
    EthernetPort,
    Activity,
    AlertTriangle
} from "lucide-react"

import { useNavigate } from "react-router-dom"
import { useOutletContext } from "react-router-dom"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import RuntimeNodeCard from "../components/RuntimeNodeCard"
import InfrastructureOverviewCard from "../components/InfrastructureOverviewCard"
import NetworkHealthSection from "../components/NetworkHealthSection"

export default function RuntimeNodesPage() {

    const navigate = useNavigate()

    // --- Fake Runtime Data ---
    const nodes = [
        {
            id: "node-1",
            name: "Garden Main Controller",
            online: true,
            connection: "wifi", // wifi | ethernet
            signal: -55, // dBm
            zonesCount: 6,
            controllerStatus: "running", // running | idle | error
            warnings: 0,
            errors: 0
        },
        {
            id: "node-2",
            name: "Greenhouse Node",
            online: true,
            connection: "ethernet",
            signal: null,
            zonesCount: 4,
            controllerStatus: "running",
            warnings: 1,
            errors: 0
        },
        {
            id: "node-3",
            name: "Orchard Node",
            online: false,
            connection: "wifi",
            signal: -82,
            zonesCount: 5,
            controllerStatus: "offline",
            warnings: 0,
            errors: 1
        }
    ]

    const onlineCount = nodes.filter(n => n.online).length
    const offlineCount = nodes.filter(n => !n.online).length
    const errorCount = nodes.filter(n => n.errors > 0).length
    const weakSignalCount = nodes.filter(
        n => n.connection === "wifi" && n.signal !== null && n.signal < -75
    ).length

    const lastHeartbeat = "12 seconds ago"

    const networkHealthData = {
        broker: {
            online: true,
            uptime: "5 days 14h",
            connectedNodes: 5,
            totalNodes: 6,
            msgPerSec: 32
        },
        latency: {
            avg: 42,
            max: 87
        },
        signal: {
            strong: 3,
            medium: 1,
            weak: 1,
            total: 5
        }
    }

    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    return (
        <Box>

            <GlassPageHeader
                title="Runtime Nodes"
                subtitle="Live status of irrigation nodes"
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <Stack
                gap={8}
                px={{ base: 4, md: 8 }}
                py={8}
            >
                {/* SECTION – Infrastructure Overview */}
                {/* SECTION – Infrastructure Overview */}
                <GlassPanelSection
                    title="Infrastructure Overview"
                    description="Fleet-level health and connectivity status"
                >
                    <Grid
                        templateColumns={{
                            base: "1fr",
                            md: "1fr 1fr",
                            xl: "1fr 1fr 1fr 1fr"
                        }}
                        gap={6}
                    >
                        <InfrastructureOverviewCard
                            icon={Server}
                            title="Nodes Online"
                            value={`${onlineCount} / ${nodes.length}`}
                            description={`${offlineCount} offline`}
                            accentColor="green.500"
                        />

                        <InfrastructureOverviewCard
                            icon={AlertTriangle}
                            title="Nodes with Errors"
                            value={errorCount}
                            description="Require attention"
                            accentColor="red.500"
                        />

                        <InfrastructureOverviewCard
                            icon={Wifi}
                            title="Weak Signal"
                            value={weakSignalCount}
                            description="WiFi nodes below -75 dBm"
                            accentColor="orange.500"
                        />

                        <InfrastructureOverviewCard
                            icon={Signal}
                            title="Last Heartbeat"
                            value={lastHeartbeat}
                            description="Most recent node activity"
                            accentColor="teal.500"
                        />
                    </Grid>
                </GlassPanelSection>

                <GlassPanelSection
                    title="Nodes Overview"
                    description={`${onlineCount} / ${nodes.length} nodes online`}
                >
                    <Grid
                        templateColumns={{
                            base: "1fr",
                            md: "1fr 1fr",
                            xl: "1fr 1fr 1fr"
                        }}
                        gap={6}
                    >
                        {nodes.map(node => (
                            <RuntimeNodeCard
                                key={node.id}
                                node={node}
                                onClick={() => navigate(`/runtime/nodes/${node.id}`)}
                            />
                        ))}
                    </Grid>
                </GlassPanelSection>

                <NetworkHealthSection data={networkHealthData} />

            </Stack>

        </Box>
    )
}
