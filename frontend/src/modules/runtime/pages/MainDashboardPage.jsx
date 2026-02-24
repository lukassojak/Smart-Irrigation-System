import { useState, useEffect } from "react"
import { getLiveSnapshot } from "../../../api/runtime.api"
import { useOutletContext } from "react-router-dom"

import useLiveRuntime from "../../../hooks/useLiveRuntime"
import useTodayRuntime from "../../../hooks/useTodayRuntime"

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
    AlertTriangle
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

export default function MainDashboardPage() {

    // ---- Fake Data ----

    // Medium-frequency, updated every 3 minutes
    const todaysActivity = [
        {
            id: "t1",
            zoneName: "Orchard",
            time: "20:00",
            volume: 14,
            status: "planned"
        },
        {
            id: "t2",
            zoneName: "South Lawn",
            time: "18:30",
            volume: 12,
            status: "planned"
        },
        {
            id: "t3",
            zoneName: "Greenhouse",
            time: "12:30",
            volume: 10,
            status: "completed"
        }

    ]

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

    const { data: liveData, loading, error, refresh: refreshLive } = useLiveRuntime(3000)
    const {
        data: todayData,
        loading: todayLoading,
        error: todayError,
        refresh: refreshToday
    } = useTodayRuntime(180000)


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
                <Text p={8} color="red.500">Failed to load live data</Text>
            </Box>
        )
    }

    return (
        <Box>
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


                {/* SECTION 2 - CURRENT IRRIGATION */}
                <GlassPanelSection
                    title="Current Irrigation"
                    description="Active irrigation tasks"
                    collapsible
                >
                    <Stack gap={2}>
                        {liveData.currentTasks.map(task => (
                            <CurrentTaskCard key={task.id} task={task} />
                        ))}
                    </Stack>
                </GlassPanelSection>

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
                    {/* Guard against missing todayData due to loading or error */}
                    {todayData ? (
                        <TodaysActivityCard items={todayData.tasks} />
                    ) : (
                        <Box p={4} borderWidth={1} borderRadius="md" textAlign="center">
                            <Text color="red.500">Failed to load today's activities</Text>
                        </Box>
                    )}

                    <WeatherWaterSummaryCard data={weatherWaterData} />
                </Grid>

                {/* SECTION 5 - ZONES STATUS */}
                <ZonesGridSection zones={liveData.zones} />

                {/* SECTION 6 - WEATHER FORECAST */}
                <WeatherForecastSection data={weatherForecastData} />


            </Stack>
        </Box >
    )
}
