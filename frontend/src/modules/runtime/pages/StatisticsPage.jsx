import {
    Box,
    Grid,
    Stack,
    Text,
    HStack,
    Badge,
    Checkbox,
    Button,
    useBreakpointValue,
    Combobox,
    Highlight,
    Portal,
    useComboboxContext,
    useFilter,
    useListCollection,
    createListCollection,
} from "@chakra-ui/react"
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    Tooltip,
    ResponsiveContainer,
    BarChart,
    Bar,
    PieChart,
    Pie,
    Cell,
    ReferenceLine,
} from "recharts"
import { Check } from "lucide-react"

import { useOutletContext } from "react-router-dom"
import { useEffect, useMemo, useState } from "react"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import PageContainer from "../../../components/layout/PageContainer"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"
import LoadingState from "../../../components/ui/LoadingState"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"

import { fetchNodes } from "../../../api/nodes.api"
import {
    fetchStatisticsOverview,
    fetchWaterUsageTrend,
    fetchOutcomeBreakdown,
    fetchZoneCorrectionTrend,
    fetchZoneWaterDistribution,
} from "../../../api/statistics.api"

import StatisticsOverviewCard from "../components/StatisticsOverviewCard"

const PIE_COLORS = ["rgba(56,161,105,0.85)", "rgba(217,119,6,0.85)", "rgba(113,128,150,0.85)", "rgba(217,119,6,0.85)", "rgba(229,62,62,0.85)"]
// Define a lighter color palette for zones in the Zone Water Distribution chart, supporting up to 10 zones. If there are more than 10 zones, colors will repeat.
// The colors are chosen to be visually distinct but with a lighter tone and similar tones to avoid overwhelming the chart.
const ZONE_WATER_DISTRIBUTION_COLORS = [
    "rgba(56,161,105,0.6)", // Zone 1
    "rgba(105, 161, 56, 0.6)",  // Zone 2
    "rgba(149, 161, 56, 0.6)",  // Zone 3
    "rgba(161, 105, 56, 0.6)",  // Zone 4
    "rgba(161, 56, 105, 0.6)",  // Zone 5
    "rgba(143, 56, 161, 0.6)",  // Zone 6
    "rgba(56, 105, 161, 0.6)",  // Zone 7
    "rgba(56, 161, 149, 0.6)",  // Zone 8
    "rgba(161, 80, 56, 0.6)",  // Zone 9
    "rgba(161, 56, 80, 0.6)",  // Zone 10
]

function formatWaterAmount(value) {
    return `${Number(value ?? 0).toFixed(1)} L`
}

function formatWaterAmountCompact(value) {
    return `${Math.round(Number(value ?? 0))} L`
}

function formatTrendDate(value) {
    const dateValue = String(value ?? "")
    if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
        return dateValue.slice(5)
    }
    return dateValue
}

function formatCorrectionPercent(value) {
    const numericValue = Number(value ?? 0)
    const sign = numericValue >= 0 ? "+" : "-"
    return `${sign}${Math.abs(numericValue).toFixed(1)}%`
}

function formatCorrectionPercentCompact(value) {
    const numericValue = Number(value ?? 0)
    const sign = numericValue >= 0 ? "+" : "-"
    return `${sign}${Math.abs(numericValue).toFixed(0)}%`
}

function formatOutcomeLabel(value) {
    if (typeof value !== "string" || !value) {
        return "Unknown"
    }
    return value.charAt(0).toUpperCase() + value.slice(1)
}

function toOverviewMetrics(payload) {
    if (!payload) {
        return null
    }

    return {
        totalWater: payload.total_water ?? 0,
        avgDailyWater: payload.avg_daily_water ?? 0,
        irrigationRuns: payload.irrigation_runs ?? 0,
        efficiency: 0,
        weatherAdjustments: 0,
        autoRuns: payload.auto_runs ?? 0,
        manualRuns: payload.manual_runs ?? 0,
        failedRuns: payload.failed_runs ?? 0,
        interruptedRuns: payload.interrupted_runs ?? 0,
        skippedRuns: payload.skipped_runs ?? 0,
        stoppedRuns: payload.stopped_runs ?? 0,
        avgDuration: payload.avg_duration ?? 0,
        avgAdjustment: 0,
        avgCorrection: (payload.avg_correction ?? 0) * 100,
        successRate: Math.round((payload.success_rate ?? 0) * 100),
    }
}

function getRangeCount(value) {
    if (value === "14d") {
        return 14
    }
    if (value === "7d") {
        return 7
    }
    return 30
}

function getRangeLabel(value) {
    if (value === "14d") {
        return "Last 14 days"
    }
    if (value === "7d") {
        return "Last 7 days"
    }
    if (value === "all") {
        return "All time"
    }
    return "Last 30 days"
}

function buildZoneOptions(nodes) {
    return nodes.flatMap((node) => {
        const zones = Array.isArray(node.zones) ? node.zones : []
        return zones.map((zone) => ({
            value: String(zone.id),
            label: zone.name ? `Zone ${zone.id} · ${zone.name}` : `Zone ${zone.id}`,
            nodeLabel: node.name ?? `Node ${node.id}`,
            comboboxLabel: zone.name ? `${zone.name}` : `Zone ${zone.id}`,
        }))
    })
}

export default function StatisticsPage() {
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    const [nodes, setNodes] = useState([])
    const [overviewRange, setOverviewRange] = useState("30d")
    const [waterTrendRange, setWaterTrendRange] = useState("30d")
    const [outcomeBreakdownRange, setOutcomeBreakdownRange] = useState("30d")
    const [correctionTrendRange, setCorrectionTrendRange] = useState("30d")
    const [zoneUsageRange, setZoneUsageRange] = useState("30d")
    const [selectedCorrectionZone, setSelectedCorrectionZone] = useState("all")
    const [selectedOutcomeZones, setSelectedOutcomeZones] = useState([])
    const [selectedDistributionZones, setSelectedDistributionZones] = useState([])

    const [overviewPayload, setOverviewPayload] = useState(null)
    const [waterTrendPayload, setWaterTrendPayload] = useState(null)
    const [outcomeBreakdownPayload, setOutcomeBreakdownPayload] = useState(null)
    const [correctionTrendPayload, setCorrectionTrendPayload] = useState(null)
    const [zoneWaterPayload, setZoneWaterPayload] = useState(null)
    const [overviewLoading, setOverviewLoading] = useState(true)
    const [waterTrendLoading, setWaterTrendLoading] = useState(true)
    const [outcomeBreakdownLoading, setOutcomeBreakdownLoading] = useState(true)
    const [correctionTrendLoading, setCorrectionTrendLoading] = useState(true)
    const [zoneWaterLoading, setZoneWaterLoading] = useState(true)
    const [error, setError] = useState(null)
    const [nodesLoaded, setNodesLoaded] = useState(false)
    const isBaseOrMdViewport = useBreakpointValue({ base: true, md: true, xl: false }) ?? false
    const isBaseViewport = useBreakpointValue({ base: true, md: false }) ?? false
    const [showAllOverviewCards, setShowAllOverviewCards] = useState(false)

    const dayRangeOptions = [
        { value: "30d", label: "30d" },
        { value: "14d", label: "14d" },
        { value: "7d", label: "7d" },
    ]

    const overviewRangeOptions = [
        ...dayRangeOptions,
        { value: "all", label: "All" },
    ]

    useEffect(() => {
        let ignore = false

        async function loadNodes() {
            try {
                const response = await fetchNodes()
                if (!ignore) {
                    setNodes(response.data || [])
                    setNodesLoaded(true)
                }
            } catch (err) {
                if (!ignore) {
                    setNodes([])
                    setNodesLoaded(true)
                    setError(err)
                }
            }
        }

        loadNodes()

        return () => {
            ignore = true
        }
    }, [])

    const zoneOptions = useMemo(() => buildZoneOptions(nodes), [nodes])
    const allZoneIds = useMemo(() => zoneOptions.map((opt) => opt.value), [zoneOptions])
    const selectedOutcomeZoneIds = useMemo(() => {
        if (selectedOutcomeZones.length > 0) {
            return selectedOutcomeZones
        }
        return allZoneIds
    }, [selectedOutcomeZones, allZoneIds])
    const selectedDistributionZoneIds = useMemo(() => {
        if (selectedDistributionZones.length > 0) {
            return selectedDistributionZones
        }
        return allZoneIds
    }, [selectedDistributionZones, allZoneIds])

    // Combobox helpers for zone lists (used in Outcome Breakdown and Zone Water Distribution)
    const zoneItems = useMemo(() => zoneOptions.map((o) => ({ label: o.label, value: o.value })), [zoneOptions])
    const { contains } = useFilter({ sensitivity: "base" })
    const [outcomeInput, setOutcomeInput] = useState("")
    const [distributionInput, setDistributionInput] = useState("")
    const [correctionInput, setCorrectionInput] = useState("")
    const filteredOutcomeItems = useMemo(() => zoneItems.filter((it) => contains(it.label, outcomeInput)), [zoneItems, outcomeInput, contains])
    const filteredDistributionItems = useMemo(() => zoneItems.filter((it) => contains(it.label, distributionInput)), [zoneItems, distributionInput, contains])
    const correctionZoneItems = useMemo(() => [{ label: "All zones", value: "all" }, ...zoneItems], [zoneItems])
    const filteredCorrectionItems = useMemo(() => correctionZoneItems.filter((it) => contains(it.label, correctionInput)), [correctionZoneItems, correctionInput, contains])

    const outcomeCollection = useMemo(() => createListCollection({ items: filteredOutcomeItems, itemToString: (i) => i.label, itemToValue: (i) => i.value }), [filteredOutcomeItems])
    const distributionCollection = useMemo(() => createListCollection({ items: filteredDistributionItems, itemToString: (i) => i.label, itemToValue: (i) => i.value }), [filteredDistributionItems])
    const correctionCollection = useMemo(() => createListCollection({ items: filteredCorrectionItems, itemToString: (i) => i.label, itemToValue: (i) => i.value }), [filteredCorrectionItems])

    // Initialize with all zones selected by default
    useEffect(() => {
        if (selectedOutcomeZones.length === 0 && allZoneIds.length > 0) {
            setSelectedOutcomeZones(allZoneIds)
        }
    }, [allZoneIds, selectedOutcomeZones.length])

    useEffect(() => {
        if (selectedDistributionZones.length === 0 && allZoneIds.length > 0) {
            setSelectedDistributionZones(allZoneIds)
        }
    }, [allZoneIds, selectedDistributionZones.length])

    const handleOutcomeValueChange = (details) => {
        setSelectedOutcomeZones(details.value)
    }

    const handleDistributionValueChange = (details) => {
        setSelectedDistributionZones(details.value)
    }

    function ComboboxListItem({ item }) {
        const combobox = useComboboxContext()
        return (
            <Combobox.Item item={item} key={item.value}>
                <Combobox.ItemText>
                    <Highlight ignoreCase query={combobox.inputValue} styles={{ bg: "yellow.emphasized", fontWeight: "medium" }}>
                        {item.label}
                    </Highlight>
                </Combobox.ItemText>
                <Combobox.ItemIndicator />
            </Combobox.Item>
        )
    }

    useEffect(() => {
        if (!nodesLoaded) {
            return
        }

        let ignore = false

        async function loadOverview() {
            setOverviewLoading(true)
            try {
                const response = await fetchStatisticsOverview({
                    range_days: overviewRange === "all" ? 3650 : getRangeCount(overviewRange),
                })
                if (!ignore) {
                    setOverviewPayload(response.data)
                }
            } catch (err) {
                if (!ignore) {
                    setOverviewPayload(null)
                    setError(err)
                }
            } finally {
                if (!ignore) {
                    setOverviewLoading(false)
                }
            }
        }

        loadOverview()

        return () => {
            ignore = true
        }
    }, [overviewRange, nodesLoaded])

    useEffect(() => {
        if (!nodesLoaded) {
            return
        }

        let ignore = false

        async function loadWaterTrend() {
            setWaterTrendLoading(true)
            try {
                const response = await fetchWaterUsageTrend({
                    range_days: getRangeCount(waterTrendRange),
                })
                if (!ignore) {
                    setWaterTrendPayload(response.data)
                }
            } catch (err) {
                if (!ignore) {
                    setWaterTrendPayload(null)
                    setError(err)
                }
            } finally {
                if (!ignore) {
                    setWaterTrendLoading(false)
                }
            }
        }

        loadWaterTrend()

        return () => {
            ignore = true
        }
    }, [waterTrendRange, nodesLoaded])

    useEffect(() => {
        if (!nodesLoaded) {
            return
        }

        let ignore = false

        async function loadOutcomeBreakdown() {
            setOutcomeBreakdownLoading(true)
            try {
                const response = await fetchOutcomeBreakdown({
                    range_days: getRangeCount(outcomeBreakdownRange),
                    circuit_ids: selectedOutcomeZoneIds.map(Number),
                })
                if (!ignore) {
                    setOutcomeBreakdownPayload(response.data)
                }
            } catch (err) {
                if (!ignore) {
                    setOutcomeBreakdownPayload(null)
                    setError(err)
                }
            } finally {
                if (!ignore) {
                    setOutcomeBreakdownLoading(false)
                }
            }
        }

        loadOutcomeBreakdown()

        return () => {
            ignore = true
        }
    }, [outcomeBreakdownRange, selectedOutcomeZoneIds, nodesLoaded])

    useEffect(() => {
        if (!nodesLoaded) {
            return
        }

        let ignore = false

        async function loadCorrectionTrend() {
            setCorrectionTrendLoading(true)
            try {
                const response = await fetchZoneCorrectionTrend({
                    range_days: getRangeCount(correctionTrendRange),
                    ...(selectedCorrectionZone !== "all" ? { circuit_id: Number(selectedCorrectionZone) } : {}),
                })
                if (!ignore) {
                    setCorrectionTrendPayload(response.data)
                }
            } catch (err) {
                if (!ignore) {
                    setCorrectionTrendPayload(null)
                    setError(err)
                }
            } finally {
                if (!ignore) {
                    setCorrectionTrendLoading(false)
                }
            }
        }

        loadCorrectionTrend()

        return () => {
            ignore = true
        }
    }, [correctionTrendRange, selectedCorrectionZone, nodesLoaded])

    useEffect(() => {
        if (!nodesLoaded) {
            return
        }

        let ignore = false

        async function loadZoneWaterDistribution() {
            setZoneWaterLoading(true)
            try {
                const response = await fetchZoneWaterDistribution({
                    range_days: getRangeCount(zoneUsageRange),
                    circuit_ids: selectedDistributionZoneIds.map(Number),
                })
                if (!ignore) {
                    setZoneWaterPayload(response.data)
                }
            } catch (err) {
                if (!ignore) {
                    setZoneWaterPayload(null)
                    setError(err)
                }
            } finally {
                if (!ignore) {
                    setZoneWaterLoading(false)
                }
            }
        }

        loadZoneWaterDistribution()

        return () => {
            ignore = true
        }
    }, [zoneUsageRange, selectedDistributionZoneIds, nodesLoaded])

    const overviewMetrics = useMemo(() => toOverviewMetrics(overviewPayload), [overviewPayload])
    const waterTrendData = useMemo(() => {
        if (waterTrendPayload?.points?.length) {
            return waterTrendPayload.points.map((point) => ({
                ...point,
                dateLabel: formatTrendDate(point.date),
            }))
        }
        return []
    }, [waterTrendPayload, waterTrendRange])
    const waterTrendShowDots = !(isBaseViewport && waterTrendData.length > 14)

    const outcomeBreakdownData = useMemo(() => {
        if (outcomeBreakdownPayload?.items?.length) {
            return outcomeBreakdownPayload.items
        }
        return []
    }, [outcomeBreakdownPayload])

    const zoneWaterData = useMemo(() => {
        if (zoneWaterPayload?.items?.length) {
            return zoneWaterPayload.items.map((item) => ({
                zone: item.zone_name || `Zone ${item.circuit_id}`,
                water: item.water,
            }))
        }
        return []
    }, [zoneWaterPayload])

    const correctionTrendData = useMemo(() => {
        if (correctionTrendPayload?.points?.length) {
            return correctionTrendPayload.points.map((point) => ({
                ...point,
                dateLabel: formatTrendDate(point.date),
                correctionPercent: Number(point.correction ?? 0) * 100,
            }))
        }
        return []
    }, [correctionTrendPayload, selectedCorrectionZone, zoneOptions])
    const correctionTrendShowDots = !(isBaseViewport && correctionTrendData.length > 14)

    const correctionMaxAbs = Math.max(1, ...correctionTrendData.map((item) => Math.abs(item.correctionPercent)))
    const correctionAverage = (correctionTrendPayload?.avg_correction ?? correctionTrendData.reduce((sum, item) => sum + (item.correctionPercent / 100), 0) / Math.max(correctionTrendData.length, 1)) * 100

    const overviewRangeFilter = { value: overviewRange, onChange: setOverviewRange, options: overviewRangeOptions }
    const waterTrendRangeFilter = { value: waterTrendRange, onChange: setWaterTrendRange, options: dayRangeOptions }
    const outcomeBreakdownRangeFilter = { value: outcomeBreakdownRange, onChange: setOutcomeBreakdownRange, options: dayRangeOptions }
    const correctionTrendRangeFilter = { value: correctionTrendRange, onChange: setCorrectionTrendRange, options: dayRangeOptions }
    const zoneUsageRangeFilter = { value: zoneUsageRange, onChange: setZoneUsageRange, options: dayRangeOptions }

    const handleCheckboxChange = (setter, zoneValue) => (details) => {
        setter((prev) => {
            const isChecked = Boolean(details.checked)
            if (isChecked) {
                return [...new Set([...prev, zoneValue])]
            }
            return prev.filter((id) => id !== zoneValue)
        })
    }

    const handleCheckboxAllChange = (setter, allZoneIds) => (details) => {
        const isChecked = Boolean(details.checked)
        if (isChecked) {
            setter(allZoneIds)
            return
        }
        setter([])
    }

    const selectedCorrectionZoneLabel = selectedCorrectionZone === "all"
        ? "All zones"
        : zoneOptions.find((option) => option.value === selectedCorrectionZone)?.label || `Zone ${selectedCorrectionZone}`

    return (
        <>
            <GlassPageHeader
                title="Statistics"
                subtitle="Irrigation analytics and performance overview"
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <PageContainer>
                <DashboardPageSectionStack>
                    <GlassPanelSection
                        title="Overview"
                        description={`Aggregate performance metrics for ${getRangeLabel(overviewRange).toLowerCase()}`}
                        rangeFilter={overviewRangeFilter}
                        isLoading={overviewLoading}
                    >
                        {!overviewLoading && !overviewMetrics && (
                            <DataUnavailableWarning message="Overview data is currently unavailable." error={error ? String(error?.message || error) : undefined} />
                        )}
                        {overviewMetrics && (
                            <>
                                <Grid templateColumns={{ base: "1fr", md: "1fr 1fr", lg: "1fr 1fr 1fr 1fr" }} gap={6}>
                                    <StatisticsOverviewCard label="Total Water" value={`${overviewMetrics.totalWater.toFixed(1)} L`} description={`Total water used in ${getRangeLabel(overviewRange).toLowerCase()}`} />
                                    <StatisticsOverviewCard label="Avg Daily" value={`${overviewMetrics.avgDailyWater.toFixed(1)} L`} description={`Over ${getRangeLabel(overviewRange).toLowerCase()}`} footer={<Badge colorPalette="teal">+5% vs previous month</Badge>} />
                                    <StatisticsOverviewCard label="Irrigation Runs" value={overviewMetrics.irrigationRuns} description="Total irrigation runs executed within all zones" />
                                    <StatisticsOverviewCard label="Success rate" value={`${overviewMetrics.successRate}%`} description="Completed successfully without interruption or failure" />
                                </Grid>

                                {(!isBaseOrMdViewport || showAllOverviewCards) && (
                                    <Grid templateColumns={{ base: "1fr 1fr", md: "repeat(4, minmax(0, 1fr))", lg: "1fr 1fr 1fr 1fr" }} gap={6} mt={6}>
                                        <StatisticsOverviewCard label="Avg correction" value={formatCorrectionPercent(overviewMetrics.avgCorrection)} />
                                        <StatisticsOverviewCard label="Avg Duration" value={`${Math.round(overviewMetrics.avgDuration)} s`} />
                                        <StatisticsOverviewCard label="Auto Runs" value={overviewMetrics.autoRuns} />
                                        <StatisticsOverviewCard label="Manual Runs" value={overviewMetrics.manualRuns} />
                                        <StatisticsOverviewCard label="Interrupted" value={overviewMetrics.interruptedRuns} />
                                        <StatisticsOverviewCard label="Failed" value={overviewMetrics.failedRuns} />
                                        <StatisticsOverviewCard label="Skipped" value={overviewMetrics.skippedRuns} />
                                        <StatisticsOverviewCard label="Stopped" value={overviewMetrics.stoppedRuns} />
                                    </Grid>
                                )}

                                {isBaseOrMdViewport && (
                                    <Box mt={6} textAlign="center">
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            colorPalette="teal"
                                            onClick={() => setShowAllOverviewCards((prev) => !prev)}
                                        >
                                            {showAllOverviewCards ? "Hide additional cards" : "Show all cards"}
                                        </Button>
                                    </Box>
                                )}
                            </>
                        )}
                    </GlassPanelSection>

                    <GlassPanelSection
                        title="Water Usage Trend"
                        description={`Daily water consumption for ${getRangeLabel(waterTrendRange).toLowerCase()}`}
                        rangeFilter={waterTrendRangeFilter}
                        isLoading={waterTrendLoading}
                    >
                        {!waterTrendLoading && !waterTrendPayload && (
                            <DataUnavailableWarning message="Water usage trend data is currently unavailable." error={error ? String(error?.message || error) : undefined} />
                        )}
                        {waterTrendPayload && (
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={waterTrendData} margin={isBaseViewport ? { top: 8, right: 8, left: 0, bottom: 0 } : undefined}>
                                    <XAxis dataKey="dateLabel" tickFormatter={formatTrendDate} />
                                    <YAxis
                                        tickFormatter={isBaseViewport ? formatWaterAmountCompact : formatWaterAmount}
                                        width={isBaseViewport ? 45 : undefined}
                                        tickMargin={isBaseViewport ? 4 : undefined}
                                    />
                                    <Tooltip
                                        labelFormatter={(label) => formatTrendDate(label)}
                                        formatter={(value) => [formatWaterAmount(value), "Water"]}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="water"
                                        stroke="#319795"
                                        strokeWidth={2}
                                        dot={waterTrendShowDots}
                                        activeDot={waterTrendShowDots ? { r: 4 } : false}
                                    />
                                </LineChart>
                            </ResponsiveContainer>
                        )}
                    </GlassPanelSection>

                    <Grid templateColumns={{ base: "1fr", lg: "1fr 1fr" }} gap={8}>
                        <GlassPanelSection
                            title="Outcome Breakdown"
                            description="Distribution of irrigation outcomes"
                            rangeFilter={outcomeBreakdownRangeFilter}
                            isLoading={outcomeBreakdownLoading}
                        >
                            <Stack gap={4}>
                                <Box>
                                    <Text mb={2} fontSize="sm" fontWeight="600" color="gray.700">
                                        Zone filter
                                    </Text>
                                    <Stack gap={2} ps={2}>
                                        <Combobox.Root
                                            multiple
                                            width="100%"
                                            collection={outcomeCollection}
                                            value={selectedOutcomeZones}
                                            onValueChange={handleOutcomeValueChange}
                                            onInputValueChange={(e) => setOutcomeInput(e.inputValue)}
                                            openOnClick
                                            closeOnSelect={false}
                                        >
                                            <Combobox.Control>
                                                <Combobox.Input placeholder="Type to search zones" />
                                                <Combobox.IndicatorGroup>
                                                    <Combobox.ClearTrigger />
                                                    <Combobox.Trigger />
                                                </Combobox.IndicatorGroup>
                                            </Combobox.Control>
                                            <Portal>
                                                <Combobox.Positioner>
                                                    <Combobox.Content>
                                                        {filteredOutcomeItems.length > 0 ? filteredOutcomeItems.map((item) => (
                                                            <ComboboxListItem item={item} key={item.value} />
                                                        )) : <Combobox.Empty>No zones found</Combobox.Empty>}
                                                    </Combobox.Content>
                                                </Combobox.Positioner>
                                            </Portal>
                                        </Combobox.Root>

                                        <Text mt={2} fontSize="sm" color="gray.600">
                                            {selectedOutcomeZones.length === zoneOptions.length ? "All zones" : zoneOptions.filter((o) => selectedOutcomeZones.includes(o.value)).map((o) => o.label).join(", ")}
                                        </Text>
                                    </Stack>
                                </Box>
                                {!outcomeBreakdownLoading && !outcomeBreakdownPayload && (
                                    <DataUnavailableWarning message="Outcome breakdown data is currently unavailable." error={error ? String(error?.message || error) : undefined} />
                                )}
                                {outcomeBreakdownPayload && (
                                    <ResponsiveContainer width="100%" height={300}>
                                        <PieChart>
                                            <Pie data={outcomeBreakdownData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={110} paddingAngle={2}>
                                                {outcomeBreakdownData.map((entry, index) => (
                                                    <Cell key={`${entry.name}-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                                                ))}
                                            </Pie>
                                            <Tooltip
                                                formatter={(value, name) => [value, formatOutcomeLabel(name)]}
                                            />
                                        </PieChart>
                                    </ResponsiveContainer>
                                )}
                            </Stack>
                        </GlassPanelSection>

                        <GlassPanelSection
                            title="Zone Correction Trend"
                            description={`Average correction applied to base water for ${selectedCorrectionZoneLabel} over ${getRangeLabel(correctionTrendRange).toLowerCase()}`}
                            rangeFilter={correctionTrendRangeFilter}
                            isLoading={correctionTrendLoading}
                        >
                            <Stack gap={4}>
                                <Box>
                                    <Text mb={2} fontSize="sm" fontWeight="600" color="gray.700">
                                        Zone filter
                                    </Text>
                                    <Combobox.Root
                                        closeOnSelect
                                        openOnClick
                                        onOpenChange={() => setCorrectionInput("")}
                                        width="100%"
                                        collection={correctionCollection}
                                        value={[selectedCorrectionZone]}
                                        onValueChange={(details) => setSelectedCorrectionZone(details.value[0] || "all")}
                                        onInputValueChange={(e) => setCorrectionInput(e.inputValue)}
                                    >
                                        <Combobox.Control>
                                            <Combobox.Input placeholder="Type to search zones" />
                                            <Combobox.IndicatorGroup>
                                                <Combobox.ClearTrigger />
                                                <Combobox.Trigger />
                                            </Combobox.IndicatorGroup>
                                        </Combobox.Control>
                                        <Portal>
                                            <Combobox.Positioner>
                                                <Combobox.Content>
                                                    {filteredCorrectionItems.length > 0 ? filteredCorrectionItems.map((item) => (
                                                        <Combobox.Item item={item} key={item.value}>
                                                            <Combobox.ItemText>
                                                                <Highlight ignoreCase query={correctionInput} styles={{ bg: "yellow.emphasized", fontWeight: "medium" }}>
                                                                    {item.label}
                                                                </Highlight>
                                                            </Combobox.ItemText>
                                                            <Combobox.ItemIndicator />
                                                        </Combobox.Item>
                                                    )) : <Combobox.Empty>No zones found</Combobox.Empty>}
                                                </Combobox.Content>
                                            </Combobox.Positioner>
                                        </Portal>
                                    </Combobox.Root>
                                </Box>
                                {!correctionTrendLoading && !correctionTrendPayload && (
                                    <DataUnavailableWarning message="Correction trend data is currently unavailable." error={error ? String(error?.message || error) : undefined} />
                                )}
                                {correctionTrendPayload && (
                                    <>
                                        <Text fontSize="sm" color="gray.600">
                                            {getRangeLabel(correctionTrendRange)}
                                        </Text>

                                        <ResponsiveContainer width="100%" height={260}>
                                            <LineChart data={correctionTrendData} margin={isBaseViewport ? { top: 8, right: 8, left: 0, bottom: 0 } : undefined}>
                                                <XAxis dataKey="dateLabel" tickFormatter={formatTrendDate} />
                                                <YAxis
                                                    domain={[-correctionMaxAbs, correctionMaxAbs]}
                                                    tickFormatter={isBaseViewport ? formatCorrectionPercentCompact : formatCorrectionPercent}
                                                    width={isBaseViewport ? 50 : undefined}
                                                    tickMargin={isBaseViewport ? 4 : undefined}
                                                />
                                                <Tooltip
                                                    labelFormatter={(label) => formatTrendDate(label)}
                                                    formatter={(value) => [formatCorrectionPercent(value), "Correction"]}
                                                />
                                                <ReferenceLine y={0} stroke="#9CA3AF" strokeDasharray="4 4" />
                                                <Line
                                                    dataKey="correctionPercent"
                                                    stroke="#319795"
                                                    strokeWidth={2}
                                                    dot={correctionTrendShowDots}
                                                    activeDot={correctionTrendShowDots ? { r: 4 } : false}
                                                />
                                            </LineChart>
                                        </ResponsiveContainer>

                                        <HStack justify="space-between" align="center">
                                            <Text fontSize="sm" color="gray.600">
                                                Average correction over {getRangeLabel(correctionTrendRange).toLowerCase()}
                                            </Text>
                                            <Badge colorPalette="teal" variant="subtle">
                                                {formatCorrectionPercent(correctionAverage)}
                                            </Badge>
                                        </HStack>
                                    </>
                                )}
                            </Stack>
                        </GlassPanelSection>

                        <GlassPanelSection title="Zone Water Distribution" description="Water usage per zone" rangeFilter={zoneUsageRangeFilter} isLoading={zoneWaterLoading}>
                            <Stack gap={4}>
                                <Box>
                                    <Text mb={2} fontSize="sm" fontWeight="600" color="gray.700">
                                        Zone filter
                                    </Text>
                                    <Stack gap={2} ps={2}>
                                        <Combobox.Root
                                            multiple
                                            closeOnSelect={false}
                                            openOnClick
                                            width="100%"
                                            collection={distributionCollection}
                                            value={selectedDistributionZones}
                                            onValueChange={handleDistributionValueChange}
                                            onInputValueChange={(e) => setDistributionInput(e.inputValue)}
                                        >
                                            <Combobox.Control>
                                                <Combobox.Input placeholder="Type to search zones" />
                                                <Combobox.IndicatorGroup>
                                                    <Combobox.ClearTrigger />
                                                    <Combobox.Trigger />
                                                </Combobox.IndicatorGroup>
                                            </Combobox.Control>
                                            <Portal>
                                                <Combobox.Positioner>
                                                    <Combobox.Content>
                                                        {filteredDistributionItems.length > 0 ? filteredDistributionItems.map((item) => (
                                                            <ComboboxListItem item={item} key={item.value} />
                                                        )) : <Combobox.Empty>No zones found</Combobox.Empty>}
                                                    </Combobox.Content>
                                                </Combobox.Positioner>
                                            </Portal>
                                        </Combobox.Root>

                                        <Text mt={2} fontSize="sm" color="gray.600">
                                            {selectedDistributionZones.length === zoneOptions.length ? "All zones" : zoneOptions.filter((o) => selectedDistributionZones.includes(o.value)).map((o) => o.label).join(", ")}
                                        </Text>
                                    </Stack>
                                </Box>

                                {!zoneWaterLoading && !zoneWaterPayload && (
                                    <DataUnavailableWarning message="Zone water distribution data is currently unavailable." error={error ? String(error?.message || error) : undefined} />
                                )}
                                {zoneWaterPayload && (
                                    <ResponsiveContainer width="100%" height={300}>
                                        <BarChart data={zoneWaterData}>
                                            <XAxis dataKey="zone" />
                                            <YAxis tickFormatter={formatWaterAmount} />
                                            <Tooltip
                                                formatter={(value) => [formatWaterAmount(value), "Water"]}
                                            />
                                            <Bar dataKey="water" fill="#319795">
                                                {zoneWaterData.map((entry, index) => (
                                                    <Cell key={`cell-${index}`} fill={ZONE_WATER_DISTRIBUTION_COLORS[index % ZONE_WATER_DISTRIBUTION_COLORS.length]} />
                                                ))}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                )}
                            </Stack>
                        </GlassPanelSection>
                    </Grid>
                </DashboardPageSectionStack>
            </PageContainer>
        </>
    )
}
