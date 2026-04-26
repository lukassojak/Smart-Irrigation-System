import { useCallback } from "react"
import { useOutletContext } from "react-router-dom"

import useLiveRuntime from "../../../hooks/useLiveRuntime"
import useTodayRuntime from "../../../hooks/useTodayRuntime"
import useRuntimeControlState from "../../../hooks/useRuntimeControlState"

import {
    Box,
    Grid,
    Stack,
    Text,
    HStack,
    VStack,
    Progress,
    Badge,
    Button,
    Spinner,
} from "@chakra-ui/react"
import {
    Activity,
    Droplets,
    CloudRain,
    ShieldCheck,
} from "lucide-react"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import PanelSection from "../../../components/layout/PanelSection"
import SystemOverviewCard from "../components/SystemOverviewCard"
import CurrentTaskCard from "../components/CurrentTaskCard"
import AlertItem from "../components/AlertItem"
import TimelineItem from "../components/TimelineItem"
import TodaysActivityCard from "../components/TodaysActivityCard"
import WeatherWaterSummaryCard from "../components/WeatherWaterSummaryCard"
import ZonesGridSection from "../components/ZonesGridSection"
import WeatherForecastSection from "../components/WeatherForecastSection"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"
import {
    controlActionDialog,
    ControlActionDialogViewport,
} from "../components/ControlActionDialogOverlay"

export default function MainDashboardPage() {
    // ---- Fake Data ----

    // Low-frequency, updated every 30 minutes
    const weatherWaterData = {
        windowDays: 7,
        data: [
            { date: "Mon", water: 120, weather: -12 },
            { date: "Tue", water: 140, weather: 8 },
            { date: "Wed", water: 110, weather: -5 },
            { date: "Thu", water: 160, weather: 15 },
            { date: "Fri", water: 130, weather: 2 },
            { date: "Sat", water: 125, weather: -3 },
            { date: "Sun", water: 150, weather: 10 }
        ],
        avgWater: 133,
        avgWeather: 2
    }

    // Low-frequency, updated every 30 minutes
    const weatherForecastData = {
        forecastDays: 5,
        data: [
            { day: "Mon", rain: 1, temp: 22, adjustment: 5 },
            { day: "Tue", rain: 3, temp: 21, adjustment: 2 },
            { day: "Wed", rain: 10, temp: 18, adjustment: -21 },
            { day: "Thu", rain: 0, temp: 27, adjustment: 12 },
            { day: "Fri", rain: 1, temp: 25, adjustment: 6 }
        ],
        summary: {
            todayRain: 1,
            tomorrowRain: 3
        }
    }

    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    const livePollIntervalMs = 2000
    const { data: liveData, loading, error, refresh: refreshLive } = useLiveRuntime(livePollIntervalMs)
    const {
        data: todayData,
        loading: todayLoading,
        error: todayError,
        refresh: refreshToday
    } = useTodayRuntime(180000)

    const {
        stoppingZoneIds,
        isStoppingAll,
        hasActiveTasks,
        handleStopZone,
        handleStopAll,
    } = useRuntimeControlState({
        tasks: liveData?.currentTasks ?? [],
    })

    const openStopActionDialog = useCallback((result) => {
        if (!result) {
            return
        }

        if (result.ok) {
            if (result.action === "stop-zone") {
                controlActionDialog.open("stop-action-result", {
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

            const nodeCount = Array.isArray(result.response?.nodes) ? result.response.nodes.length : 0
            controlActionDialog.open("stop-action-result", {
                title: "Stop all completed",
                description: "Irrigation stop command was delivered to all target nodes.",
                status: "success",
                mode: result.response?.mode,
                nodeCount,
            })
            return
        }

        controlActionDialog.open("stop-action-result", {
            title: "Stop action failed",
            description: result.error?.message ?? "Unknown error occurred while stopping irrigation.",
            status: "error",
            zoneId: result.zoneId,
            nodeId: result.error?.node_id,
            code: result.error?.code,
            retryable: result.error?.retryable,
            correlationId: result.error?.correlation_id,
        })
    }, [])

    const handleStopZoneWithNotification = useCallback(async (zoneId) => {
        const result = await handleStopZone(zoneId)
        openStopActionDialog(result)
    }, [handleStopZone, openStopActionDialog])

    const handleStopAllWithNotification = useCallback(async () => {
        const result = await handleStopAll()
        openStopActionDialog(result)
    }, [handleStopAll, openStopActionDialog])

    if (loading && !liveData) {
        return (
            <Box>
                <GlassPageHeader
                    title="Dashboard"
                    subtitle="Live system overview"
                    showMobileMenuButton={isMobile}
                    onMobileMenuClick={openMobileSidebar}
                />
                <Stack align="center" gap={4} py={20}>
                    <Spinner color="teal.500" size="lg" />

                    <Text
                        fontSize="md"
                        fontWeight="medium"
                        color="teal.700"
                    >
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
                    title="Dashboard"
                    subtitle="Live system overview"
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
                title="Dashboard"
                subtitle="Live system overview"
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <Stack
                gap={8}
                px={{ base: 2, md: 6 }}
                py={{ base: 4, md: 8 }}
            >

                {/* SECTION 1 - SYSTEM OVERVIEW */}
                <GlassPanelSection
                    title="System Overview"
                    description="Current system health and today's irrigation summary"
                >
                    <Grid
                        templateColumns="repeat(auto-fit, minmax(240px, 1fr))"
                        gap={6}
                    >

                        <SystemOverviewCard
                            icon={ShieldCheck}
                            title="System Health"
                            value={`${liveData.overview.zonesOnline} / ${liveData.overview.totalZones}`}
                            description="Zones online"
                            footer={
                                <>
                                    <Badge colorPalette="orange" variant="subtle">
                                        {liveData.overview.warnings} warnings
                                    </Badge>
                                    <Badge colorPalette="red" variant="subtle">
                                        {liveData.overview.errors} errors
                                    </Badge>
                                </>
                            }
                        />

                        <SystemOverviewCard
                            icon={Activity}
                            title="Today Summary"
                            unavailable={!todayLoading && !todayData}
                            unavailableMessage="Today's activities are unavailable right now."
                            value={`${todayData ? todayData.overview.tasksPlanned : "N/A"} planned`}
                            description={`${todayData ? todayData.overview.tasksCompleted : "N/A"} completed`}
                        />

                        <SystemOverviewCard
                            icon={Droplets}
                            title="Water Usage"
                            value="43 L"
                            description="vs average +8%"
                        />

                        <SystemOverviewCard
                            icon={CloudRain}
                            title="Weather Impact"
                            value="+6%"
                            description="Adjustment applied today"
                        />

                    </Grid>
                </GlassPanelSection>


                {/* SECTION 2 - CURRENT IRRIGATION (visible only when there are active tasks) */}
                {liveData.currentTasks.length > 0 && (
                    <GlassPanelSection
                        title="Current Irrigation"
                        description="Active irrigation tasks"
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
                            {(liveData?.currentTasks ?? []).map(task => (
                                <CurrentTaskCard
                                    key={task.id}
                                    task={task}
                                    isStopping={isStoppingAll || stoppingZoneIds[String(task.id)] === true}
                                    onStop={() => handleStopZoneWithNotification(task.id)}
                                />
                            ))}
                        </Stack>
                    </GlassPanelSection>
                )}

                {/* SECTION 3 - ALERTS */}
                <GlassPanelSection
                    title="Alerts"
                    description="Recent system notifications requiring attention"
                    collapsible
                >
                    <Stack gap={2}>
                        {liveData.alerts.map(alert => (
                            <AlertItem key={alert.id} alert={alert} />
                        ))}
                    </Stack>
                </GlassPanelSection>

                {/* SECTION 4 - UPCOMING TASKS */}
                <Grid
                    templateColumns={{ base: "1fr", xl: "1fr 1fr" }}
                    gap={8}
                >
                    <TodaysActivityCard
                        items={todayData?.tasks ?? []}
                        unavailable={Boolean(todayError)}
                        unavailableMessage="Today's activities are unavailable right now."
                    />

                    <WeatherWaterSummaryCard data={weatherWaterData} />
                </Grid>

                {/* SECTION 5 - ZONES STATUS */}
                <ZonesGridSection
                    zones={liveData.zones}
                    stoppingZoneIds={stoppingZoneIds}
                    onStopZone={handleStopZoneWithNotification}
                />

                {/* SECTION 6 - WEATHER FORECAST */}
                <WeatherForecastSection data={weatherForecastData} />


            </Stack>
        </Box >
    )
}
