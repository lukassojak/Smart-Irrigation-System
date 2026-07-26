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
    HStack,
    Slider,
} from "@chakra-ui/react"

import { useOutletContext } from "react-router-dom"

import { fetchZoneById } from "../../../api/nodes.api"
import useLiveRuntime from "../../../hooks/useLiveRuntime"
import useRuntimeControlState from "../../../hooks/useRuntimeControlState"
import { startIrrigation as startIrrigationApi } from "../../../api/runtime.api"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import PageContainer from "../../../components/layout/PageContainer"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"

import CurrentTaskCard from "../components/CurrentTaskCard"
import SelectableZoneCard from "../components/SelectableZoneCard"

import LoadingState from "../../../components/ui/LoadingState"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"
import {
    ControlActionDialogViewport,
    openControlActionDialog,
} from "../../../components/ui/ControlActionDialogOverlay"

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

const parsePositiveNumber = (value) => {
    const parsedValue = Number(value)

    if (!Number.isFinite(parsedValue) || parsedValue <= 0) {
        return null
    }

    return parsedValue
}

const formatLiters = (value) => `${value.toFixed(1)} L`

export default function ManualControlPage() {
    const [selectedZone, setSelectedZone] = useState(null)
    const [mode, setMode] = useState("volume")
    const [valueInput, setValueInput] = useState("")
    const [percentageInput, setPercentageInput] = useState(100)
    const [rainMmInput, setRainMmInput] = useState("")
    const [isStarting, setIsStarting] = useState(false)
    const [selectedZoneDetail, setSelectedZoneDetail] = useState(null)
    const [zoneDetailLoading, setZoneDetailLoading] = useState(false)
    const [zoneDetailError, setZoneDetailError] = useState(null)

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

    const selectedZoneNodeId = selectedZoneData?.node_id ?? selectedZoneData?.nodeId ?? null

    useEffect(() => {
        let isActive = true

        if (!selectedZoneData || selectedZoneNodeId === null || selectedZoneNodeId === undefined) {
            setSelectedZoneDetail(null)
            setZoneDetailLoading(false)
            setZoneDetailError(null)
            return undefined
        }

        const loadZoneDetail = async () => {
            setZoneDetailLoading(true)
            setZoneDetailError(null)

            try {
                const response = await fetchZoneById(selectedZoneNodeId, selectedZoneData.id)

                if (!isActive) {
                    return
                }

                setSelectedZoneDetail(response.data)
            } catch (detailError) {
                if (!isActive) {
                    return
                }

                console.error("Failed to load selected zone details:", detailError)
                setSelectedZoneDetail(null)
                setZoneDetailError(detailError)
            } finally {
                if (isActive) {
                    setZoneDetailLoading(false)
                }
            }
        }

        loadZoneDetail()

        return () => {
            isActive = false
        }
    }, [selectedZoneData, selectedZoneNodeId])

    useEffect(() => {
        if (!selectedZoneData) {
            return
        }

        const canStaySelected = selectedZoneData.online && selectedZoneData.status !== "error"
        if (!canStaySelected) {
            setSelectedZone(null)
        }
    }, [selectedZoneData])

    useEffect(() => {
        if (mode !== "rain" || zoneDetailLoading) {
            return
        }

        if (selectedZoneDetail?.irrigation_mode !== "even_area") {
            setMode("volume")
        }
    }, [mode, selectedZoneDetail, zoneDetailLoading])

    const selectedZoneBaseVolumeLiters = useMemo(() => {
        if (!selectedZoneDetail) {
            return null
        }

        if (selectedZoneDetail.irrigation_mode === "even_area") {
            const targetMm = parsePositiveNumber(selectedZoneDetail?.irrigation_configuration?.target_mm)
            const zoneAreaM2 = parsePositiveNumber(selectedZoneDetail?.irrigation_configuration?.zone_area_m2)

            if (targetMm === null || zoneAreaM2 === null) {
                return null
            }

            return targetMm * zoneAreaM2
        }

        return parsePositiveNumber(selectedZoneDetail?.irrigation_configuration?.base_target_volume_liters)
    }, [selectedZoneDetail])

    const selectedZoneAreaM2 = useMemo(() => {
        if (selectedZoneDetail?.irrigation_mode !== "even_area") {
            return null
        }

        return parsePositiveNumber(selectedZoneDetail?.irrigation_configuration?.zone_area_m2)
    }, [selectedZoneDetail])

    const canUseRainMode = selectedZoneDetail?.irrigation_mode === "even_area" || (zoneDetailLoading && mode === "rain")

    const modeOptions = useMemo(() => ([
        { value: "volume", label: "By Volume (L)" },
        { value: "percent", label: "By Base Volume (%)" },
        ...(canUseRainMode ? [{ value: "rain", label: "By Rainfall (mm)" }] : []),
    ]), [canUseRainMode])

    const manualIrrigationPlan = useMemo(() => {
        if (!selectedZoneData) {
            return {
                valid: false,
                message: "Select a zone first.",
                targetVolumeLiters: null,
            }
        }

        if (mode === "volume") {
            const liters = parsePositiveNumber(valueInput)

            if (liters === null) {
                return {
                    valid: false,
                    message: "Enter a value greater than 0 liters.",
                    targetVolumeLiters: null,
                }
            }

            return {
                valid: true,
                message: `Manual volume: ${formatLiters(liters)}.`,
                targetVolumeLiters: liters,
            }
        }

        if (mode === "percent") {
            if (selectedZoneBaseVolumeLiters === null) {
                return {
                    valid: false,
                    message: "Base volume is unavailable for this zone.",
                    targetVolumeLiters: null,
                }
            }

            const targetVolumeLiters = selectedZoneBaseVolumeLiters * (percentageInput / 100)

            if (targetVolumeLiters <= 0) {
                return {
                    valid: false,
                    message: "Calculated volume must be greater than 0 liters.",
                    targetVolumeLiters: null,
                }
            }

            return {
                valid: true,
                message: `${percentageInput}% of base volume = ${formatLiters(targetVolumeLiters)}.`,
                targetVolumeLiters,
            }
        }

        if (mode === "rain") {
            if (selectedZoneDetail?.irrigation_mode !== "even_area") {
                return {
                    valid: false,
                    message: "Rainfall mode is only available for even_area zones.",
                    targetVolumeLiters: null,
                }
            }

            if (selectedZoneAreaM2 === null) {
                return {
                    valid: false,
                    message: "Zone area is unavailable for this zone.",
                    targetVolumeLiters: null,
                }
            }

            const rainfallMm = parsePositiveNumber(rainMmInput)

            if (rainfallMm === null) {
                return {
                    valid: false,
                    message: "Enter a rainfall amount greater than 0 mm.",
                    targetVolumeLiters: null,
                }
            }

            const targetVolumeLiters = rainfallMm * selectedZoneAreaM2

            return {
                valid: true,
                message: `${rainfallMm.toFixed(1)} mm on ${selectedZoneAreaM2.toFixed(1)} m² = ${formatLiters(targetVolumeLiters)}.`,
                targetVolumeLiters,
            }
        }

        return {
            valid: false,
            message: "Unsupported manual control mode.",
            targetVolumeLiters: null,
        }
    }, [mode, percentageInput, rainMmInput, selectedZoneAreaM2, selectedZoneBaseVolumeLiters, selectedZoneData, selectedZoneDetail])

    const openControlDialog = useCallback((payload) => {
        const id = `manual-control-action-result-${Date.now()}`
        openControlActionDialog(id, payload)
    }, [])

    const handleStartManual = useCallback(async () => {
        const targetZone = selectedZoneData
        if (!targetZone || isStarting || !manualIrrigationPlan.valid) {
            return
        }

        setIsStarting(true)
        try {
            const response = await startIrrigationApi({
                zoneId: targetZone.id,
                targetVolume: manualIrrigationPlan.targetVolumeLiters,
                waitForResponse: true,
                timeoutSeconds: 5,
            })

            openControlDialog({
                title: "Manual irrigation started",
                description: `${manualIrrigationPlan.message} Start command completed successfully.`,
                status: "success",
                zoneId: targetZone.id,
                nodeId: response?.node_id,
                mode: response?.mode,
                correlationId: response?.response?.correlation_id,
            })

            setValueInput("")
            setRainMmInput("")
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
    }, [isStarting, manualIrrigationPlan, openControlDialog, selectedZoneData])

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

    const startDisabled = !selectedZoneData || isStarting || !manualIrrigationPlan.valid

    if (loading && !liveData) {
        return (
            <>
                <GlassPageHeader
                    title="Manual Control"
                    subtitle="Override automatic irrigation"
                    showMobileMenuButton={isMobile}
                    onMobileMenuClick={openMobileSidebar}
                />

                <PageContainer>
                    <LoadingState
                        message="Loading live data..."
                    />
                </PageContainer>
            </>
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
                <PageContainer>
                    <GlassPanelSection>
                        <DataUnavailableWarning message="Live runtime data is unavailable. Server may be disconnected." />
                    </GlassPanelSection>
                </PageContainer>
            </Box>
        )
    }

    return (
        <>
            <ControlActionDialogViewport />

            <GlassPageHeader
                title="Manual Control"
                subtitle="Override automatic irrigation"
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <PageContainer>
                <DashboardPageSectionStack>
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
                                        {modeOptions.map((option) => (
                                            <option key={option.value} value={option.value}>
                                                {option.label}
                                            </option>
                                        ))}
                                    </NativeSelect.Field>
                                    <NativeSelect.Indicator />
                                </NativeSelect.Root>

                                {zoneDetailLoading && selectedZoneData && (
                                    <Text fontSize="xs" color="gray.500">
                                        Loading zone configuration...
                                    </Text>
                                )}

                                {zoneDetailError && selectedZoneData && (
                                    <Text fontSize="xs" color="red.500">
                                        Zone configuration could not be loaded. Base-volume and rainfall modes are unavailable.
                                    </Text>
                                )}

                                <Text fontSize="sm" color="gray.600">
                                    Value
                                </Text>

                                {mode === "volume" && (
                                    <Input
                                        placeholder="Enter liters"
                                        type="number"
                                        min="0"
                                        step="0.1"
                                        value={valueInput}
                                        onChange={(event) => setValueInput(event.target.value)}
                                        disabled={!selectedZoneData || isStarting}
                                    />
                                )}

                                {mode === "percent" && (
                                    <VStack align="stretch" gap={3}>
                                        <Slider.Root
                                            value={[percentageInput]}
                                            min={50}
                                            max={150}
                                            step={5}
                                            colorPalette="orange"
                                            onValueChange={(event) => setPercentageInput(event.value[0])}
                                            disabled={!selectedZoneData || isStarting || selectedZoneBaseVolumeLiters === null}
                                        >
                                            <HStack justify="space-between" align="center">
                                                <Text fontSize="sm" color="gray.600">
                                                    Base volume multiplier
                                                </Text>
                                                <Text fontSize="sm" fontWeight="medium">
                                                    {percentageInput}%
                                                </Text>
                                            </HStack>
                                            <Slider.Control>
                                                <Slider.Track>
                                                    <Slider.Range />
                                                </Slider.Track>
                                                <Slider.Thumbs />
                                            </Slider.Control>
                                        </Slider.Root>

                                        <Text fontSize="sm" color="gray.600">
                                            {selectedZoneBaseVolumeLiters === null
                                                ? "Base volume is unavailable for this zone."
                                                : `${percentageInput}% of ${formatLiters(selectedZoneBaseVolumeLiters)} = ${formatLiters(selectedZoneBaseVolumeLiters * (percentageInput / 100))}`}
                                        </Text>
                                    </VStack>
                                )}

                                {mode === "rain" && (
                                    <VStack align="stretch" gap={3}>
                                        <Input
                                            placeholder="Enter rainfall depth in mm"
                                            type="number"
                                            min="0"
                                            step="0.1"
                                            value={rainMmInput}
                                            onChange={(event) => setRainMmInput(event.target.value)}
                                            disabled={!selectedZoneData || isStarting || selectedZoneAreaM2 === null}
                                        />

                                        <Text fontSize="sm" color="gray.600">
                                            {selectedZoneAreaM2 === null
                                                ? "Zone area is unavailable for this zone."
                                                : `1 mm over ${selectedZoneAreaM2.toFixed(1)} m² = ${formatLiters(selectedZoneAreaM2)}`}
                                        </Text>
                                    </VStack>
                                )}

                                {!manualIrrigationPlan.valid && selectedZoneData && (
                                    <Text fontSize="xs" color="red.500">
                                        {manualIrrigationPlan.message}
                                    </Text>
                                )}

                                <Button
                                    colorPalette="orange"
                                    variant="solid"
                                    disabled={startDisabled}
                                    loading={isStarting}
                                    onClick={handleStartManual}
                                >
                                    Start Manual Irrigation
                                </Button>

                                <Text fontSize="xs" color="gray.500">
                                    Manual irrigation overrides scheduled automation. The zone will be skipped by automation for today after the manual irrigation completes.
                                </Text>

                            </VStack>

                        </Grid>


                    </GlassPanelSection>

                    {/* SECTION 2 – Active Irrigation */}
                    <GlassPanelSection
                        title="Active Irrigation Tasks"
                        description="Currently running irrigation sessions"
                        actions={
                            <>
                                {hasActiveTasks && (
                                    <Button
                                        size="xs"
                                        variant="ghost"
                                        colorPalette="red"
                                        onClick={handleStopAllWithNotification}
                                        disabled={!hasActiveTasks || isStoppingAll}
                                        loading={isStoppingAll}
                                    >
                                        Stop All
                                    </Button>
                                )}
                            </>
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
                </DashboardPageSectionStack>
            </PageContainer >

        </>
    )
}
