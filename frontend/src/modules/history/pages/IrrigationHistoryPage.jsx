import {
    Box,
    Badge,
    Button,
    Grid,
    Stack,
    NativeSelect,
    HStack,
    Text,
    Spinner,
    Checkbox,
} from "@chakra-ui/react"
import { useEffect, useMemo, useState } from "react"
import { useOutletContext } from "react-router-dom"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import PageContainer from "../../../components/layout/PageContainer"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"
import HistoryRecordsTable from "../components/HistoryRecordsTable"
import HistoryStats from "../components/HistoryStats"

import LoadingState from "../../../components/ui/LoadingState"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"
import { HeaderActionDanger, PanelButton } from "../../../components/ui/ActionButtons"
import {
    ControlActionDialogViewport,
    openControlActionConfirmDialog,
    openControlActionDialog,
} from "../../../components/ui/ControlActionDialogOverlay"

import { fetchNodes } from "../../../api/nodes.api"
import { fetchAllHistoryRecords, fetchNodeHistory } from "../../../api/history.api"
import { deleteAllHistory } from "../../../api/history.api"

const SORT_OPTIONS = [
    { value: "start_time_desc", label: "Newest first" },
    { value: "start_time_asc", label: "Oldest first" },
    { value: "node_asc", label: "Node A → Z" },
    { value: "node_desc", label: "Node Z → A" },
    { value: "zone_asc", label: "Zone 1 → 9" },
    { value: "zone_desc", label: "Zone 9 → 1" },
    { value: "outcome_asc", label: "Outcome A → Z" },
    { value: "outcome_desc", label: "Outcome Z → A" },
]

const OUTCOME_OPTIONS = [
    { value: "all", label: "All outcomes" },
    { value: "success", label: "Success" },
    { value: "failed", label: "Failed" },
    { value: "stopped", label: "Stopped" },
    { value: "interrupted", label: "Interrupted" },
    { value: "skipped", label: "Skipped" },
]

function normalizeText(value) {
    return String(value ?? "").toLowerCase()
}

function compareStrings(left, right) {
    return normalizeText(left).localeCompare(normalizeText(right), "cs", {
        sensitivity: "base",
    })
}

function compareNumbers(left, right) {
    return Number(left ?? 0) - Number(right ?? 0)
}

function compareTimestamps(left, right) {
    return new Date(left ?? 0).getTime() - new Date(right ?? 0).getTime()
}

function getOutcomeRank(outcome) {
    switch (outcome) {
        case "success":
            return 0
        case "failed":
            return 1
        case "stopped":
            return 2
        case "interrupted":
            return 3
        case "skipped":
            return 4
        default:
            return 5
    }
}

export default function IrrigationHistoryPage() {
    const outlet = useOutletContext()

    const [nodes, setNodes] = useState([])
    const [selectedNodeId, setSelectedNodeId] = useState("all")
    const [selectedOutcome, setSelectedOutcome] = useState("all")
    const [sortBy, setSortBy] = useState("start_time_desc")
    const [historyRecords, setHistoryRecords] = useState([])
    const [includeDeleted, setIncludeDeleted] = useState(true)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [recordLimit, setRecordLimit] = useState(30)

    const openDialog = (payload) => {
        const id = `history-action-result-${Date.now()}`
        openControlActionDialog(id, payload)
    }

    const getErrorMessage = (err, fallbackMessage) => {
        const detail = err?.response?.data?.detail
        if (typeof detail === "string") {
            return detail
        }
        if (detail?.message) {
            return detail.message
        }
        return err?.message ?? fallbackMessage
    }

    const handleDeleteAllRecords = async () => {
        const id = `history-delete-confirm-${Date.now()}`
        const confirmed = await openControlActionConfirmDialog(id, {
            title: "Delete irrigation history",
            description: "Delete all irrigation history records? This action cannot be undone.",
            status: "error",
            confirmLabel: "Delete all",
            cancelLabel: "Cancel",
        })

        if (!confirmed) {
            return
        }

        try {
            await deleteAllHistory()
            await loadHistory()
            openDialog({
                title: "History deleted",
                description: "All irrigation history records were deleted.",
                status: "success",
            })
        } catch (err) {
            openDialog({
                title: "Delete failed",
                description: getErrorMessage(err, "Failed to delete history records."),
                status: "error",
            })
        }
    }

    const nodeLabelById = useMemo(
        () => Object.fromEntries(nodes.map((node) => [String(node.id), node.name ?? `Node ${node.id}`])),
        [nodes],
    )

    // Load available nodes
    useEffect(() => {
        const loadNodes = async () => {
            try {
                const response = await fetchNodes()
                setNodes(response.data || [])
            } catch (err) {
                setError(`Failed to load nodes: ${err.message}`)
            }
        }
        loadNodes()
    }, [])

    // Load history records when node selection changes (exposed as function so we can
    // reload after deleting all records)
    const loadHistory = async () => {
        setLoading(true)
        setError(null)
        try {
            const response = selectedNodeId === "all"
                ? await fetchAllHistoryRecords(recordLimit)
                : await fetchNodeHistory(selectedNodeId, recordLimit)
            setHistoryRecords(response.data.records || [])
        } catch (err) {
            setError(`Failed to load history: ${err.message}`)
            setHistoryRecords([])
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        loadHistory()
    }, [selectedNodeId, recordLimit])

    const visibleRecords = useMemo(() => {
        const filteredRecords = historyRecords.filter((record) => {
            if (selectedOutcome !== "all" && record.outcome !== selectedOutcome) {
                return false
            }
            if (!includeDeleted && record.zone_deleted) {
                return false
            }
            return true
        })

        const sortedRecords = [...filteredRecords]

        sortedRecords.sort((left, right) => {
            switch (sortBy) {
                case "start_time_asc":
                    return compareTimestamps(left.start_time, right.start_time)
                case "node_asc":
                    return compareStrings(
                        nodeLabelById[String(left.node_id)] ?? left.node_id,
                        nodeLabelById[String(right.node_id)] ?? right.node_id,
                    ) || compareTimestamps(right.start_time, left.start_time)
                case "node_desc":
                    return compareStrings(
                        nodeLabelById[String(right.node_id)] ?? right.node_id,
                        nodeLabelById[String(left.node_id)] ?? left.node_id,
                    ) || compareTimestamps(right.start_time, left.start_time)
                case "zone_asc":
                    return compareNumbers(left.circuit_id, right.circuit_id) || compareTimestamps(right.start_time, left.start_time)
                case "zone_desc":
                    return compareNumbers(right.circuit_id, left.circuit_id) || compareTimestamps(right.start_time, left.start_time)
                case "outcome_asc":
                    return getOutcomeRank(left.outcome) - getOutcomeRank(right.outcome) || compareTimestamps(right.start_time, left.start_time)
                case "outcome_desc":
                    return getOutcomeRank(right.outcome) - getOutcomeRank(left.outcome) || compareTimestamps(right.start_time, left.start_time)
                case "start_time_desc":
                default:
                    return compareTimestamps(right.start_time, left.start_time)
            }
        })

        return sortedRecords
    }, [historyRecords, nodeLabelById, selectedOutcome, sortBy, includeDeleted])

    const selectedNode = selectedNodeId !== "all"
        ? nodes.find((node) => String(node.id) === String(selectedNodeId))
        : null

    const visibleNodeCount = new Set(visibleRecords.map((record) => String(record.node_id))).size
    const visibleZoneCount = new Set(visibleRecords.map((record) => `${record.node_id}:${record.circuit_id}`)).size

    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    return (
        <>
            <ControlActionDialogViewport />

            <GlassPageHeader
                title="Irrigation History"
                subtitle="Search irrigation cycles and it's outcomes across nodes"
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
                actions={(
                    <>
                        {!error && (
                            <HeaderActionDanger
                                onClick={handleDeleteAllRecords}
                            >
                                Delete all records
                            </HeaderActionDanger>
                        )}
                    </>
                )}
            />
            <PageContainer>
                {error ? (
                    <GlassPanelSection>
                        <DataUnavailableWarning
                            message="History data is unavailable. Server may be disconnected."
                            error={error}
                        />
                    </GlassPanelSection>
                ) : (

                    <DashboardPageSectionStack>
                        <GlassPanelSection title="Filters & Sorting">
                            <Stack gap={6}>
                                <Grid templateColumns={{ base: "1fr", lg: "repeat(3, minmax(0, 1fr))" }} gap={4}>
                                    <Box>
                                        <Text mb={2} fontSize="sm" fontWeight="600" color="gray.700">
                                            Node scope
                                        </Text>
                                        <NativeSelect.Root>
                                            <NativeSelect.Field
                                                value={selectedNodeId}
                                                onChange={(event) => setSelectedNodeId(event.target.value)}
                                                bg="rgba(255, 255, 255, 0.55)"
                                                border="1px solid rgba(56,178,172,0.16)"
                                            >
                                                <option value="all">All nodes</option>
                                                {nodes.map((node) => (
                                                    <option key={node.id} value={String(node.id)}>
                                                        Node #{node.id} {node.name ? `- ${node.name}` : ""}
                                                    </option>
                                                ))}
                                            </NativeSelect.Field>
                                            <NativeSelect.Indicator />
                                        </NativeSelect.Root>
                                    </Box>

                                    <Box>
                                        <Text mb={2} fontSize="sm" fontWeight="600" color="gray.700">
                                            Outcome filter
                                        </Text>
                                        <NativeSelect.Root>
                                            <NativeSelect.Field
                                                value={selectedOutcome}
                                                onChange={(event) => setSelectedOutcome(event.target.value)}
                                                bg="rgba(255, 255, 255, 0.55)"
                                                border="1px solid rgba(56,178,172,0.16)"
                                            >
                                                {OUTCOME_OPTIONS.map((option) => (
                                                    <option key={option.value} value={option.value}>
                                                        {option.label}
                                                    </option>
                                                ))}
                                            </NativeSelect.Field>
                                            <NativeSelect.Indicator />
                                        </NativeSelect.Root>
                                    </Box>

                                    <Box>
                                        <Text mb={2} fontSize="sm" fontWeight="600" color="gray.700">
                                            Sort order
                                        </Text>
                                        <NativeSelect.Root>
                                            <NativeSelect.Field
                                                value={sortBy}
                                                onChange={(event) => setSortBy(event.target.value)}
                                                bg="rgba(255, 255, 255, 0.55)"
                                                border="1px solid rgba(56,178,172,0.16)"
                                            >
                                                {SORT_OPTIONS.map((option) => (
                                                    <option key={option.value} value={option.value}>
                                                        {option.label}
                                                    </option>
                                                ))}
                                            </NativeSelect.Field>
                                            <NativeSelect.Indicator />
                                        </NativeSelect.Root>
                                    </Box>
                                </Grid>

                                <Checkbox.Root
                                    colorPalette="teal"
                                    checked={includeDeleted}
                                    onCheckedChange={(event) => setIncludeDeleted(Boolean(event.checked))}
                                    mb={2}
                                >
                                    <Checkbox.HiddenInput />
                                    <Checkbox.Control />
                                    <Checkbox.Label>Include deleted zones</Checkbox.Label>
                                </Checkbox.Root>

                                <HStack justify="space-between" flexWrap="wrap" gap={3}>
                                    <Stack direction={{ base: "column", md: "row" }} gap={2} align="center">
                                        <HStack spacing={2} flexWrap="wrap">
                                            <Text fontSize="sm" color="gray.600">
                                                Displaying
                                            </Text>
                                            <Badge colorPalette="gray" variant="subtle">
                                                {visibleRecords.length} records
                                            </Badge>
                                        </HStack>
                                        <HStack spacing={2} flexWrap="wrap">
                                            <Text fontSize="sm" color="gray.600">
                                                across
                                            </Text>
                                            <Badge colorPalette="gray" variant="subtle">
                                                {visibleZoneCount} zones
                                            </Badge>
                                            <Text fontSize="sm" color="gray.600">
                                                and
                                            </Text>
                                            <Badge colorPalette="gray" variant="subtle">
                                                {visibleNodeCount} nodes
                                            </Badge>
                                        </HStack>
                                    </Stack>

                                    <Button
                                        size="sm"
                                        variant="outline"
                                        borderColor="rgba(56,178,172,0.18)"
                                        onClick={() => {
                                            setSelectedNodeId("all")
                                            setSelectedOutcome("all")
                                            setSortBy("start_time_desc")
                                            setIncludeDeleted(true)
                                        }}
                                    >
                                        Reset view
                                    </Button>
                                </HStack>
                            </Stack>
                        </GlassPanelSection>

                        {selectedNode && !loading && (
                            <Box px={1}>
                                <Text fontSize="sm" color="gray.600">
                                    Currently scoped to node <strong>{selectedNode.name}</strong>.
                                </Text>
                            </Box>
                        )}

                        <GlassPanelSection title="Summary">
                            <HistoryStats records={visibleRecords} />
                        </GlassPanelSection>

                        <GlassPanelSection title="Irrigation Records">
                            {loading && (
                                <LoadingState
                                    message="Loading irrigation history data..."
                                />
                            )}
                            {!loading && visibleRecords.length === 0 && (
                                <Box
                                    py={12}
                                    px={6}
                                    borderRadius="xl"
                                    bg="rgba(255,255,255,0.45)"
                                    border="1px dashed rgba(56,178,172,0.22)"
                                    textAlign="center"
                                >
                                    <Text fontWeight="600" color="gray.700" mb={2}>
                                        No irrigation records match the current filters
                                    </Text>
                                    <Text fontSize="sm" color="gray.500">
                                        Try switching the node scope, outcome filter, or sort order.
                                    </Text>
                                </Box>
                            )}
                            {!loading && visibleRecords.length > 0 && (
                                <>
                                    <HistoryRecordsTable records={visibleRecords} nodes={nodes} />
                                    <Stack align="center" mt={6}>
                                        <PanelButton
                                            loading={loading}
                                            onClick={() => setRecordLimit(prev => prev + 30)}
                                        >
                                            Load 30 More Records
                                        </PanelButton>
                                    </Stack>
                                </>
                            )}
                        </GlassPanelSection>
                    </DashboardPageSectionStack>
                )}
            </PageContainer>
        </>
    )
}
