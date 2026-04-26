import { useCallback, useEffect, useMemo, useState } from "react"
import {
    Box,
    Stack,
    Grid,
    Text,
    NativeSelect,
    Input,
    Button,
    VStack,
    Spinner,
} from "@chakra-ui/react"

import { useOutletContext } from "react-router-dom"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import CurrentTaskCard from "../components/CurrentTaskCard"
import SelectableZoneCard from "../components/SelectableZoneCard"
import useLiveRuntime from "../../../hooks/useLiveRuntime"
import useRuntimeControlState from "../../../hooks/useRuntimeControlState"
import { startIrrigation as startIrrigationApi } from "../../../api/runtime.api"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"
import {
    controlActionDialog,
    ControlActionDialogViewport,
} from "../components/ControlActionDialogOverlay"

const buildErrorDetail = (error, fallbackMessage) => {
    const detail = error?.response?.data?.detail

    if (typeof detail === "string") {
        return {
            message: detail,
            retryable: false,
        }
    }

    if (detail && typeof detail === "object") {
        return {
            ...detail,
            message: detail.message ?? fallbackMessage,
            retryable: Boolean(detail.retryable),
        }
    }

    return {
        message: error?.message ?? fallbackMessage,
        retryable: false,
    }
}

export default function ManualControlPage() {
    const [selectedZone, setSelectedZone] = useState(null)
    const [mode, setMode] = useState("volume")
    const [valueInput, setValueInput] = useState("")
    const [isStarting, setIsStarting] = useState(false)

    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    const livePollIntervalMs = 2000
    const { data: liveData, loading, error } = useLiveRuntime(livePollIntervalMs)

    const zones = liveData?.zones ?? []
    const activeTasks = liveData?.currentTasks ?? []

    const {
        stoppingZoneIds,
        isStoppingAll,
        hasActiveTasks,
        handleStopZone,
        handleStopAll,
    } = useRuntimeControlState({ tasks: activeTasks })

    const selectedZoneData = useMemo(
        () => zones.find(zone => String(zone.id) === String(selectedZone)),
        [selectedZone, zones],
    )

    useEffect(() => {
        if (!selectedZoneData) {
            return
        }

        const canStaySelected = selectedZoneData.online && selectedZoneData.status !== "error"
        if (!canStaySelected) {
            setSelectedZone(null)
        }
    }, [selectedZoneData])

    const openControlDialog = useCallback((payload) => {
        controlActionDialog.open("manual-control-action-result", payload)
    }, [])

    const handleStartManual = useCallback(async () => {
        const targetZone = selectedZoneData
        if (!targetZone || isStarting) {
            return
        }

        const numericValue = Number(valueInput)
        if (!Number.isFinite(numericValue) || numericValue <= 0) {
            openControlDialog({
                title: "Invalid input",
                description: "Enter a value greater than 0 liters.",
                status: "error",
                zoneId: targetZone.id,
            })
            return
        }

        setIsStarting(true)
        try {
            const response = await startIrrigationApi({
                zoneId: targetZone.id,
                targetVolume: numericValue,
                waitForResponse: true,
                timeoutSeconds: 5,
            })

            openControlDialog({
                title: "Manual irrigation started",
                description: "Start command completed successfully.",
                status: "success",
                zoneId: targetZone.id,
                nodeId: response?.node_id,
                mode: response?.mode,
                correlationId: response?.response?.correlation_id,
            })

            setValueInput("")
        } catch (startError) {
            const errorDetail = buildErrorDetail(startError, `Failed to start irrigation for zone ${targetZone.id}`)
            openControlDialog({
                title: "Start action failed",
                description: errorDetail.message,
                status: "error",
                zoneId: targetZone.id,
                nodeId: errorDetail.node_id,
                code: errorDetail.code,
                retryable: errorDetail.retryable,
                correlationId: errorDetail.correlation_id,
            })
        } finally {
            setIsStarting(false)
        }
    }, [isStarting, openControlDialog, selectedZoneData, valueInput])

    const handleStopZoneWithNotification = useCallback(async (zoneId) => {
        const result = await handleStopZone(zoneId)
        if (!result) {
            return
        }

        if (result.ok) {
            openControlDialog({
                title: "Zone stop completed",
                description: "Irrigation stop command was completed successfully.",
                status: "success",
                zoneId: result.zoneId,
                nodeId: result.response?.node_id,
                mode: result.response?.mode,
                correlationId: result.response?.response?.correlation_id,
            })
            return
        }

        openControlDialog({
            title: "Stop action failed",
            description: result.error?.message ?? "Unknown error occurred while stopping irrigation.",
            status: "error",
            zoneId: result.zoneId,
            nodeId: result.error?.node_id,
            code: result.error?.code,
            retryable: result.error?.retryable,
            correlationId: result.error?.correlation_id,
        })
    }, [handleStopZone, openControlDialog])

    const handleStopAllWithNotification = useCallback(async () => {
        const result = await handleStopAll()
        if (!result) {
            return
        }

        if (result.ok) {
            const nodeCount = Array.isArray(result.response?.nodes) ? result.response.nodes.length : 0
            openControlDialog({
                title: "Stop all completed",
                description: "Irrigation stop command was delivered to all target nodes.",
                status: "success",
                mode: result.response?.mode,
                nodeCount,
            })
            return
        }

        openControlDialog({
            title: "Stop action failed",
            description: result.error?.message ?? "Unknown error occurred while stopping irrigation.",
            status: "error",
            nodeId: result.error?.node_id,
            code: result.error?.code,
            retryable: result.error?.retryable,
            correlationId: result.error?.correlation_id,
        })
    }, [handleStopAll, openControlDialog])

    const startDisabled = !selectedZoneData || isStarting || mode !== "volume"

    if (loading && !liveData) {
        return (
            <Box>
                <GlassPageHeader
                    title="Manual Control"
                    subtitle="Override automatic irrigation"
                    showMobileMenuButton={isMobile}
                    onMobileMenuClick={openMobileSidebar}
                />

                <Stack align="center" gap={4} py={20}>
                    <Spinner color="teal.500" size="lg" />
                    <Text fontSize="md" fontWeight="medium" color="teal.700">
                        Loading live data...
                    </Text>
                </Stack>
            </Box>
        )
    }

    if (error) {
        return (
            <Box>
                <GlassPageHeader
                    title="Manual Control"
                    subtitle="Override automatic irrigation"
                    showMobileMenuButton={isMobile}
                    onMobileMenuClick={openMobileSidebar}
                />
                <Box p={8}>
                    <DataUnavailableWarning message="Live runtime data is unavailable. Server may be disconnected." />
                </Box>
            </Box>
        )
    }

    return (
        <Box>
            <ControlActionDialogViewport />

            <GlassPageHeader
                title="Manual Control"
                subtitle="Override automatic irrigation"
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <Stack
                gap={8}
                px={{ base: 4, md: 8 }}
                py={8}
            >

                {/* SECTION 1 – Start Manual */}
                <GlassPanelSection
                    title="Start Manual Irrigation"
                    description="Select zone and parameters to start immediate irrigation"
                >
                    <Grid
                        templateColumns={{ base: "1fr", xl: "2fr 1fr" }}
                        gap={{ base: 4, md: 8 }}
                    >

                        {/* Zone Selection */}
                        <Grid
                            templateColumns={{
                                base: "1fr",
                                md: "1fr 1fr"
                            }}
                            gap={4}
                        >
                            {zones.map(zone => (
                                <SelectableZoneCard
                                    key={zone.id}
                                    zone={zone}
                                    selected={selectedZone === zone.id}
                                    onClick={() =>
                                        zone.online && zone.status !== "error" &&
                                        setSelectedZone(zone.id)
                                    }
                                />
                            ))}
                        </Grid>

                        {/* Parameters */}
                        <VStack align="stretch" gap={4}>

                            <Text fontSize="sm" color="gray.600">
                                Mode
                            </Text>

                            <NativeSelect.Root>
                                <NativeSelect.Field
                                    value={mode}
                                    onChange={(event) => setMode(event.target.value)}
                                >
                                    <option value="volume">By Volume (L)</option>
                                </NativeSelect.Field>
                                <NativeSelect.Indicator />
                            </NativeSelect.Root>

                            <Text fontSize="sm" color="gray.600">
                                Value
                            </Text>

                            <Input
                                placeholder="Enter value"
                                type="number"
                                value={valueInput}
                                onChange={(event) => setValueInput(event.target.value)}
                                isDisabled={!selectedZoneData || isStarting}
                            />

                            <Button
                                colorPalette="orange"
                                variant="solid"
                                isDisabled={startDisabled}
                                loading={isStarting}
                                onClick={handleStartManual}
                            >
                                Start Manual Irrigation
                            </Button>

                            <Text fontSize="xs" color="gray.500">
                                Manual irrigation overrides scheduled automation.
                            </Text>

                        </VStack>

                    </Grid>


                </GlassPanelSection>

                {/* SECTION 2 – Active Irrigation */}
                <GlassPanelSection
                    title="Active Irrigation Tasks"
                    description="Currently running irrigation sessions"
                    actions={
                        <Button
                            size="xs"
                            variant="ghost"
                            colorPalette="red"
                            onClick={handleStopAllWithNotification}
                            isDisabled={!hasActiveTasks || isStoppingAll}
                            loading={isStoppingAll}
                        >
                            Stop All
                        </Button>
                    }
                >
                    <Stack gap={2}>
                        {activeTasks.map(task => (
                            <Box key={task.id}>
                                <CurrentTaskCard
                                    task={task}
                                    isStopping={isStoppingAll || stoppingZoneIds[String(task.id)] === true}
                                    onStop={() => handleStopZoneWithNotification(task.id)}
                                />
                            </Box>
                        ))}

                        {activeTasks.length === 0 && (
                            <Text fontSize="sm" color="gray.500" textAlign="center" py={6}>
                                No active irrigation tasks.
                            </Text>
                        )}
                    </Stack>
                </GlassPanelSection>
            </Stack>

        </Box>
    )
}
