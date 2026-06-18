import { useEffect, useState } from "react"
import { Link, useParams, useNavigate, useOutletContext } from "react-router-dom"
import {
    Stack,
    Box,
    Heading,
    Text,
    SimpleGrid,
    DataList,
    Badge,
    Image,
    Flex
} from "@chakra-ui/react"
import { MemoryStick, CloudUpload } from "lucide-react"

import { fetchNodeById, deleteNode, forceDeleteNode, pushNodeConfig } from "../../../api/nodes.api"
import { fetchNodeMetadata } from "../../../api/system.api"

import PageContainer from "../../../components/layout/PageContainer"
import PageSectionStack from "../../../components/layout/PageSectionStack"
import PanelSection from "../../../components/layout/PanelSection"
import GlassPageHeader, { HeaderActions } from '../../../components/layout/GlassPageHeader'

import { HeaderAction, HeaderActionDanger, PanelButton } from '../../../components/ui/ActionButtons'
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"
import LoadingState from "../../../components/ui/LoadingState"
import ZoneCard from "../../../components/ui/cards/ZoneCard"
import {
    ControlActionDialogViewport,
    openControlActionConfirmDialog,
    openControlActionDialog,
} from "../../../components/ui/ControlActionDialogOverlay"



export default function NodeDetailPage() {
    const { nodeId } = useParams()
    const navigate = useNavigate()
    const [node, setNode] = useState(null)
    const [nodeError, setNodeError] = useState(false)
    const [isPushingConfig, setIsPushingConfig] = useState(false)
    const [isDeletingNode, setIsDeletingNode] = useState(false)
    const { isMobile, openMobileSidebar } = useOutletContext() || {}
    const [nodeMetadata, setNodeMetadata] = useState(null)

    useEffect(() => {
        fetchNodeMetadata(nodeId)
            .then((response) => {
                setNodeMetadata(response.data)
            })
            .catch((error) => {
                console.error("Failed to fetch node metadata:", error)
            })
    }, [nodeId])

    const openDialog = (payload) => {
        const id = `node-detail-action-result-${Date.now()}`
        openControlActionDialog(id, payload)
    }

    const getErrorMessage = (error, fallbackMessage) => {
        const detail = error?.response?.data?.detail
        if (typeof detail === "string") {
            return detail
        }
        if (detail?.message) {
            return detail.message
        }
        return error?.message ?? fallbackMessage
    }

    const loadNode = () => {
        setNodeError(false)
        fetchNodeById(nodeId)
            .then((response) => {
                setNode(response.data)
            })
            .catch((error) => {
                console.error("Failed to fetch node:", error)
                setNodeError(true)
            })
    }

    useEffect(() => {
        loadNode()
    }, [nodeId])

    const handlePushConfig = async () => {
        if (!node || isPushingConfig) {
            return
        }

        setIsPushingConfig(true)
        try {
            await pushNodeConfig(node.id)
            await loadNode()
            openDialog({
                title: "Configuration pushed",
                description: "Node configuration was pushed successfully.",
                status: "success",
                nodeId: node.id,
            })
        } catch (error) {
            openDialog({
                title: "Push failed",
                description: getErrorMessage(error, "Configuration push failed."),
                status: "error",
                nodeId: node.id,
            })
        } finally {
            setIsPushingConfig(false)
        }
    }

    const handleDeleteNode = async () => {
        if (!node || isDeletingNode) {
            return
        }

        const id = `node-delete-confirm-${Date.now()}`
        const deleteAction = await openControlActionConfirmDialog(id, {
            title: "Delete node",
            description: "Are you sure you want to delete this node and all its zones? This action cannot be undone.",
            status: "error",
            nodeId: node.id,
            confirmLabel: "Delete node",
            confirmMenuItems: [
                { label: "Force delete", value: "force" },
            ],
            cancelLabel: "Cancel",
        })

        if (!deleteAction) {
            return
        }

        const isForceDelete = deleteAction === "force"

        // If force delete was selected, show additional confirmation dialog with warning
        if (isForceDelete) {
            const forceConfirmId = `node-force-delete-confirm-${Date.now()}`
            const forceConfirmed = await openControlActionConfirmDialog(forceConfirmId, {
                title: "Force delete node",
                description: "Warning: Force deleting will remove the node from server configuration immediately without coordinating with the device. This may result in configuration inconsistencies on the node. Only use this if the node is offline and cannot be deleted normally.",
                status: "error",
                nodeId: node.id,
                confirmLabel: "Force delete",
                cancelLabel: "Cancel",
            })

            if (!forceConfirmed) {
                return
            }
        }

        setIsDeletingNode(true)
        try {
            if (isForceDelete) {
                await forceDeleteNode(node.id)
            } else {
                await deleteNode(node.id)
            }

            openDialog({
                title: "Node deleted",
                description: isForceDelete
                    ? "Node was force deleted from server configuration."
                    : "Node and all its zones were deleted successfully.",
                status: "success",
                nodeId: node.id,
            })

            window.setTimeout(() => {
                navigate("/configuration/nodes")
            }, 900)
        } catch (error) {
            openDialog({
                title: "Delete node failed",
                description: getErrorMessage(error, "Failed to delete node."),
                status: "error",
                nodeId: node.id,
            })
        } finally {
            setIsDeletingNode(false)
        }
    }

    const isPushed = node?.config_sync_status === "PUSHED"

    return (
        <>
            <ControlActionDialogViewport />

            <GlassPageHeader
                title={!node ? "Node" : `Node #${node.id}`}
                subtitle={!node ? undefined : (node.name || "Unnamed Node")}
                actions={
                    <HeaderActions>
                        {node && (
                            <>
                                <HeaderActionDanger
                                    onClick={handleDeleteNode}
                                    disabled={isDeletingNode || !node}
                                >
                                    {isDeletingNode ? "Deleting..." : "Delete node"}
                                </HeaderActionDanger>
                                <HeaderAction
                                    as={Link}
                                    to={`/configuration/nodes/${node.id}/edit`}
                                >
                                    Edit node
                                </HeaderAction>
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
                            </>
                        )}

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

            <PageContainer>
                {nodeError ? (
                    <PanelSection>
                        <DataUnavailableWarning
                            message="Node details are unavailable. Server may be disconnected."
                        />
                    </PanelSection>
                ) : !node ? (
                    <LoadingState
                        message="Loading node details..."
                    />
                ) : (
                    <PageSectionStack>
                        {/* Node summary with board image */}
                        <SimpleGrid
                            columns={{ base: 1, lg: 2 }}
                            gap={6}
                        >
                            <Box>
                                <PanelSection
                                    h="100%"
                                    title="Node Summary"
                                >
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
                                                    {isPushed ? "Pushed" : "Pending"}
                                                </Badge>
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                        <DataList.Item>
                                            <DataList.ItemLabel>Software version</DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                {nodeMetadata?.software_version || "Unknown"}
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                        <DataList.Item>
                                            <DataList.ItemLabel>Serial number</DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                {nodeMetadata?.serial_number || "N/A"}
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                    </DataList.Root>

                                    {/* Show PanelButton on mobile views to view header details */}
                                    {isMobile && (
                                        <Box mt={4}>
                                            <PanelButton
                                                size="sm"
                                                as={Link}
                                                to={`/configuration/nodes/${node.id}/header`}
                                                flexShrink={0}
                                                width="100%"
                                                variant="subtle"
                                                colorPalette="gray"
                                            >
                                                <MemoryStick size={14} style={{ marginRight: "6px" }} />
                                                View GPIO header configuration
                                            </PanelButton>
                                        </Box>
                                    )}
                                </PanelSection>
                            </Box>

                            <Box display={{ base: "none", lg: "block" }}>
                                <PanelSection
                                    h="100%"
                                    title="GPIO Header"
                                >
                                    <Stack
                                        justify="space-between"
                                    >
                                        <Image
                                            src="/pi_zero_2w_board.webp"
                                            alt="Raspberry Pi Zero 2W Board"
                                            maxH="160px"
                                            objectFit="contain"
                                            mx="auto"
                                        />
                                        <PanelButton
                                            size="sm"
                                            as={Link}
                                            to={`/configuration/nodes/${node.id}/header`}
                                            width="fit-content"
                                            variant="subtle"
                                            colorPalette="gray"
                                        >
                                            <MemoryStick size={14} style={{ marginRight: "6px" }} />
                                            View GPIO header configuration
                                        </PanelButton>
                                    </Stack>

                                </PanelSection>
                            </Box>
                        </SimpleGrid>

                        <SimpleGrid
                            columns={{ base: 1, md: 2 }}
                            gap={6}
                        >
                            <PanelSection title="Configuration Overview">
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
                                </DataList.Root>
                            </PanelSection>

                            {/* Software Updates section */}
                            <PanelSection
                                title="Software Updates"
                                h="100%"
                            >
                                <Stack justify="space-between" gap={6}>
                                    <DataList.Root orientation="horizontal">
                                        <DataList.Item>
                                            <DataList.ItemLabel>Status</DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                <Badge colorPalette="green">
                                                    Up to date
                                                </Badge>
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                        <DataList.Item>
                                            <DataList.ItemLabel>Current version</DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                {nodeMetadata?.software_version || "Unknown"}
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                        <DataList.Item>
                                            <DataList.ItemLabel>Latest version</DataList.ItemLabel>
                                            <DataList.ItemValue>
                                                {nodeMetadata?.software_version || "Unknown"}
                                            </DataList.ItemValue>
                                        </DataList.Item>
                                    </DataList.Root>
                                    <PanelButton
                                        size="sm"
                                        width={isMobile ? "100%" : "fit-content"}
                                        disabled
                                        variant="subtle"
                                        colorPalette="gray"
                                    >
                                        <CloudUpload size={14} style={{ marginRight: "6px" }} />
                                        Update Node Software
                                    </PanelButton>
                                </Stack>
                            </PanelSection>

                        </SimpleGrid>

                        {/* Zones */}
                        <Stack>
                            <Heading size="md" color="fg">
                                Zones
                            </Heading>

                            {/* Info text */}
                            {!nodeError && (
                                <Text fontSize="sm" color="fg.muted">
                                    {node.zones.length} configured zone{node.zones.length !== 1 && "s"}
                                </Text>
                            )}

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
                        </Stack>

                        <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                            {node.zones.map((zone) => (
                                <ZoneCard
                                    key={zone.id}
                                    nodeId={node.id}
                                    zone={zone}
                                />
                            ))}
                        </SimpleGrid>
                    </PageSectionStack>
                )}
            </PageContainer>
        </>
    )
}
