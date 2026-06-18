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
import { useEffect, useState } from "react"

import { getNodesSnapshot } from "../api/live.api"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import PageContainer from "../../../components/layout/PageContainer"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"

import LoadingState from "../../../components/ui/LoadingState"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"

import RuntimeNodeCard from "../components/RuntimeNodeCard"
import InfrastructureOverviewCard from "../components/InfrastructureOverviewCard"
import NetworkHealthSection from "../components/NetworkHealthSection"

export default function RuntimeNodesPage() {

    const navigate = useNavigate()

    const [nodes, setNodes] = useState([])
    const [nodesError, setNodesError] = useState(false)
    const [nodesLoading, setNodesLoading] = useState(true)

    useEffect(() => {
        let mounted = true
        async function load() {
            try {
                const data = await getNodesSnapshot()
                if (!mounted) return
                setNodes((data || []).map(n => ({
                    id: String(n.id),
                    name: n.name || `Node ${n.id}`,
                    online: !!n.online,
                    connection: "unknown",
                    signal: null,
                    zonesCount: n.total_zones || 0,
                    controllerStatus: n.online ? "running" : "offline",
                    warnings: 0,
                    errors: 0,
                    lastSeen: n.last_seen_at || null,
                })))
            } catch (e) {
                setNodesError(true)
            } finally {
                setNodesLoading(false)
            }
        }

        load()
        const iv = setInterval(load, 2500)
        return () => {
            mounted = false
            clearInterval(iv)
        }
    }, [])

    const onlineCount = nodes.filter(n => n.online).length
    const offlineCount = nodes.filter(n => !n.online).length
    const errorCount = 0
    const weakSignalCount = 0

    const lastHeartbeat = (() => {
        if (!nodes || nodes.length === 0) return "-"
        const dates = nodes
            .map(n => n.lastSeen)
            .filter(Boolean)
            .map(d => new Date(d).getTime())
        if (dates.length === 0) return "-"
        const latest = Math.max(...dates)
        return new Date(latest).toLocaleString()
    })()

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
        <>
            <GlassPageHeader
                title="Monitoring"
                subtitle="Live system and nodes status"
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <PageContainer>
                {nodesError ? (
                    <GlassPanelSection>
                        <DataUnavailableWarning message="Monitoring data is unavailable. Server may be disconnected." />
                    </GlassPanelSection>
                ) : nodesLoading ? (
                    <LoadingState
                        message="Loading monitoring data..."
                    />
                ) : (

                    <DashboardPageSectionStack>
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
                                    /* onClick={() => navigate(`/runtime/nodes/${node.id}`)} */
                                    />
                                ))}
                            </Grid>
                        </GlassPanelSection>

                        {/* <NetworkHealthSection data={networkHealthData} /> */}
                    </DashboardPageSectionStack>
                )}
            </PageContainer>

        </>
    )
}
