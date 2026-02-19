import {
    Box,
    Grid,
    VStack,
    HStack,
    Text,
    Badge
} from "@chakra-ui/react"
import {
    ResponsiveContainer,
    ComposedChart,
    Bar,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend
} from "recharts"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"

export default function WeatherForecastSection({ data }) {

    const avgAdjustment =
        data.data.reduce((sum, d) => sum + d.adjustment, 0) /
        data.data.length

    let summaryText = ""
    let summaryColor = "gray"

    if (avgAdjustment < -5) {
        summaryText = `In the next ${data.forecastDays} days we expect reduced irrigation due to rain and cooler conditions.`
        summaryColor = "teal"
    } else if (avgAdjustment > 5) {
        summaryText = `In the next ${data.forecastDays} days higher temperatures may increase irrigation demand.`
        summaryColor = "orange"
    } else if (avgAdjustment > 15) {
        summaryText = `In the next ${data.forecastDays} days we expect significantly higher irrigation demand due to hot and dry conditions.`
        summaryColor = "red"
    } else {
        summaryText = `Irrigation demand is expected to remain relatively stable over the next ${data.forecastDays} days.`
        summaryColor = "gray"
    }

    return (
        <GlassPanelSection
            title="Weather Forecast"
            description={`Next ${data.forecastDays} days`}
        >
            <Grid
                templateColumns={{ base: "1fr", xl: "2fr 1fr" }}
                gap={8}
            >

                {/* Chart */}
                <Box
                    height="280px"
                    bg="rgba(255,255,255,0.75)"
                    border="1px solid rgba(56,178,172,0.06)"
                    borderRadius="lg"
                    p={4}
                >
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data.data}>

                            <CartesianGrid
                                stroke="rgba(15,23,42,0.06)"
                                vertical={false}
                            />

                            <XAxis
                                dataKey="day"
                                stroke="#94A3B8"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />

                            {/* Rain axis */}
                            <YAxis
                                yAxisId="rain"
                                stroke="#319795"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />

                            {/* Temperature axis */}
                            <YAxis
                                yAxisId="temp"
                                orientation="right"
                                stroke="#F59E0B"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />

                            {/* Adjustment axis */}
                            <YAxis
                                yAxisId="adj"
                                orientation="right"
                                hide
                            />

                            <Tooltip
                                contentStyle={{
                                    background: "rgba(255,255,255,0.95)",
                                    border: "1px solid rgba(56,178,172,0.08)",
                                    borderRadius: "8px",
                                    boxShadow: "0 8px 24px rgba(15,23,42,0.08)"
                                }}
                            />

                            <Legend wrapperStyle={{ fontSize: "12px" }} />

                            {/* Rain */}
                            <Bar
                                yAxisId="rain"
                                dataKey="rain"
                                name="Rain (mm)"
                                fill="#319795"
                                radius={[4, 4, 0, 0]}
                            />

                            {/* Temperature */}
                            <Line
                                yAxisId="temp"
                                type="monotone"
                                dataKey="temp"
                                name="Temperature (°C)"
                                stroke="#F6AD55"
                                strokeWidth={2}
                                dot={{ r: 2 }}
                            />

                            {/* Irrigation Adjustment */}
                            <Line
                                yAxisId="adj"
                                type="monotone"
                                dataKey="adjustment"
                                name="Predicted Adjustment (%)"
                                stroke="#64748B"
                                strokeDasharray="4 4"
                                strokeWidth={2}
                                dot={{ r: 3 }}
                            />

                        </ComposedChart>
                    </ResponsiveContainer>
                </Box>

                {/* Summary */}
                <VStack align="stretch" gap={4}>

                    {/* Irrigation Outlook */}
                    <Box
                        p={5}
                        bg="rgba(255,255,255,0.85)"
                        border="1px solid rgba(56,178,172,0.06)"
                        borderRadius="lg"
                    >
                        <VStack align="start" spacing={3}>
                            {/* Outlook Header */}
                            <Text fontSize="sm" fontWeight="600" color="gray.700">
                                Irrigation Outlook
                            </Text>

                            {/* use italics for the summary text */}
                            <Text fontSize="sm" color="gray.600" fontStyle="italic">
                                {summaryText}
                            </Text>
                        </VStack>
                    </Box>

                    {/* Rain metrics */}

                    <Metric
                        label="Today Rain"
                        value={`${data.summary.todayRain} mm`}
                    />

                    <Metric
                        label="Tomorrow Rain"
                        value={`${data.summary.tomorrowRain} mm`}
                    />

                </VStack>


            </Grid>
        </GlassPanelSection>
    )
}

function Metric({ label, value }) {
    return (
        <VStack align="start" gap={1}>
            <Text fontSize="sm" color="gray.600">
                {label}
            </Text>
            <Text fontWeight="600">
                {value}
            </Text>
        </VStack>
    )
}
