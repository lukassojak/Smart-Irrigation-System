import { useEffect, useState } from "react"
import { Link, useParams, useNavigate, useOutletContext } from "react-router-dom"
import {
    Stack,
    Box,
    Heading,
    Text,
    SimpleGrid,
    DataList,
    Badge
} from "@chakra-ui/react"

import { fetchNodeById, deleteNode, pushNodeConfig } from "../../../api/nodes.api"

import { LimitedCorrectionIndicator } from "../../../components/CorrectionIndicator"
import PanelSection from "../../../components/layout/PanelSection"
import GlassPageHeader, { HeaderActions } from '../../../components/layout/GlassPageHeader'
import { HeaderAction, HeaderActionDanger } from '../../../components/ui/ActionButtons'
import ZoneCard from "../../../components/ui/cards/ZoneCard"



export default function NodeDetailPage() {
    const { nodeId } = useParams()
    const navigate = useNavigate()
    const [node, setNode] = useState(null)
    const [isPushingConfig, setIsPushingConfig] = useState(false)
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    const loadNode = () => {
        fetchNodeById(nodeId)
            .then((response) => setNode(response.data))
            .catch((error) => console.error("Failed to fetch node:", error))
    }

    useEffect(() => {
        loadNode()
    }, [nodeId])

    const handlePushConfig = async () => {
        setIsPushingConfig(true)
        try {
            await pushNodeConfig(node.id)
            await loadNode()
            alert("Configuration was pushed successfully.")
        } catch (error) {
            const detail = error?.response?.data?.detail
            if (typeof detail === "string") {
                alert(detail)
            } else if (detail?.message) {
                alert(detail.message)
            } else {
                alert("Configuration push failed.")
            }
        } finally {
            setIsPushingConfig(false)
        }
    }

    const isPushed = node?.config_sync_status === "PUSHED"

    if (!node) {
        return (
            <Box p={6}>
                <Text color="fg.muted">Loading node…</Text>
            </Box>
        )
    }

    return (
        <>
            <GlassPageHeader
                title={`Node #${node.id}`}
                subtitle={node.name || "Unnamed Node"}
                actions={
                    <HeaderActions>
                        <HeaderActionDanger
                            onClick={() => {
                                if (!confirm("Are you sure you want to delete this node and all its zones?")) return
                                deleteNode(node.id)
                                    .then(() => navigate("/configuration/nodes"))
                                    .catch(() => alert("Failed to delete node"))
                            }}
                        >
                            Delete node
                        </HeaderActionDanger>
                        <HeaderAction
                            as={Link}
                            to={`/configuration/nodes/${node.id}/zones/new`}
                        >
                            Create new zone
                        </HeaderAction>
                        <HeaderAction
                            onClick={handlePushConfig}
                            disabled={isPushingConfig}
                        >
                            {isPushingConfig ? "Pushing..." : "Push config"}
                        </HeaderAction>
                        <HeaderAction
                            as={Link}
                            to="/configuration/nodes"
                        >
                            &larr; Back
                        </HeaderAction>
                    </HeaderActions>
                }
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />
            <Box p={6}>
                <Stack gap={10} mb={6}>
                    {/* Node summary */}
                    <PanelSection title="Node Summary">
                        <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                            <DataList.Root orientation="horizontal">
                                <DataList.Item>
                                    <DataList.ItemLabel>Node ID</DataList.ItemLabel>
                                    <DataList.ItemValue>{node.id}</DataList.ItemValue>
                                </DataList.Item>
                                <DataList.Item>
                                    <DataList.ItemLabel>Location</DataList.ItemLabel>
                                    <DataList.ItemValue>{node.location || "N/A"}</DataList.ItemValue>
                                </DataList.Item>
                                <DataList.Item>
                                    <DataList.ItemLabel>Last updated</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        {node.last_updated ? new Date(node.last_updated).toLocaleString() : "N/A"}
                                    </DataList.ItemValue>
                                </DataList.Item>
                                <DataList.Item>
                                    <DataList.ItemLabel>Config sync</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        <Badge colorPalette={isPushed ? "green" : "orange"}>
                                            {isPushed ? "PUSHED" : "PENDING"}
                                        </Badge>
                                    </DataList.ItemValue>
                                </DataList.Item>
                            </DataList.Root>
                        </SimpleGrid>
                    </PanelSection>

                    <PanelSection title="Configuration Overview">
                        <SimpleGrid columns={{ base: 1, md: 2 }} gap={3}>
                            <DataList.Root orientation="horizontal">
                                <DataList.Item>
                                    <DataList.ItemLabel>Automation</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        {/* Use badge colors for enabled/disabled */}
                                        {node.automation.enabled ? (
                                            <Badge colorPalette="green">Enabled</Badge>
                                        ) : (
                                            <Badge colorPalette="red">Disabled</Badge>
                                        )}
                                    </DataList.ItemValue>
                                </DataList.Item>
                                <DataList.Item>
                                    <DataList.ItemLabel>Scheduled Time</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        {node.automation.enabled
                                            ? `${String(node.automation.scheduled_hour).padStart(2, '0')}:${String(node.automation.scheduled_minute).padStart(2, '0')}`
                                            : "N/A"}
                                    </DataList.ItemValue>
                                </DataList.Item>
                                <DataList.Item>
                                    <DataList.ItemLabel>Batch Strategy</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        {node.batch_strategy.concurrent_irrigation
                                            ? "Concurrent irrigation"
                                            : "Sequential irrigation"}
                                    </DataList.ItemValue>
                                </DataList.Item>
                                <DataList.Item>
                                    <DataList.ItemLabel>Flow Control</DataList.ItemLabel>
                                    <DataList.ItemValue>
                                        {node.batch_strategy.flow_control ? "Enabled" : "Disabled"}
                                    </DataList.ItemValue>
                                </DataList.Item>
                                {/*
                        <DataList.Item>
                            <DataList.ItemLabel>Input Pins</DataList.ItemLabel>
                            <DataList.ItemValue>{node.hardware.input_pins.length}</DataList.ItemValue>
                        </DataList.Item>
                        <DataList.Item>
                            <DataList.ItemLabel>Output Pins</DataList.ItemLabel>
                            <DataList.ItemValue>{node.hardware.output_pins.length}</DataList.ItemValue>
                        </DataList.Item>
                        */}
                            </DataList.Root>
                        </SimpleGrid>
                    </PanelSection>
                </Stack>

                {/* Zones */}
                <Box>
                    <Heading size="md" mb={4} color="fg">
                        Zones
                    </Heading>

                    {/* Info text */}
                    <Text mb={4} fontSize="sm" color="fg.muted">
                        {node.zones.length} configured zone{node.zones.length !== 1 && "s"}
                    </Text>

                    {node.zones.length === 0 && (
                        <Box
                            bg="bg.subtle"
                            borderWidth="1px"
                            borderColor="border.subtle"
                            borderRadius="md"
                            p={4}
                        >
                            <Text color="fg.muted">
                                Node has no zones defined.
                            </Text>
                        </Box>
                    )}

                    <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                        {node.zones.map((zone) => (
                            <ZoneCard
                                key={zone.id}
                                nodeId={node.id}
                                zone={zone}
                            />
                        ))}
                    </SimpleGrid>
                </Box>
            </Box>
        </>
    )
}
