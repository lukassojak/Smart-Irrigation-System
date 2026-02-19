import {
    Box,
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

export default function WeatherWaterSummaryCard({ data }) {

    return (
        <GlassPanelSection
            title="Weather vs Water Usage"
            description={`Rolling ${data.windowDays}-day comparison`}
        >
            <VStack align="stretch" gap={6}>

                {/* Chart */}
                <Box
                    height="260px"
                    bg="rgba(255,255,255,0.75)"
                    border="1px solid rgba(56,178,172,0.06)"
                    borderRadius="lg"
                    p={2}
                >
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data.data}>

                            <CartesianGrid
                                stroke="rgba(15,23,42,0.06)"
                                vertical={false}
                            />

                            <XAxis
                                dataKey="date"
                                stroke="#94A3B8"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />

                            {/* Left axis – Water */}
                            <YAxis
                                yAxisId="left"
                                stroke="#319795"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />

                            {/* Right axis – Weather deviation */}
                            <YAxis
                                yAxisId="right"
                                orientation="right"
                                stroke="#64748B"
                                fontSize={12}
                                tickLine={false}
                                axisLine={false}
                            />

                            <Tooltip
                                contentStyle={{
                                    background: "rgba(255,255,255,0.95)",
                                    border: "1px solid rgba(56,178,172,0.08)",
                                    borderRadius: "8px",
                                    boxShadow: "0 8px 24px rgba(15,23,42,0.08)"
                                }}
                            />

                            <Legend
                                wrapperStyle={{
                                    fontSize: "12px"
                                }}
                            />

                            <Bar
                                yAxisId="left"
                                dataKey="water"
                                name="Water (L)"
                                fill="#319795"
                                radius={[4, 4, 0, 0]}
                            />

                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey="weather"
                                name="Weather deviation (%)"
                                stroke="#64748B"
                                strokeWidth={2}
                                dot={{ r: 3 }}
                                activeDot={{ r: 5 }}
                            />

                        </ComposedChart>
                    </ResponsiveContainer>
                </Box>

                {/* Summary metrics */}
                <HStack justify="space-between">

                    <VStack align="start" spacing={1}>
                        <Text fontSize="sm" color="gray.600">
                            Avg Daily Water
                        </Text>
                        <Text fontWeight="600">
                            {data.avgWater} L
                        </Text>
                    </VStack>

                    <VStack align="end" spacing={1}>
                        <Text fontSize="sm" color="gray.600">
                            Avg Weather Deviation
                        </Text>
                        <HStack>
                            <Text
                                fontWeight="600"
                                color={
                                    data.avgWeather > 0
                                        ? "orange.500"
                                        : "teal.600"
                                }
                            >
                                {data.avgWeather > 0 ? "+" : ""}
                                {data.avgWeather}%
                            </Text>
                            <Text
                                size="xs"
                                color="gray.500"
                                variant="subtle"
                            >
                                vs standard
                            </Text>
                        </HStack>
                    </VStack>

                </HStack>

            </VStack>
        </GlassPanelSection>
    )
}
