import {
    Box,
    Grid,
    Stack,
    Text,
    VStack,
    HStack,
    Badge
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
    AreaChart,
    Area
} from "recharts"

import { useOutletContext } from "react-router-dom"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import StatisticsOverviewCard from "../components/StatisticsOverviewCard"
import AnomalyHeatmapSection from "../components/AnomalyHeatmapSection"

export default function StatisticsPage() {

    const statsData = {
        kpis: {
            totalWater: 12450,
            avgDailyWater: 356,
            irrigationRuns: 84,
            efficiency: 92,
            weatherAdjustments: -12,
            autoRuns: 63,
            manualRuns: 21,
            skippedRuns: 12,
            interruptedRuns: 3,
            avgDuration: 480,
            avgAdjustment: -8,
            waterSavedVsStatic: 14
        },
        waterTrend: [
            { date: "Mon", water: 120 },
            { date: "Tue", water: 140 },
            { date: "Wed", water: 110 },
            { date: "Thu", water: 160 },
            { date: "Fri", water: 130 },
            { date: "Sat", water: 125 },
            { date: "Sun", water: 150 }
        ],
        zoneUsage: [
            { zone: "South Lawn", water: 320 },
            { zone: "Greenhouse", water: 210 },
            { zone: "Orchard", water: 420 },
            { zone: "North Lawn", water: 180 }
        ],
        correlation: [
            { date: "Mon", weather: -10, water: 150 },
            { date: "Tue", weather: 5, water: 120 },
            { date: "Wed", weather: 12, water: 95 },
            { date: "Thu", weather: -8, water: 170 },
            { date: "Fri", weather: 2, water: 130 }
        ],
        heatmap: [
            { hour: 0, Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 0, Sat: 0, Sun: 0 },
            { hour: 6, Mon: 12, Tue: 15, Wed: 0, Thu: 18, Fri: 10, Sat: 0, Sun: 0 },
            { hour: 9, Mon: 25, Tue: 20, Wed: 15, Thu: 30, Fri: 22, Sat: 10, Sun: 5 },
            { hour: 12, Mon: 30, Tue: 25, Wed: 20, Thu: 35, Fri: 28, Sat: 22, Sun: 18 },
            { hour: 18, Mon: 50, Tue: 45, Wed: 40, Thu: 60, Fri: 55, Sat: 48, Sun: 52 },
            { hour: 20, Mon: 40, Tue: 35, Wed: 30, Thu: 50, Fri: 45, Sat: 38, Sun: 42 },
            { hour: 22, Mon: 20, Tue: 15, Wed: 10, Thu: 25, Fri: 18, Sat: 12, Sun: 8 }
        ],
        adjustmentImpact: [
            { date: "Mon", base: 150, adjusted: 120 },
            { date: "Tue", base: 150, adjusted: 165 },
            { date: "Wed", base: 150, adjusted: 135 },
            { date: "Thu", base: 150, adjusted: 180 },
            { date: "Fri", base: 150, adjusted: 130 },
            { date: "Sat", base: 150, adjusted: 125 },
            { date: "Sun", base: 150, adjusted: 150 }
        ],
        anomalies: [
            {
                date: "2025-06-01", anomalies_list: [
                    { time: "14:30", zone_id: 1, severity: "high", description: "Unexpectedly high water usage in South Lawn", resolved: false },
                    { time: "16:00", zone_id: 3, severity: "medium", description: "Skipped irrigation run in Greenhouse", resolved: true }
                ]
            },
            {
                date: "2025-06-02", anomalies_list: [
                    { time: "09:15", zone_id: 2, severity: "low", description: "Slightly higher water usage in Orchard", resolved: false }
                ]
            },
            {
                date: "2025-06-03", anomalies_list: []
            },
            {
                date: "2025-06-04", anomalies_list: []
            },
            {
                date: "2025-06-05", anomalies_list: [
                    { time: "18:45", zone_id: 1, severity: "medium", description: "Interrupted irrigation run in South Lawn due to low pressure", resolved: true }
                ]
            },
            {
                date: "2025-06-06", anomalies_list: []
            },
            {
                date: "2025-06-07", anomalies_list: [
                    { time: "12:00", zone_id: 4, severity: "high", description: "Significant water usage spike in North Lawn", resolved: false }
                ]
            },
            {
                date: "2025-06-08", anomalies_list: []
            },
            {
                date: "2025-06-09", anomalies_list: []
            },
            {
                date: "2025-06-10", anomalies_list: [
                    { time: "20:30", zone_id: 2, severity: "medium", description: "Missed irrigation run in Orchard due to sensor failure", resolved: true },
                    { time: "21:00", zone_id: 3, severity: "low", description: "Slightly higher water usage in Greenhouse during evening hours", resolved: false },
                    { time: "21:15", zone_id: 2, severity: "medium", description: "Missed irrigation run in Orchard due to sensor failure", resolved: true },
                    { time: "21:30", zone_id: 1, severity: "medium", description: "Interrupted irrigation run in South Lawn due to power fluctuation", resolved: true }
                ]
            },
            {
                date: "2025-06-11", anomalies_list: []
            },
            {
                date: "2025-06-12", anomalies_list: [
                    { time: "08:00", zone_id: 3, severity: "low", description: "Slightly lower water usage in Greenhouse", resolved: false }
                ]
            },
            {
                date: "2025-06-13", anomalies_list: []
            },
            {
                date: "2025-06-14", anomalies_list: [
                    { time: "15:00", zone_id: 1, severity: "high", description: "Unexpectedly high water usage in South Lawn during afternoon hours", resolved: false },
                    { time: "17:00", zone_id: 4, severity: "medium", description: "Skipped irrigation run in North Lawn due to communication error", resolved: true }
                ]
            },
            {
                date: "2025-06-15", anomalies_list: [
                    { time: "19:00", zone_id: 1, severity: "high", description: "Unexpectedly high water usage in South Lawn during evening hours", resolved: false },
                    { time: "19:00", zone_id: 1, severity: "high", description: "Unexpectedly high water usage in South L{awn during evening hours", resolved: false },
                    { time: "19:15", zone_id: 1, severity: "high", description: "Unexpectedly high water usage in South Lawn during evening hours", resolved: false },
                    { time: "19:30", zone_id: 4, severity: "medium", description: "Skipped irrigation run in North Lawn due to communication error", resolved: true },
                    { time: "20:00", zone_id: 2, severity: "low", description: "Slightly higher water usage in Orchard during afternoon hours", resolved: false },
                    { time: "20:30", zone_id: 4, severity: "medium", description: "Skipped irrigation run in North Lawn due to communication error", resolved: true }
                ]
            },
            {
                date: "2025-06-16", anomalies_list: [
                    { time: "07:45", zone_id: 1, severity: "high", description: "Unexpectedly high water usage in South Lawn during early morning hours", resolved: false },
                    { time: "08:30", zone_id: 4, severity: "medium", description: "Skipped irrigation run in North Lawn due to communication error", resolved: true },
                ]
            },
            {
                date: "2025-06-17", anomalies_list: [
                    { time: "14:00", zone_id: 4, severity: "low", description: "Slightly higher water usage in Greenhouse during afternoon hours", resolved: false }
                ]
            },
            {
                date: "2025-06-18", anomalies_list: [
                    { time: "10:30", zone_id: 4, severity: "medium", description: "Skipped irrigation run in North Lawn due to communication error", resolved: true }
                ]
            },
            {
                date: "2025-06-19", anomalies_list: []
            },
            {
                date: "2025-06-20", anomalies_list: [
                    { time: "17:45", zone_id: 2, severity: "low", description: "Slightly higher water usage in Orchard during afternoon hours", resolved: false }
                ]
            }
        ]

    }

    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    return (
        <Box>

            <GlassPageHeader
                title="Statistics"
                subtitle="Irrigation analytics and performance overview"
                showMobileMenuButton={isMobile}
                onMobileMenuClick={openMobileSidebar}
            />

            <Stack gap={8} p={8}>

                {/* KPI OVERVIEW */}
                <GlassPanelSection
                    title="Overview"
                    description="Aggregate performance metrics for the last 30 days"
                >
                    <Grid
                        templateColumns={{
                            base: "1fr",
                            md: "1fr 1fr",
                            xl: "1fr 1fr 1fr 1fr"
                        }}
                        gap={6}
                    >
                        <StatisticsOverviewCard
                            label="Total Water"
                            value={`${statsData.kpis.totalWater} L`}
                            description="Total water used in the last 30 days"
                        />
                        <StatisticsOverviewCard
                            label="Avg Daily"
                            value={`${statsData.kpis.avgDailyWater} L`}
                            description="Over the last 30 days"
                            footer={<Badge colorPalette="teal">+5% vs previous month</Badge>}
                        />
                        <StatisticsOverviewCard
                            label="Irrigation Runs"
                            value={statsData.kpis.irrigationRuns}
                            description="Total irrigation runs executed within all zones"
                        />
                        <StatisticsOverviewCard
                            label="Water Saved"
                            value={`${statsData.kpis.waterSavedVsStatic}%`}
                            description="Compared to a static schedule without adjustments"
                        />
                        <StatisticsOverviewCard label="Auto Runs" value={statsData.kpis.autoRuns} />
                        <StatisticsOverviewCard label="Manual Runs" value={statsData.kpis.manualRuns} />
                        <StatisticsOverviewCard label="Skipped" value={statsData.kpis.skippedRuns} />
                        <StatisticsOverviewCard label="Interrupted" value={statsData.kpis.interruptedRuns} />
                    </Grid>
                </GlassPanelSection>

                {/* WATER TREND */}
                <GlassPanelSection
                    title="Water Usage Trend"
                    description="Daily water consumption (7-day rolling window)"
                >
                    <ResponsiveContainer width="100%" height={300}>
                        <LineChart data={statsData.waterTrend}>
                            <XAxis dataKey="date" />
                            <YAxis />
                            <Tooltip />
                            <Line
                                type="monotone"
                                dataKey="water"
                                stroke="#319795"
                                strokeWidth={2}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </GlassPanelSection>
            </Stack>

            <Grid
                templateColumns={{ base: "1fr", xl: "1fr 1fr" }}
                gap={8}
                p={8}
            >
                {/* CORRELATION */}
                <GlassPanelSection
                    title="Weather vs Irrigation"
                    description="Correlation between weather index and water usage"
                >
                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={statsData.correlation}>
                            <XAxis dataKey="date" />
                            <YAxis />
                            <Tooltip />
                            <Area
                                type="monotone"
                                dataKey="water"
                                stroke="#3182CE"
                                fill="#BEE3F8"
                            />
                            <Area
                                type="monotone"
                                dataKey="weather"
                                stroke="#DD6B20"
                                fill="#FBD38D"
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </GlassPanelSection>

                {/* ZONE DISTRIBUTION */}
                <GlassPanelSection
                    title="Zone Water Distribution"
                    description="Water usage per zone"
                >
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={statsData.zoneUsage}>
                            <XAxis dataKey="zone" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="water" fill="#319795" />
                        </BarChart>
                    </ResponsiveContainer>
                </GlassPanelSection>

                <GlassPanelSection
                    title="Hourly Irrigation Heatmap"
                    description="Water usage distribution across hours (7-day window)"
                >
                    <ResponsiveContainer width="100%" height={350}>
                        <BarChart data={statsData.heatmap}>
                            <XAxis dataKey="hour" />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="Mon" stackId="a" fill="#319795" />
                            <Bar dataKey="Tue" stackId="a" fill="#2C7A7B" />
                            <Bar dataKey="Wed" stackId="a" fill="#285E61" />
                            <Bar dataKey="Thu" stackId="a" fill="#81E6D9" />
                            <Bar dataKey="Fri" stackId="a" fill="#38B2AC" />
                            <Bar dataKey="Sat" stackId="a" fill="#4FD1C5" />
                            <Bar dataKey="Sun" stackId="a" fill="#B2F5EA" />
                        </BarChart>
                    </ResponsiveContainer>
                </GlassPanelSection>
                {/* Get only last 10 days with anomalies */}
                <AnomalyHeatmapSection anomalies={statsData.anomalies.slice(-12)} />
            </Grid>
        </Box>
    )
}