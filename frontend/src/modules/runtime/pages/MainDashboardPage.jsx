import {
    Box,
    Grid,
    Stack,
    Text,
    HStack,
    VStack,
    Progress,
    Badge,
    Button
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

    const overview = {
        zonesOnline: 12,
        totalZones: 15,
        warnings: 1,
        errors: 0,
        irrigationPlanned: 5,
        completedToday: 2,
        waterUsedToday: 124,
        waterDelta: "+8%",
        weatherAdjustment: "-15%"
    }

    const currentTasks = [
        {
            id: "1",
            zoneName: "South Lawn",
            progress: 45,
            currentVolume: 6.2,
            targetVolume: 12,
            remainingMinutes: 5
        },
        {
            id: "2",
            zoneName: "Greenhouse",
            progress: 70,
            currentVolume: 9.8,
            targetVolume: 14,
            remainingMinutes: 3
        }
    ]

    const alerts = [
        {
            id: "a1",
            type: "warning",
            title: "Low flow detected",
            message: "Zone South Lawn reported lower than expected flow.",
            timestamp: "12:42 today"
        },
        {
            id: "a2",
            type: "error",
            title: "Water leak detected",
            message: "Zone Greenhouse reported a possible leak. Immediate inspection recommended.",
            timestamp: "08:15 today"
        }
    ]

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

    const zones = [
        {
            id: "1",
            name: "South Lawn",
            status: "irrigating", // irrigating | idle | error | stopping
            enabled: true,
            online: true,
            lastRun: "today 12:30",
            progress: 45
        },
        {
            id: "2",
            name: "Greenhouse",
            status: "irrigating",
            enabled: true,
            online: true,
            lastRun: "today 12:30"
        },
        {
            id: "3",
            name: "South Flowerbed",
            status: "idle",
            enabled: true,
            online: true,
            lastRun: "today 07:00"
        },
        {
            id: "4",
            name: "North Lawn",
            status: "idle",
            enabled: true,
            online: true,
            lastRun: "yesterday"
        },
        {
            id: "5",
            name: "Orchard",
            status: "offline",
            enabled: false,
            online: false,
            lastRun: "yesterday"
        },
        {
            id: "6",
            name: "North Garden",
            status: "offline",
            enabled: true,
            online: false,
            lastRun: "2 days ago"
        },
        {
            id: "7",
            name: "East Flowerbed",
            status: "error",
            enabled: true,
            online: true,
            lastRun: "N/A"
        }
    ]

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




    return (
        <Box>

            <GlassPageHeader
                title="Dashboard"
                subtitle="Live system overview"
            />

            <Stack gap={8} p={8}>

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
                            value={`${overview.zonesOnline} / ${overview.totalZones}`}
                            description="Zones online"
                            footer={
                                <>
                                    <Badge colorPalette="orange" variant="subtle">
                                        {overview.warnings} warnings
                                    </Badge>
                                    <Badge colorPalette="red" variant="subtle">
                                        {overview.errors} errors
                                    </Badge>
                                </>
                            }
                        />

                        <SystemOverviewCard
                            icon={Activity}
                            title="Today Summary"
                            value={`${overview.irrigationPlanned} planned`}
                            description={`${overview.completedToday} completed`}
                        />

                        <SystemOverviewCard
                            icon={Droplets}
                            title="Water Usage"
                            value={`${overview.waterUsedToday} L`}
                            description={`vs average ${overview.waterDelta}`}
                        />

                        <SystemOverviewCard
                            icon={CloudRain}
                            title="Weather Impact"
                            value={overview.weatherAdjustment}
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
                        {currentTasks.map(task => (
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
                        {alerts.map(alert => (
                            <AlertItem key={alert.id} alert={alert} />
                        ))}
                    </Stack>
                </GlassPanelSection>

                {/* SECTION 4 - UPCOMING TASKS */}
                <Grid
                    templateColumns={{ base: "1fr", xl: "1fr 1fr" }}
                    gap={8}
                >
                    <TodaysActivityCard items={todaysActivity} />
                    <WeatherWaterSummaryCard data={weatherWaterData} />
                </Grid>

                {/* SECTION 5 - ZONES STATUS */}
                <ZonesGridSection zones={zones} />

                {/* SECTION 6 - WEATHER FORECAST */}
                <WeatherForecastSection data={weatherForecastData} />


            </Stack>
        </Box>
    )
}
