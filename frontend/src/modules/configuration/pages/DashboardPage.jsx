import { useEffect, useState } from "react"
import {
    Box,
    Text,
    Stack,
    SimpleGrid,
    Badge,
    HStack,
    DataList,
    Heading,
} from "@chakra-ui/react"
import { Link, useOutletContext } from "react-router-dom"
import { Cloud, Thermometer, Settings, MonitorCog, FileSliders, RefreshCcw, LayoutGrid, Droplets, Activity } from "lucide-react"

import { fetchNodes, pushAllPendingNodeConfigs } from "../../../api/nodes.api"
import { fetchGlobalConfig } from "../../../api/globalConfig.api"


import { FullCorrectionIndicator } from "../../../components/CorrectionIndicator"
import GlassPageHeader, { HeaderActions } from '../../../components/layout/GlassPageHeader'
import { HeaderAction, PanelButton } from '../../../components/ui/ActionButtons'
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"

import PageContainer from "../../../components/layout/PageContainer"
import PageSectionStack from "../../../components/layout/PageSectionStack"
import PanelSection from '../../../components/layout/PanelSection'
import NodeCard from "../../../components/ui/cards/NodeCard"
import {
    ControlActionDialogViewport,
    openControlActionDialog,
} from "../../../components/ui/ControlActionDialogOverlay"


export default function NodesDashboardPage() {
    const [nodes, setNodes] = useState([])
    const [nodesError, setNodesError] = useState(false)
    const [globalConfig, setGlobalConfig] = useState(null)
    const [isSyncingAll, setIsSyncingAll] = useState(false)
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    const openControlDialog = (payload) => {
        const id = `nodes-dashboard-action-result-${Date.now()}`
        openControlActionDialog(id, payload)
    }

    useEffect(() => {
        setNodesError(false)
        fetchNodes()
            .then((response) => setNodes(response.data))
            .catch((error) => {
                console.error("Error fetching nodes:", error)
                setNodesError(true)
                setNodes([])
            })

        fetchGlobalConfig()
            .then((response) => setGlobalConfig(response.data))
            .catch((error) => console.error("Error fetching global config:", error))
    }, [])

    const handleSyncAll = async () => {
        if (isSyncingAll) {
            return
        }

        setIsSyncingAll(true)
        try {
            const response = await pushAllPendingNodeConfigs()
            const result = response?.data ?? {}

            openControlDialog({
                title: "Sync completed",
                description: `Applied ${result.applied ?? 0} of ${result.pending_nodes ?? 0} pending nodes.`,
                status: "success",
                mode: result.status,
            })

            const refreshed = await fetchNodes()
            setNodes(refreshed.data)
        } catch (error) {
            const message = error?.response?.data?.detail?.message || error?.response?.data?.detail || "Failed to sync nodes."
            openControlDialog({
                title: "Sync failed",
                description: message,
                status: "error",
            })
        } finally {
            setIsSyncingAll(false)
        }
    }

    const totalZones = nodes.reduce((sum, node) => sum + (node.zones?.length ?? 0), 0)
    const pendingNodes = nodes.filter((node) => node.config_sync_status === "PENDING")
    const pushedNodes = nodes.filter((node) => node.config_sync_status === "PUSHED")
    const pendingCount = pendingNodes.length
    const pushedCount = pushedNodes.length
    const hasNodes = nodes.length > 0
    const isAllSynced = hasNodes && pendingCount === 0
    const isNoneSynced = hasNodes && pushedCount === 0
    const isSomeUnsynced = hasNodes && pendingCount > 0 && pushedCount > 0

    return (
        <>
            <ControlActionDialogViewport />

            <GlassPageHeader
                title="Configuration Dashboard"
                subtitle="Manage system configuration, nodes and their zones"
                actions={
                    <HeaderActions>
                        <HeaderAction as={Link} to="/configuration/settings">
                            Settings
                        </HeaderAction>
                        <HeaderAction as={Link} to="/configuration/nodes/discovery">
                            Add Node
                        </HeaderAction>
                    </HeaderActions>
                }
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />
            <PageContainer>
                <PageSectionStack>
                    <PanelSection>
                        <Stack gap={6}>
                            {/* Header with icon and action */}
                            <HStack justify="space-between" align="flex-start">
                                <HStack gap={4} align="flex-start" flex="1">
                                    <Box
                                        w="44px"
                                        h="44px"
                                        borderRadius="md"
                                        bg="rgba(56,178,172,0.08)"
                                        display="flex"
                                        alignItems="center"
                                        justifyContent="center"
                                        flexShrink={0}
                                    >
                                        <MonitorCog size={24} color="#319795" />
                                    </Box>
                                    <Stack spacing={1}>
                                        <Heading size="md" fontWeight="600" color="fg">
                                            System Configuration
                                        </Heading>
                                        <Text fontSize="sm" color="fg.muted">
                                            Global weather and correction settings for all nodes
                                        </Text>
                                    </Stack>
                                </HStack>
                                {!isMobile && (
                                    <PanelButton
                                        as={globalConfig ? Link : undefined}
                                        to={globalConfig ? "/configuration/settings" : undefined}
                                        size="sm"
                                        flexShrink={0}
                                        colorPalette="teal"
                                        disabled={!globalConfig}
                                    >
                                        <Settings size={16} style={{ marginRight: "6px" }} />
                                        Edit
                                    </PanelButton>
                                )}
                            </HStack>

                            {globalConfig ? (
                                <Stack gap={6}>
                                    {/* Three-column info cards */}
                                    <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
                                        {/* Standard Conditions */}
                                        <Box
                                            borderRadius="md"
                                            p={4}
                                            bg="rgba(56,178,172,0.03)"
                                            border="1px solid rgba(56,178,172,0.08)"
                                        >
                                            <HStack gap={2} mb={3}>
                                                <Box w="28px" h="28px" display="flex" alignItems="center" justifyContent="center" flexShrink={0}>
                                                    <Thermometer size={18} color="#319795" />
                                                </Box>
                                                <Text fontSize="sm" fontWeight="600" color="teal.700">
                                                    Standard Conditions
                                                </Text>
                                            </HStack>
                                            <Text fontSize="xs" color="fg.muted" mb={3}>
                                                Baseline weather values. If real weather is above or below these numbers, watering is adjusted.
                                            </Text>
                                            <DataList.Root orientation="horizontal" size="sm">
                                                <DataList.Item>
                                                    <DataList.ItemLabel fontSize="xs" color="fg.muted">
                                                        Solar Total
                                                    </DataList.ItemLabel>
                                                    <DataList.ItemValue fontSize="sm" fontWeight="500">
                                                        {globalConfig.standard_conditions.solar_total} kWh/m²/day
                                                    </DataList.ItemValue>
                                                </DataList.Item>
                                                <DataList.Item>
                                                    <DataList.ItemLabel fontSize="xs" color="fg.muted">
                                                        Rain
                                                    </DataList.ItemLabel>
                                                    <DataList.ItemValue fontSize="sm" fontWeight="500">
                                                        {globalConfig.standard_conditions.rain_mm} mm
                                                    </DataList.ItemValue>
                                                </DataList.Item>
                                                <DataList.Item>
                                                    <DataList.ItemLabel fontSize="xs" color="fg.muted">
                                                        Temperature
                                                    </DataList.ItemLabel>
                                                    <DataList.ItemValue fontSize="sm" fontWeight="500">
                                                        {globalConfig.standard_conditions.temperature_celsius} °C
                                                    </DataList.ItemValue>
                                                </DataList.Item>
                                            </DataList.Root>
                                        </Box>

                                        {/* Correction Factors */}
                                        <Box
                                            borderRadius="md"
                                            p={4}
                                            bg="rgba(56,178,172,0.03)"
                                            border="1px solid rgba(56,178,172,0.08)"
                                        >
                                            <HStack gap={2} mb={3}>
                                                <Box w="28px" h="28px" display="flex" alignItems="center" justifyContent="center" flexShrink={0}>
                                                    <FileSliders size={18} color="#319795" />
                                                </Box>
                                                <Text fontSize="sm" fontWeight="600" color="teal.700">
                                                    Correction Factors
                                                </Text>
                                            </HStack>
                                            <Text fontSize="xs" color="fg.muted" mb={3}>
                                                Strength of each weather effect. Positive means more watering, negative means less.
                                            </Text>
                                            <SimpleGrid columns={3} gap={2} w="100%">
                                                <FullCorrectionIndicator
                                                    label="Solar"
                                                    value={globalConfig.correction_factors.solar}
                                                />
                                                <FullCorrectionIndicator
                                                    label="Rain"
                                                    value={globalConfig.correction_factors.rain}
                                                />
                                                <FullCorrectionIndicator
                                                    label="Temperature"
                                                    value={globalConfig.correction_factors.temperature}
                                                />
                                            </SimpleGrid>
                                        </Box>

                                        {/* Weather API */}
                                        <Box
                                            borderRadius="md"
                                            p={4}
                                            bg="rgba(56,178,172,0.03)"
                                            border="1px solid rgba(56,178,172,0.08)"
                                        >
                                            <HStack gap={2} mb={3}>
                                                <Box w="28px" h="28px" display="flex" alignItems="center" justifyContent="center" flexShrink={0}>
                                                    <Cloud size={18} color="#319795" />
                                                </Box>
                                                <Text fontSize="sm" fontWeight="600" color="teal.700">
                                                    Weather API
                                                </Text>
                                            </HStack>
                                            <DataList.Root orientation="horizontal" size="sm">
                                                <DataList.Item>
                                                    <DataList.ItemLabel fontSize="xs" color="fg.muted">
                                                        Status
                                                    </DataList.ItemLabel>
                                                    <DataList.ItemValue fontSize="sm" fontWeight="500">
                                                        <Badge
                                                            colorPalette={globalConfig.weather_api.api_enabled ? "green" : "gray"}
                                                            size="sm"
                                                        >
                                                            {globalConfig.weather_api.api_enabled ? "Enabled" : "Disabled"}
                                                        </Badge>
                                                    </DataList.ItemValue>
                                                </DataList.Item>
                                                <DataList.Item>
                                                    <DataList.ItemLabel fontSize="xs" color="fg.muted">
                                                        Realtime
                                                    </DataList.ItemLabel>
                                                    <DataList.ItemValue fontSize="sm" fontWeight="500">
                                                        <Badge colorPalette={globalConfig.weather_api.realtime_url ? "green" : "gray"} size="sm">
                                                            {globalConfig.weather_api.realtime_url ? "Set" : "Not Set"}
                                                        </Badge>
                                                    </DataList.ItemValue>
                                                </DataList.Item>
                                                <DataList.Item>
                                                    <DataList.ItemLabel fontSize="xs" color="fg.muted">
                                                        History
                                                    </DataList.ItemLabel>
                                                    <DataList.ItemValue fontSize="sm" fontWeight="500">
                                                        <Badge colorPalette={globalConfig.weather_api.history_url ? "green" : "gray"} size="sm">
                                                            {globalConfig.weather_api.history_url ? "Set" : "Not Set"}
                                                        </Badge>
                                                    </DataList.ItemValue>
                                                </DataList.Item>
                                            </DataList.Root>
                                        </Box>
                                    </SimpleGrid>

                                    {isMobile && (
                                        <PanelButton
                                            as={Link}
                                            to="/configuration/settings"
                                            size="sm"
                                            flexShrink={0}
                                            colorPalette="teal"
                                        >
                                            <Settings size={16} style={{ marginRight: "6px" }} />
                                            Edit Configuration
                                        </PanelButton>
                                    )}
                                </Stack>
                            ) : (
                                <DataUnavailableWarning message="System configuration is currently unavailable. Server may be disconnected." />
                            )}
                        </Stack>
                    </PanelSection>

                    <PanelSection>
                        <Stack gap={6}>
                            <HStack justify="space-between" align="flex-start">
                                <HStack gap={4} align="flex-start" flex="1">
                                    <Box
                                        w="44px"
                                        h="44px"
                                        borderRadius="md"
                                        bg="rgba(56,178,172,0.08)"
                                        display="flex"
                                        alignItems="center"
                                        justifyContent="center"
                                        flexShrink={0}
                                    >
                                        <LayoutGrid size={22} color="#319795" />
                                    </Box>
                                    <Stack spacing={1}>
                                        <Heading size="md" fontWeight="600" color="fg">
                                            Nodes Configuration Overview
                                        </Heading>
                                        <Text fontSize="sm" color="fg.muted">
                                            Aggregate status across all nodes and zones
                                        </Text>
                                    </Stack>
                                </HStack>
                                {!isMobile && (
                                    <PanelButton
                                        size="sm"
                                        colorPalette="teal"
                                        flexShrink={0}
                                        onClick={handleSyncAll}
                                        loading={isSyncingAll}
                                        disabled={pendingCount === 0 || isSyncingAll || !hasNodes || !globalConfig}
                                    >
                                        <RefreshCcw size={14} style={{ marginRight: "6px" }} />
                                        Sync all nodes
                                    </PanelButton>
                                )}
                            </HStack>

                            {globalConfig ? (
                                <Stack gap={6}>
                                    <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
                                        <Box
                                            borderRadius="md"
                                            p={4}
                                            bg="rgba(56,178,172,0.03)"
                                            border="1px solid rgba(56,178,172,0.08)"
                                        >
                                            <HStack gap={2} mb={2}>
                                                <Box w="28px" h="28px" display="flex" alignItems="center" justifyContent="center" flexShrink={0}>
                                                    <Activity size={18} color="#319795" />
                                                </Box>
                                                <Text fontSize="sm" fontWeight="600" color="teal.700">
                                                    Sync Status
                                                </Text>
                                            </HStack>
                                            <Stack gap={1}>
                                                <Text fontSize="xs" color="fg.muted">
                                                    {pendingCount} pending, {pushedCount} synced
                                                </Text>
                                                <HStack gap={2} flexWrap="wrap">
                                                    <Badge colorPalette={isAllSynced ? "green" : "gray"} size="sm">
                                                        All synced
                                                    </Badge>
                                                    <Badge colorPalette={isSomeUnsynced ? "orange" : "gray"} size="sm">
                                                        Some pending
                                                    </Badge>
                                                    <Badge colorPalette={isNoneSynced ? "orange" : "gray"} size="sm">
                                                        None synced
                                                    </Badge>
                                                </HStack>
                                            </Stack>
                                        </Box>

                                        <Box
                                            borderRadius="md"
                                            p={4}
                                            bg="rgba(56,178,172,0.03)"
                                            border="1px solid rgba(56,178,172,0.08)"
                                        >
                                            <HStack gap={2} mb={2}>
                                                <Box w="28px" h="28px" display="flex" alignItems="center" justifyContent="center" flexShrink={0}>
                                                    <Droplets size={18} color="#319795" />
                                                </Box>
                                                <Text fontSize="sm" fontWeight="600" color="teal.700">
                                                    Zones Configured
                                                </Text>
                                            </HStack>
                                            <Text fontSize="xs" color="fg.muted">
                                                Total zones across all nodes
                                            </Text>
                                            <Text fontSize="lg" fontWeight="600" color="fg">
                                                {totalZones}
                                            </Text>
                                        </Box>

                                        <Box
                                            borderRadius="md"
                                            p={4}
                                            bg={pendingCount > 0 ? "rgba(245,158,11,0.08)" : "rgba(56,178,172,0.03)"}
                                            border={pendingCount > 0 ? "1px solid rgba(245,158,11,0.16)" : "1px solid rgba(56,178,172,0.08)"}
                                        >
                                            <HStack gap={2} mb={2}>
                                                <Box w="28px" h="28px" display="flex" alignItems="center" justifyContent="center" flexShrink={0}>
                                                    <RefreshCcw size={18} color={pendingCount > 0 ? "#d97706" : "#319795"} />
                                                </Box>
                                                <Text fontSize="sm" fontWeight="600" color={pendingCount > 0 ? "orange.700" : "teal.700"}>
                                                    Pending Sync
                                                </Text>
                                            </HStack>
                                            <Text fontSize="xs" color="fg.muted">
                                                Nodes needing config push
                                            </Text>
                                            <Text fontSize="lg" fontWeight="600" color="fg">
                                                {pendingCount}
                                            </Text>
                                        </Box>
                                    </SimpleGrid>

                                    {isMobile && (
                                        <PanelButton
                                            size="sm"
                                            colorPalette="teal"
                                            flexShrink={0}
                                            onClick={handleSyncAll}
                                            loading={isSyncingAll}
                                            disabled={pendingCount === 0 || isSyncingAll || !hasNodes}
                                        >
                                            <RefreshCcw size={14} style={{ marginRight: "6px" }} />
                                            Sync all nodes
                                        </PanelButton>
                                    )}
                                </Stack>
                            ) : (
                                <DataUnavailableWarning message="Node data is currently unavailable. Server may be disconnected." />
                            )}
                        </Stack>
                    </PanelSection>

                    {/* Info text */}
                    {globalConfig && (
                        <Text mt={6} mb={2} fontSize="sm" color="fg.muted">
                            {nodes.length} configured node{nodes.length !== 1 && "s"}
                        </Text>
                    )}

                    {/* Empty state */}
                    {nodes.length === 0 && !nodesError && (
                        <Box
                            bg="bg.subtle"
                            borderWidth="1px"
                            borderColor="border.subtle"
                            borderRadius="md"
                            p={6}
                        >
                            <Text color="fg.muted">
                                No nodes found. Create your first node to get started.
                            </Text>
                        </Box>
                    )
                    }

                    {/* Nodes grid */}
                    <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
                        {nodes.map((node) => (
                            <NodeCard
                                key={node.id}
                                node={node}
                            />
                        ))}
                    </SimpleGrid>
                </PageSectionStack>
            </PageContainer>
        </>
    )
}
