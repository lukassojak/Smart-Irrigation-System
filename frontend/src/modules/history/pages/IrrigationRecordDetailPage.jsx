import React, { useMemo } from "react"
import { useParams, useNavigate } from "react-router-dom"
import {
    Box,
    Badge,
    Center,
    Flex,
    Heading,
    Text,
    Grid,
    Stack,
    HStack,
    SimpleGrid,
    Button,
    Separator,
} from "@chakra-ui/react"
import {
    Activity,
    ArrowLeft,
    CalendarClock,
    CheckCircle2,
    CloudRain,
    Droplets,
    LandPlot,
    MapPinned,
    Timer,
    Square,
    SunMedium,
    Thermometer,
    TimerReset,
    TriangleAlert,
    Wind,
    WavesArrowDown,
} from "lucide-react"

import { deleteRecordById, fetchRecordById } from "../../../api/history.api"

import {
    ControlActionDialogViewport,
    openControlActionConfirmDialog,
    openControlActionDialog,
} from "../../../components/ui/ControlActionDialogOverlay"
import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import PageContainer from "../../../components/layout/PageContainer"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"
import { HeaderActionDanger, HeaderAction } from "../../../components/ui/ActionButtons"
import WaterAmountGauge from "../components/WaterAmountGauge"


function safeDiv(a, b) {
    if (a == null || b == null) return null
    if (b === 0) return null
    return a / b
}

function computeCorrection(base, standard, actual, label) {
    if (base == null || standard == null || actual == null) return null
    const factor = safeDiv(actual, standard)
    if (factor == null) return null
    const adjusted = base * factor
    const delta = adjusted - base
    return {
        label,
        factor,
        adjusted,
        delta,
    }
}

function formatDateTime(value) {
    if (!value) return "-"

    return new Date(value).toLocaleString("cs-CZ", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    })
}

function formatNumber(value, fractionDigits = 2) {
    if (value == null || Number.isNaN(Number(value))) return "-"
    return Number(value).toFixed(fractionDigits)
}

function getOutcomeMeta(record) {
    const outcome = record?.outcome

    switch (outcome) {
        case "success":
            return {
                label: "Success",
                colorPalette: "green",
                icon: CheckCircle2,
                accent: "rgba(72, 187, 120, 0.08)",
            }
        case "failed":
            return {
                label: "Failed",
                colorPalette: "red",
                icon: TriangleAlert,
                accent: "rgba(245,101,101,0.16)",
            }
        case "stopped":
            return {
                label: "Stopped",
                colorPalette: "orange",
                icon: Square,
                accent: "rgba(237,137,54,0.16)",
            }
        case "interrupted":
            return {
                label: "Interrupted",
                colorPalette: "yellow",
                icon: TriangleAlert,
                accent: "rgba(251,182,206,0.16)",
            }
        case "skipped":
            return {
                label: "Skipped",
                colorPalette: "gray",
                icon: TimerReset,
                accent: "rgba(160,174,192,0.14)",
            }
        default:
            return {
                label: outcome ?? "Unknown",
                colorPalette: "blue",
                icon: Activity,
                accent: "rgba(66,153,225,0.16)",
            }
    }
}

function MetricCard({ icon: Icon, label, value, hint, accent = "rgba(56,178,172,0.08)", valueColor = "gray.800" }) {
    return (
        <Box
            borderRadius="xl"
            p={4}
            bg={accent}
            border="1px solid rgba(56,178,172,0.10)"
            boxShadow="0 10px 24px rgba(15,23,42,0.04)"
        >
            <HStack gap={3} align="flex-start">
                {Icon && (
                    <Center
                        w="40px"
                        h="40px"
                        borderRadius="lg"
                        bg="rgba(255,255,255,0.72)"
                        border="1px solid rgba(255,255,255,0.8)"
                        flexShrink={0}
                    >
                        <Icon size={18} color="#319795" />
                    </Center>
                )}
                <Stack gap={1} minW={0}>
                    <Text fontSize="xs" color="gray.500" textTransform="uppercase" letterSpacing="0.08em">
                        {label}
                    </Text>
                    <Text fontSize="lg" fontWeight="700" color={valueColor} lineHeight="1.15">
                        {value}
                    </Text>
                    {hint && (
                        <Text fontSize="xs" color="gray.600">
                            {hint}
                        </Text>
                    )}
                </Stack>
            </HStack>
        </Box>
    )
}

function MetricConditionCard({ icon: Icon, label, valueFrom, valueTo, unit, hint, accent = "rgba(56,178,172,0.08)", valueColor = "gray.800" }) {
    return (
        <Box
            borderRadius="xl"
            p={4}
            bg={accent}
            border="1px solid rgba(56,178,172,0.10)"
            boxShadow="0 10px 24px rgba(15,23,42,0.04)"
        >
            <HStack gap={3} align="flex-start">
                {Icon && (
                    <Center
                        w="40px"
                        h="40px"
                        borderRadius="lg"
                        bg="rgba(255,255,255,0.72)"
                        border="1px solid rgba(255,255,255,0.8)"
                        flexShrink={0}
                    >
                        <Icon size={18} color="#319795" />
                    </Center>
                )}
                <Stack gap={1} minW={0}>
                    <Text fontSize="xs" color="gray.500" textTransform="uppercase" letterSpacing="0.08em">
                        {label}
                    </Text>
                    <HStack gap={2} align="baseline">
                        <Text fontSize="lg" fontWeight="700" color={valueColor} lineHeight="1.15">
                            {valueFrom != null ? `${formatNumber(valueFrom)}` : "-"}
                        </Text>
                        <Text fontSize="sm" color="gray.500">
                            {unit}
                        </Text>
                        <Text fontSize="lg" fontWeight="700" color={valueColor} lineHeight="1.15" mx={1}>
                            {valueTo != null ? `→` : ""}
                        </Text>
                        <Text fontSize="lg" fontWeight="700" color={valueColor} lineHeight="1.15">
                            {valueTo != null ? `${formatNumber(valueTo)}` : "-"}
                        </Text>
                        <Text fontSize="sm" color="gray.500">
                            {unit}
                        </Text>
                    </HStack>
                    {hint && (
                        <Text fontSize="xs" color="gray.600">
                            {hint}
                        </Text>
                    )}
                </Stack>
            </HStack>
        </Box>
    )
}

function MetricConfigCard({ icon: Icon, label, value, hint, accent = "rgba(56,178,172,0.08)", valueColor = "gray.800" }) {
    return (
        <Box
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={5}
            boxShadow="0 4px 16px rgba(15, 23, 42, 0.05)"
            transition="all 0.15s ease"
            _hover={{
                borderColor: "rgba(56,178,172,0.18)",
                boxShadow: "0 6px 20px rgba(15,23,42,0.06)",
                transform: "translateY(-2px)"
            }}
        >
            <HStack gap={3} align="flex-start">
                {Icon && (
                    <Center
                        w="40px"
                        h="40px"
                        borderRadius="lg"
                        bg="rgba(255,255,255,0.72)"
                        border="1px solid rgba(255,255,255,0.8)"
                        flexShrink={0}
                    >
                        <Icon size={18} color="#319795" />
                    </Center>
                )}
                <Stack gap={1} minW={0}>
                    <Text fontSize="xs" color="gray.500" textTransform="uppercase" letterSpacing="0.08em">
                        {label}
                    </Text>
                    <Text fontSize="lg" fontWeight="700" color={valueColor} lineHeight="1.15">
                        {value}
                    </Text>
                    {hint && (
                        <Text fontSize="xs" color="gray.600">
                            {hint}
                        </Text>
                    )}
                </Stack>
            </HStack>
        </Box>
    )
}

function InfoChip({ icon: Icon, label, value }) {
    return (
        <HStack
            gap={2}
            px={3}
            py={2}
            borderRadius="full"
            bg="rgba(255,255,255,0.65)"
            border="1px solid rgba(56,178,172,0.10)"
            color="gray.700"
            fontSize="sm"
        >
            <Icon size={14} />
            <Text>
                <strong>{label}:</strong> {value}
            </Text>
        </HStack>
    )
}

/* CorrectionGauge removed; replaced by WaterAmountGauge component. */

export default function IrrigationRecordDetailPage() {
    const { recordId } = useParams()
    const navigate = useNavigate()

    const [record, setRecord] = React.useState(null)
    const [loading, setLoading] = React.useState(true)
    const [error, setError] = React.useState(null)

    const handleDeleteRecord = React.useCallback(async () => {
        if (!record) {
            return
        }

        const confirmed = await openControlActionConfirmDialog(`delete-record-${record.id}`, {
            title: "Delete irrigation record",
            description: "Delete this irrigation record? This action cannot be undone.",
            status: "error",
            confirmLabel: "Delete record",
            cancelLabel: "Cancel",
        })

        if (!confirmed) {
            return
        }

        try {
            await deleteRecordById(record.id)
            openControlActionDialog(`delete-record-success-${record.id}`, {
                title: "Record deleted",
                description: "The irrigation record was deleted.",
                status: "success",
            })
            navigate(-1)
        } catch (err) {
            openControlActionDialog(`delete-record-error-${record.id}`, {
                title: "Delete failed",
                description: err?.response?.data?.detail ?? err.message ?? "Failed to delete record.",
                status: "error",
            })
        }
    }, [navigate, record])

    React.useEffect(() => {
        let mounted = true
        async function load() {
            setLoading(true)
            setError(null)
            try {
                const resp = await fetchRecordById(recordId)
                if (!mounted) return
                setRecord(resp.data)
            } catch (err) {
                setError(err.message || String(err))
            } finally {
                if (mounted) setLoading(false)
            }
        }
        load()
        return () => { mounted = false }
    }, [recordId])

    const computed = useMemo(() => {
        if (!record) return {}
        const solar = computeCorrection(record.base_water_amount, record.standard_conditions_solar, record.actual_solar, "solar")
        const rain = computeCorrection(record.base_water_amount, record.standard_conditions_rain, record.actual_rain, "rain")
        const temp = computeCorrection(record.base_water_amount, record.standard_conditions_temp, record.actual_temp, "temperature")

        let carryOverVolume = null
        if (record.outcome === "skipped" && record.dynamic_interval_enabled) {
            carryOverVolume = record.target_water_amount ?? null
        }

        return { solar, rain, temp, carryOverVolume }
    }, [record])

    if (loading) {
        return (
            <>
                <ControlActionDialogViewport />
                <PageContainer>
                    <DataUnavailableWarning message="Loading irrigation record details..." />
                </PageContainer>
            </>
        )
    }

    if (error) {
        return (
            <>
                <ControlActionDialogViewport />
                <PageContainer>
                    <DataUnavailableWarning message="Irrigation record details are unavailable." error={error} />
                    <Button mt={4} onClick={() => navigate(-1)}>Back</Button>
                </PageContainer>
            </>
        )
    }

    if (!record) {
        return (
            <>
                <ControlActionDialogViewport />
                <PageContainer>
                    <DataUnavailableWarning message="Record not found or already deleted." />
                    <Button mt={4} onClick={() => navigate(-1)}>Back</Button>
                </PageContainer>
            </>
        )
    }

    const startStr = record.start_time
        ? new Date(record.start_time).toLocaleString('cs-CZ', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
        })
        : "-"

    const outcomeMeta = getOutcomeMeta(record)
    const OutcomeIcon = outcomeMeta.icon
    const carryOverVolume = computed.carryOverVolume
    const isDynamicSkip = record.outcome === "skipped" && record.dynamic_interval_enabled
    const isUncleanInterrupt = record.outcome === "interrupted" && /unclean|shutdown|power/i.test(record.reason ?? "")
    const zoneTitle = record.zone_name || `Zone ${record.circuit_id}`

    return (
        <>
            <ControlActionDialogViewport />

            <GlassPageHeader
                title={`Irrigation record — Zone #${record.circuit_id}`}
                subtitle={startStr}
                actions={(
                    <>
                        <HeaderAction onClick={() => navigate(-1)}>
                            <ArrowLeft size={16} style={{ marginRight: 6 }} />
                            Back
                        </HeaderAction>
                        <HeaderActionDanger onClick={handleDeleteRecord}>
                            Delete record
                        </HeaderActionDanger>
                    </>
                )}
            />

            <PageContainer>
                <DashboardPageSectionStack>
                    <GlassPanelSection>
                        <Stack gap={4}>
                            <Flex direction={{ base: "column", lg: "row" }} gap={5} align="stretch">
                                <Box flex="1" p={5} borderRadius="2xl" bg={outcomeMeta.accent} border="1px solid rgba(56,178,172,0.10)">
                                    <HStack justify="space-between" align="start" mb={4}>
                                        <Stack gap={2}>
                                            <HStack gap={2} flexWrap="wrap">
                                                <Badge colorPalette={outcomeMeta.colorPalette} variant="subtle">
                                                    <OutcomeIcon size={14} style={{ marginRight: 6 }} />
                                                    {outcomeMeta.label}
                                                </Badge>
                                                {record.zone_deleted && <Badge colorPalette="gray" variant="solid">Deleted zone</Badge>}
                                                {record.was_manual_run && <Badge colorPalette="gray" variant="subtle">Manual run</Badge>}
                                                {record.success != null && (
                                                    <Badge colorPalette={record.success ? "green" : "red"} variant="subtle">
                                                        {record.success ? "Successful" : "Unsuccessful"}
                                                    </Badge>
                                                )}
                                            </HStack>

                                            <Heading size="lg" color="gray.800" letterSpacing="-0.02em">
                                                {record.zone_deleted ? "Deleted Zone" : zoneTitle}
                                            </Heading>

                                            <HStack gap={2} flexWrap="wrap">
                                                <InfoChip icon={CalendarClock} label="Started" value={startStr} />
                                                <InfoChip icon={MapPinned} label="Node ID" value={record.node_id} />
                                                <InfoChip icon={LandPlot} label="Zone ID" value={record.circuit_id} />
                                            </HStack>
                                            <>
                                                {isDynamicSkip && (
                                                    <>
                                                        <Separator mt={4} mb={2} />
                                                        <Box>
                                                            <HStack gap={2} align="start">
                                                                <Stack gap={1}>
                                                                    <Text fontWeight="700" color="gray.800">Skipped by dynamic interval</Text>
                                                                    <Text color="gray.700">
                                                                        The normal target water is not shown here because it has been moved into carry-over volume.
                                                                        This helps explain why the cycle was not executed immediately.
                                                                    </Text>
                                                                    <Text fontSize="sm" color="gray.600">
                                                                        Carry-over volume: <strong>{formatNumber(carryOverVolume)} L</strong>
                                                                    </Text>
                                                                </Stack>
                                                            </HStack>
                                                        </Box>
                                                    </>
                                                )}

                                                {record.outcome === "stopped" && (
                                                    <>
                                                        <Separator mt={4} mb={2} />
                                                        <Box>
                                                            <HStack gap={2} align="start">
                                                                <Stack gap={1}>
                                                                    <Text fontWeight="700" color="gray.800">Stopped irrigation</Text>
                                                                    <Text color="gray.700">
                                                                        This irrigation cycle was stopped by user before completion.
                                                                    </Text>
                                                                    {record.reason && (
                                                                        <Text fontSize="sm" color="gray.600">
                                                                            Reason: <strong>{record.reason}</strong>
                                                                        </Text>
                                                                    )}
                                                                </Stack>
                                                            </HStack>
                                                        </Box>
                                                    </>
                                                )}

                                                {record.outcome === "interrupted" && (
                                                    <>
                                                        <Separator mt={4} mb={2} />
                                                        <Box>
                                                            <HStack gap={2} align="start">
                                                                <Stack gap={1}>
                                                                    <Text fontWeight="700" color="gray.800">Irrigation interrupted</Text>
                                                                    <Text color="gray.700">
                                                                        This irrigation cycle was interrupted unexpectedly.
                                                                    </Text>
                                                                    {isUncleanInterrupt && (
                                                                        <Text fontSize="sm" color="gray.600">
                                                                            The interruption appears to be unclean (e.g., due to power loss or system failure). Please check the system logs for more details.
                                                                        </Text>
                                                                    )}
                                                                    {record.reason && (
                                                                        <Text fontSize="sm" color="gray.600">
                                                                            Reason: <strong>{record.reason}</strong>
                                                                        </Text>
                                                                    )}
                                                                </Stack>
                                                            </HStack>
                                                        </Box>
                                                    </>
                                                )}

                                                {record.outcome === "failed" && (
                                                    <>
                                                        <Separator mt={4} mb={2} />
                                                        <Box>
                                                            <HStack gap={2} align="start">
                                                                <Stack gap={1}>
                                                                    <Text fontWeight="700" color="gray.800">Irrigation failed</Text>
                                                                    <Text color="gray.700">
                                                                        This irrigation cycle failed to complete successfully.
                                                                    </Text>
                                                                    {record.reason && (
                                                                        <Text fontSize="sm" color="gray.600">
                                                                            Reason: <strong>{record.reason}</strong>
                                                                        </Text>
                                                                    )}
                                                                </Stack>
                                                            </HStack>
                                                        </Box>
                                                    </>
                                                )}
                                            </>
                                        </Stack>
                                    </HStack>
                                </Box>

                                <SimpleGrid columns={{ base: 1, md: 2 }} gap={4} flex="1">
                                    <MetricCard
                                        icon={Droplets}
                                        label="Water target"
                                        value={isDynamicSkip ? formatNumber(carryOverVolume) : `${formatNumber(record.target_water_amount)} L`}
                                        hint={isDynamicSkip ? "Displayed as carry-over volume because the cycle was skipped by dynamic interval." : "Planned irrigation volume in liters."}
                                        accent="rgba(56,178,172,0.08)"
                                    />
                                    <MetricCard
                                        icon={Droplets}
                                        label="Actual water"
                                        value={`${formatNumber(record.actual_water_amount)} L`}
                                        hint="Measured or reported delivered volume."
                                        accent="rgba(56,178,172,0.08)"
                                    />
                                    <MetricCard
                                        icon={Timer}
                                        label="Duration"
                                        value={record.completed_duration != null ? `${record.completed_duration} s` : "-"}
                                        hint={record.target_duration != null ? `Target: ${record.target_duration} s` : "No target duration provided."}
                                        accent="rgba(56,178,172,0.08)"
                                    />
                                    <MetricCard
                                        icon={WavesArrowDown}
                                        label="Carry-over"
                                        value={record.carry_over_applied ? "Applied" : "Not applied"}
                                        hint={record.dynamic_interval_enabled ? "Dynamic interval enabled." : "Standard interval flow."}
                                        accent="rgba(56,178,172,0.08)"
                                    />
                                </SimpleGrid>
                            </Flex>
                        </Stack>
                    </GlassPanelSection>

                    <GlassPanelSection title="Zone & Irrigation Context">
                        <SimpleGrid columns={{ base: 1, md: 2, xl: 4 }} gap={4}>
                            <MetricConfigCard
                                label="Irrigation mode"
                                value={record.even_area_mode ? "Even area" : "Per plant"}
                                hint={record.even_area_mode ? "mm-based target is available." : "Volume-based target is available."}
                            />
                            <MetricConfigCard
                                label="Dynamic interval"
                                value={record.dynamic_interval_enabled ? "Enabled" : "Disabled"}
                                hint={record.irrigation_volume_threshold_percent != null ? `Threshold: ${record.irrigation_volume_threshold_percent}%` : "No threshold reported."}
                            />
                            <MetricConfigCard
                                label="Base amount"
                                value={`${formatNumber(record.base_water_amount)} L`}
                                hint="Uncorrected reference target."
                            />
                        </SimpleGrid>
                    </GlassPanelSection>

                    <GlassPanelSection title="Corrections & Conditions">
                        <Stack gap={4}>
                            <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
                                <MetricConditionCard
                                    icon={SunMedium}
                                    label="Solar"
                                    valueFrom={record.standard_conditions_solar}
                                    valueTo={record.actual_solar}
                                    unit="W/m²/day"
                                    hint="Baseline vs actual solar total."
                                />
                                <MetricConditionCard
                                    icon={CloudRain}
                                    label="Rain"
                                    valueFrom={record.standard_conditions_rain}
                                    valueTo={record.actual_rain}
                                    unit="mm/day"
                                    hint="Baseline vs actual rainfall."
                                />
                                <MetricConditionCard
                                    icon={Thermometer}
                                    label="Temperature"
                                    valueFrom={record.standard_conditions_temp}
                                    valueTo={record.actual_temp}
                                    unit="°C avg"
                                    hint="Baseline vs actual temperature."
                                />
                            </SimpleGrid>

                            <Separator />

                            <Box>
                                <WaterAmountGauge
                                    base={record.base_water_amount}
                                    target={record.target_water_amount}
                                    actual={record.actual_water_amount}
                                    unit="L"
                                    manualRun={record.was_manual_run}
                                />
                            </Box>
                        </Stack>
                    </GlassPanelSection>
                </DashboardPageSectionStack>
            </PageContainer>
        </>
    )
}
