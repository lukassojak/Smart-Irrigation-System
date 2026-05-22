import { useMemo } from "react"
import { Box, Badge, Button, Grid, HStack, Progress, SimpleGrid, Stack, Text, VStack } from "@chakra-ui/react"
import { ArrowLeft, CalendarClock, CheckCircle2, Clock3, Droplets, Gauge, Repeat2, Sparkles, TimerReset, Waves } from "lucide-react"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import PanelSection from "../../../components/layout/PanelSection"
import FrequencyTimeline from "../../../components/FrequencyTimeline"
import HistoryRecordsTable from "../../history/components/HistoryRecordsTable"
import HistoryStats from "../../history/components/HistoryStats"

function formatDateTime(value) {
    if (!value) {
        return "-"
    }

    const dateValue = value instanceof Date ? value : new Date(value)

    if (Number.isNaN(dateValue.getTime())) {
        return String(value)
    }

    return dateValue.toLocaleString("cs-CZ", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    })
}

function formatWater(liters) {
    if (liters === null || liters === undefined) {
        return "-"
    }

    return `${Number(liters).toFixed(1)} L`
}

function shiftDate(baseDate, minutes) {
    return new Date(baseDate.getTime() + minutes * 60_000)
}

function buildMockTaskHistory(zone, nodeId) {
    const baseTime = zone?.lastRun instanceof Date && !Number.isNaN(zone.lastRun.getTime())
        ? zone.lastRun
        : new Date(Date.now() - 36 * 60 * 60 * 1000)

    return [
        {
            node_id: nodeId,
            circuit_id: zone.id,
            start_time: shiftDate(baseTime, -24 * 60).toISOString(),
            completed_duration: 690,
            actual_water_amount: 16.8,
            target_water_amount: 17.4,
            outcome: "success",
            reason: null,
            zone_deleted: false,
        },
        {
            node_id: nodeId,
            circuit_id: zone.id,
            start_time: shiftDate(baseTime, -48 * 60).toISOString(),
            completed_duration: 0,
            actual_water_amount: 0,
            target_water_amount: 13.6,
            outcome: "skipped",
            reason: "Rainfall correction pushed the result below the irrigation threshold.",
            zone_deleted: false,
        },
        {
            node_id: nodeId,
            circuit_id: zone.id,
            start_time: shiftDate(baseTime, -72 * 60).toISOString(),
            completed_duration: 514,
            actual_water_amount: 14.2,
            target_water_amount: 15.0,
            outcome: "stopped",
            reason: "Manual stop after soil saturation rose faster than expected.",
            zone_deleted: false,
        },
        {
            node_id: nodeId,
            circuit_id: zone.id,
            start_time: shiftDate(baseTime, -96 * 60).toISOString(),
            completed_duration: null,
            actual_water_amount: 0,
            target_water_amount: 16.0,
            outcome: "interrupted",
            reason: "Node reboot during irrigation.",
            zone_deleted: false,
        },
        {
            node_id: nodeId,
            circuit_id: zone.id,
            start_time: shiftDate(baseTime, -120 * 60).toISOString(),
            completed_duration: 768,
            actual_water_amount: 15.9,
            target_water_amount: 16.4,
            outcome: "success",
            reason: null,
            zone_deleted: false,
        },
    ]
}

function buildMockDecisionSteps(zone, activeTask, nextTask) {
    const lastRun = zone?.lastRun instanceof Date && !Number.isNaN(zone.lastRun.getTime())
        ? zone.lastRun
        : new Date(Date.now() - 30 * 60 * 60 * 1000)

    const nextRun = nextTask?.scheduledTime instanceof Date && !Number.isNaN(nextTask.scheduledTime.getTime())
        ? nextTask.scheduledTime
        : shiftDate(lastRun, 18 * 60)

    return [
        {
            icon: <Clock3 size={16} />,
            title: "Last irrigation closed",
            time: formatDateTime(lastRun),
            tone: "green",
            description: "This is the baseline decision input. The node can now measure how much time has passed and whether the zone should be considered for the next dynamic interval.",
        },
        {
            icon: <Waves size={16} />,
            title: "Weather and soil context refreshed",
            time: formatDateTime(shiftDate(lastRun, 360)),
            tone: "blue",
            description: "Rain, temperature, and correction factors are re-evaluated before the next decision window opens.",
        },
        {
            icon: <Repeat2 size={16} />,
            title: "Dynamic interval window opened",
            time: "Between the minimum and maximum allowed days",
            tone: "teal",
            description: "The node keeps the zone eligible, but does not yet commit to the exact day. This is the interval that the mock timeline highlights below.",
        },
        {
            icon: <Sparkles size={16} />,
            title: activeTask ? "A runtime task is already in progress" : "Decision scoring finished",
            time: activeTask ? `${activeTask.progress ?? 0}% complete` : "Highest score locked",
            tone: activeTask ? "orange" : "purple",
            description: activeTask
                ? "The zone is currently irrigating, so the next decision is effectively postponed until the active task finishes."
                : "The best day won on weather balance, volume threshold, and carry-over behaviour.",
        },
        {
            icon: <CalendarClock size={16} />,
            title: "Next irrigation decision",
            time: formatDateTime(nextRun),
            tone: "red",
            description: "This is the mocked nearest future irrigation. In the real product this will come from node-side dynamic interval telemetry.",
        },
    ]
}

function MetricCard({ icon, label, value, helper, accent = "teal" }) {
    return (
        <Box
            borderRadius="2xl"
            bg="rgba(255,255,255,0.76)"
            backdropFilter="blur(18px) saturate(160%)"
            border="1px solid rgba(56,178,172,0.12)"
            boxShadow="0 12px 30px rgba(15,23,42,0.05)"
            p={5}
        >
            <HStack spacing={3} mb={3} align="center">
                <Box
                    p={2}
                    borderRadius="xl"
                    bg={`${accent}.50`}
                    color={`${accent}.600`}
                >
                    {icon}
                </Box>
                <Text fontSize="sm" fontWeight="700" color="gray.600">
                    {label}
                </Text>
            </HStack>

            <Text fontSize="2xl" fontWeight="800" color="gray.800" lineHeight="1.1">
                {value}
            </Text>

            <Text fontSize="sm" color="gray.500" mt={2} lineHeight="1.45">
                {helper}
            </Text>
        </Box>
    )
}

function DecisionStep({ step, index, isLast = false }) {
    const colorMap = {
        green: { bg: "green.500", border: "rgba(72,187,120,0.20)", panel: "rgba(72,187,120,0.08)" },
        blue: { bg: "blue.500", border: "rgba(66,153,225,0.20)", panel: "rgba(66,153,225,0.08)" },
        teal: { bg: "teal.500", border: "rgba(56,178,172,0.22)", panel: "rgba(56,178,172,0.10)" },
        orange: { bg: "orange.500", border: "rgba(237,137,54,0.22)", panel: "rgba(237,137,54,0.10)" },
        purple: { bg: "purple.500", border: "rgba(159,122,234,0.22)", panel: "rgba(159,122,234,0.08)" },
        red: { bg: "red.500", border: "rgba(245,101,101,0.20)", panel: "rgba(245,101,101,0.08)" },
    }[step.tone] ?? { bg: "gray.500", border: "rgba(113,128,150,0.18)", panel: "rgba(113,128,150,0.08)" }

    return (
        <HStack align="stretch" spacing={4} position="relative">
            <VStack spacing={0} align="center" flexShrink={0}>
                <Box
                    w="12px"
                    h="12px"
                    borderRadius="full"
                    bg={colorMap.bg}
                    boxShadow={`0 0 0 5px ${colorMap.panel}`}
                />
                {!isLast && (
                    <Box w="2px" flex="1" minH="48px" bg="rgba(148,163,184,0.30)" />
                )}
            </VStack>

            <Box
                flex="1"
                borderRadius="2xl"
                bg={colorMap.panel}
                border="1px solid"
                borderColor={colorMap.border}
                p={4}
            >
                <HStack justify="space-between" align="flex-start" gap={4}>
                    <Stack gap={1} flex="1">
                        <HStack gap={2} flexWrap="wrap">
                            <Badge colorPalette="gray" variant="subtle">
                                Step {index + 1}
                            </Badge>
                            <Text fontWeight="700" color="gray.800">
                                {step.title}
                            </Text>
                        </HStack>
                        <Text fontSize="sm" color="gray.600" lineHeight="1.5">
                            {step.description}
                        </Text>
                    </Stack>

                    <Box
                        flexShrink={0}
                        px={3}
                        py={2}
                        borderRadius="xl"
                        bg="rgba(255,255,255,0.66)"
                        border="1px solid rgba(255,255,255,0.75)"
                    >
                        <Text fontSize="xs" color="gray.500" mb={1}>
                            Decision signal
                        </Text>
                        <HStack gap={2} color="gray.700">
                            {step.icon}
                            <Text fontSize="sm" fontWeight="700">
                                {step.time}
                            </Text>
                        </HStack>
                    </Box>
                </HStack>
            </Box>
        </HStack>
    )
}

export default function RuntimeZoneDetailPage({ zone, liveData, todayData, currentTasks = [], todayTasks = [], onBack }) {
    const derived = useMemo(() => {
        const zoneName = zone?.name ?? `Zone ${zone?.id ?? "?"}`
        const nodeId = Number(zone?.id ?? 1)
        const nodeName = `${zoneName} Node`
        const matchingCurrentTask = currentTasks.find((task) => task.zoneName === zoneName)
        const matchingTodayTask = todayTasks.find((task) => String(task.zoneId) === String(zone?.id) || task.zoneName === zoneName)
        const mockHistory = buildMockTaskHistory(zone, nodeId)
        const historyNode = [{ id: nodeId, name: nodeName, zones: [{ id: zone?.id, name: zoneName }] }]
        const isDynamicIntervalEnabled = true
        const nextDecisionTask = matchingTodayTask ?? {
            scheduledTime: shiftDate(zone?.lastRun instanceof Date && !Number.isNaN(zone.lastRun.getTime()) ? zone.lastRun : new Date(), 18 * 60),
            expectedVolume: 15.2,
            expectedAdjustmentPercent: 6,
            status: "scheduled",
        }

        return {
            zoneName,
            nodeId,
            nodeName,
            matchingCurrentTask,
            matchingTodayTask,
            mockHistory,
            historyNode,
            isDynamicIntervalEnabled,
            nextDecisionTask,
            summary: {
                statusLabel: zone?.status ?? "unknown",
                statusTone: zone?.status === "irrigating" ? "blue" : zone?.status === "error" ? "red" : zone?.status === "offline" ? "gray" : "green",
                lastRun: zone?.lastRun,
                nextRun: nextDecisionTask.scheduledTime,
                activeProgress: matchingCurrentTask?.progress ?? null,
                currentVolume: matchingCurrentTask?.currentVolume ?? null,
                targetVolume: matchingCurrentTask?.targetVolume ?? null,
                remainingMinutes: matchingCurrentTask?.remainingMinutes ?? null,
                waterForecast: nextDecisionTask.expectedVolume,
            },
        }
    }, [currentTasks, todayTasks, zone])

    const decisionSteps = useMemo(() => {
        return buildMockDecisionSteps(zone, derived.matchingCurrentTask, derived.nextDecisionTask)
    }, [derived.matchingCurrentTask, derived.nextDecisionTask, zone])

    const mockFrequencySettings = useMemo(() => ({
        min_interval_days: 2,
        max_interval_days: 6,
        carry_over_volume: true,
        irrigation_volume_threshold_percent: 18,
    }), [])

    if (!zone) {
        return (
            <Box>
                <GlassPageHeader
                    title="Runtime Zone Detail"
                    subtitle="Mock runtime detail for an irrigation zone"
                />
                <Box p={8}>
                    <PanelSection title="No zone selected">
                        <Text color="gray.600">
                            Select a zone card from the dashboard to open the mock runtime detail.
                        </Text>
                    </PanelSection>
                </Box>
            </Box>
        )
    }

    return (
        <Box>
            <GlassPageHeader
                title={`Zone #${zone.id} runtime detail`}
                subtitle={derived.zoneName}
                actions={(
                    <Button
                        variant="outline"
                        colorPalette="teal"
                        onClick={onBack}
                    >
                        <HStack gap={2}>
                            <ArrowLeft size={16} />
                            <Text>Back to dashboard</Text>
                        </HStack>
                    </Button>
                )}
            >
                <HStack gap={2} flexWrap="wrap">
                    <Badge colorPalette={derived.summary.statusTone} variant="subtle">
                        {derived.summary.statusLabel}
                    </Badge>
                    <Badge colorPalette="teal" variant="subtle">
                        Mock UI only
                    </Badge>
                    <Badge colorPalette="gray" variant="subtle">
                        Dynamic interval runtime data not yet collected
                    </Badge>
                </HStack>
            </GlassPageHeader>

            <Stack gap={8} px={{ base: 4, md: 8 }} py={{ base: 4, md: 8 }}>
                <Box
                    borderRadius="3xl"
                    bg="linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(236,253,245,0.88) 100%)"
                    border="1px solid rgba(56,178,172,0.12)"
                    boxShadow="0 18px 42px rgba(15,23,42,0.06)"
                    p={{ base: 5, md: 6 }}
                >
                    <Grid templateColumns={{ base: "1fr", xl: "1.3fr 0.9fr" }} gap={6} alignItems="stretch">
                        <Stack spacing={4}>
                            <HStack gap={3} flexWrap="wrap">
                                <Badge colorPalette="teal" variant="solid">
                                    Zone #{zone.id}
                                </Badge>
                                <Badge colorPalette="gray" variant="subtle">
                                    {derived.nodeName}
                                </Badge>
                                {zone.online ? (
                                    <Badge colorPalette="green" variant="subtle">Online</Badge>
                                ) : (
                                    <Badge colorPalette="gray" variant="subtle">Offline</Badge>
                                )}
                            </HStack>

                            <Stack spacing={2}>
                                <Text fontSize={{ base: "3xl", md: "4xl" }} fontWeight="900" letterSpacing="-0.03em" color="gray.800">
                                    {derived.zoneName}
                                </Text>
                                <Text maxW="2xl" fontSize="md" color="gray.600" lineHeight="1.6">
                                    This mock runtime view explains the zone's next decision, the dynamic interval window, and the recent task history. The timeline is intentionally visual so operators can understand why the node would irrigate now, wait, or skip.
                                </Text>
                            </Stack>

                            <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
                                <MetricCard
                                    icon={<Clock3 size={18} />}
                                    label="Last known irrigation"
                                    value={formatDateTime(derived.summary.lastRun)}
                                    helper="Baseline for the next dynamic interval calculation."
                                />
                                <MetricCard
                                    icon={<CalendarClock size={18} />}
                                    label="Nearest future decision"
                                    value={formatDateTime(derived.summary.nextRun)}
                                    helper="Mocked from the current zone context and today schedule."
                                    accent="blue"
                                />
                            </SimpleGrid>
                        </Stack>

                        <Box
                            borderRadius="2xl"
                            bg="rgba(15,23,42,0.90)"
                            color="white"
                            p={5}
                            boxShadow="0 16px 36px rgba(15,23,42,0.24)"
                        >
                            <HStack justify="space-between" align="start" mb={4}>
                                <Stack spacing={1}>
                                    <Text fontSize="sm" color="rgba(226,232,240,0.82)">Decision spotlight</Text>
                                    <Text fontSize="2xl" fontWeight="800">What the node would do next</Text>
                                </Stack>
                                <Badge colorPalette="green" variant="solid">
                                    {derived.isDynamicIntervalEnabled ? "Dynamic" : "Fixed"}
                                </Badge>
                            </HStack>

                            <Stack spacing={4}>
                                <Box>
                                    <HStack justify="space-between" mb={2}>
                                        <Text fontSize="sm" color="rgba(226,232,240,0.82)">Active task progress</Text>
                                        <Text fontSize="sm" fontWeight="700">
                                            {derived.summary.activeProgress !== null ? `${derived.summary.activeProgress}%` : "No active task"}
                                        </Text>
                                    </HStack>
                                    <Progress.Root
                                        value={derived.summary.activeProgress ?? 0}
                                        colorPalette="teal"
                                        size="sm"
                                        borderRadius="full"
                                    >
                                        <Progress.Track bg="rgba(255,255,255,0.08)">
                                            <Progress.Range bg="teal.400" />
                                        </Progress.Track>
                                    </Progress.Root>
                                </Box>

                                <SimpleGrid columns={2} gap={4}>
                                    <Box p={4} borderRadius="xl" bg="rgba(255,255,255,0.08)">
                                        <Text fontSize="xs" color="rgba(226,232,240,0.72)">Current volume</Text>
                                        <Text fontSize="lg" fontWeight="800">{formatWater(derived.summary.currentVolume)}</Text>
                                    </Box>
                                    <Box p={4} borderRadius="xl" bg="rgba(255,255,255,0.08)">
                                        <Text fontSize="xs" color="rgba(226,232,240,0.72)">Target volume</Text>
                                        <Text fontSize="lg" fontWeight="800">{formatWater(derived.summary.targetVolume)}</Text>
                                    </Box>
                                    <Box p={4} borderRadius="xl" bg="rgba(255,255,255,0.08)">
                                        <Text fontSize="xs" color="rgba(226,232,240,0.72)">Remaining time</Text>
                                        <Text fontSize="lg" fontWeight="800">
                                            {derived.summary.remainingMinutes !== null ? `${derived.summary.remainingMinutes} min` : "-"}
                                        </Text>
                                    </Box>
                                    <Box p={4} borderRadius="xl" bg="rgba(255,255,255,0.08)">
                                        <Text fontSize="xs" color="rgba(226,232,240,0.72)">Projected volume</Text>
                                        <Text fontSize="lg" fontWeight="800">{formatWater(derived.summary.waterForecast)}</Text>
                                    </Box>
                                </SimpleGrid>

                                <Text fontSize="sm" color="rgba(226,232,240,0.86)" lineHeight="1.6">
                                    The mocked next decision is based on the last run, the current weather correction story, and the zone-specific interval window. In the real product this will become node-side telemetry.
                                </Text>
                            </Stack>
                        </Box>
                    </Grid>
                </Box>

                <Grid templateColumns={{ base: "1fr", xl: "1.1fr 0.9fr" }} gap={8}>
                    <GlassPanelSection
                        title="Dynamic interval timeline"
                        description="A visual explanation of how the node evaluates the next irrigation window."
                    >
                        <Stack spacing={6}>
                            <FrequencyTimeline settings={mockFrequencySettings} />

                            <Box>
                                <Text fontSize="sm" fontWeight="700" color="gray.700" mb={3}>
                                    Why this decision matters
                                </Text>
                                <Stack spacing={4}>
                                    {decisionSteps.map((step, index) => (
                                        <DecisionStep
                                            key={step.title}
                                            step={step}
                                            index={index}
                                            isLast={index === decisionSteps.length - 1}
                                        />
                                    ))}
                                </Stack>
                            </Box>
                        </Stack>
                    </GlassPanelSection>

                    <GlassPanelSection
                        title="Runtime summary"
                        description="The current zone is summarized with the same cadence an operator would expect in a live drill-down."
                    >
                        <SimpleGrid columns={{ base: 1, md: 2 }} gap={4}>
                            <MetricCard
                                icon={<Gauge size={18} />}
                                label="Decision status"
                                value={zone.status}
                                helper="Mocked from the live runtime snapshot."
                                accent="orange"
                            />
                            <MetricCard
                                icon={<Droplets size={18} />}
                                label="Expected water"
                                value={formatWater(derived.summary.waterForecast)}
                                helper="Projected from today schedule and runtime context."
                                accent="blue"
                            />
                            <MetricCard
                                icon={<TimerReset size={18} />}
                                label="Threshold story"
                                value="18%"
                                helper="Below this point the node would prefer skipping or deferring the cycle."
                                accent="teal"
                            />
                            <MetricCard
                                icon={<CheckCircle2 size={18} />}
                                label="Carry-over"
                                value="Enabled"
                                helper="Skipped volume can roll over into the next irrigation cycle."
                                accent="green"
                            />
                        </SimpleGrid>

                        <Box mt={6} p={4} borderRadius="2xl" bg="rgba(56,178,172,0.06)" border="1px solid rgba(56,178,172,0.12)">
                            <HStack justify="space-between" align="start" gap={4}>
                                <Stack spacing={1}>
                                    <Text fontWeight="700" color="gray.800">
                                        Mock runtime note
                                    </Text>
                                    <Text fontSize="sm" color="gray.600" lineHeight="1.55">
                                        The node-side dynamic interval calculation is referenced here as an explanation layer only. No server persistence or node telemetry is changed by this page.
                                    </Text>
                                </Stack>
                                <Badge colorPalette="gray" variant="subtle">
                                    Frontend only
                                </Badge>
                            </HStack>
                        </Box>
                    </GlassPanelSection>
                </Grid>

                <PanelSection
                    title="Task history"
                    description="Recent irrigation tasks for this zone, rendered with the same record-card language as the history page."
                >
                    <Stack spacing={6}>
                        <HistoryStats records={derived.mockHistory} />
                        <HistoryRecordsTable records={derived.mockHistory} nodes={derived.historyNode} />
                    </Stack>
                </PanelSection>

                <PanelSection
                    title="Context"
                    description="A quick operator note tying the mock runtime view back to the live dashboard and today's plan."
                >
                    <SimpleGrid columns={{ base: 1, md: 3 }} gap={4}>
                        <Box p={4} borderRadius="xl" bg="rgba(255,255,255,0.78)" border="1px solid rgba(56,178,172,0.10)">
                            <Text fontSize="xs" color="gray.500" mb={1}>Live snapshot</Text>
                            <Text fontWeight="700" color="gray.800">{liveData?.overview?.zonesOnline ?? "-"} zones online</Text>
                        </Box>
                        <Box p={4} borderRadius="xl" bg="rgba(255,255,255,0.78)" border="1px solid rgba(56,178,172,0.10)">
                            <Text fontSize="xs" color="gray.500" mb={1}>Today's schedule</Text>
                            <Text fontWeight="700" color="gray.800">{todayData?.overview?.tasksPlanned ?? "-"} tasks planned</Text>
                        </Box>
                        <Box p={4} borderRadius="xl" bg="rgba(255,255,255,0.78)" border="1px solid rgba(56,178,172,0.10)">
                            <Text fontSize="xs" color="gray.500" mb={1}>Selected zone</Text>
                            <Text fontWeight="700" color="gray.800">Zone #{zone.id}</Text>
                        </Box>
                    </SimpleGrid>
                </PanelSection>
            </Stack>
        </Box>
    )
}