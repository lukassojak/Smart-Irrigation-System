import { Box, Text } from "@chakra-ui/react"
import ReactApexChart from "react-apexcharts"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"

export default function AnomalyHeatmapSection({ anomalies }) {

    // ---- Transform data ----

    const zoneIds = [...new Set(
        anomalies.flatMap(day =>
            day.anomalies_list.map(a => a.zone_id)
        )
    )].sort((a, b) => a - b)

    const dates = anomalies.map(d => d.date)

    const series = zoneIds.map(zoneId => ({
        name: `Zone ${zoneId}`,
        data: dates.map(date => {
            const day = anomalies.find(d => d.date === date)
            const count = day.anomalies_list
                .filter(a => a.zone_id === zoneId)
                .length

            return {
                x: date.slice(5), // Show MM-DD
                y: count
            }
        })
    }))

    const options = {
        chart: {
            type: "heatmap",
            toolbar: { show: false }
        },
        dataLabels: {
            enabled: false
        },
        colors: ["#319795"],
        plotOptions: {
            heatmap: {
                shadeIntensity: 0.6,
                radius: 4,
                colorScale: {
                    ranges: [
                        { from: 0, to: 0, color: "#EDF2F7", name: "none" },
                        { from: 1, to: 1, color: "#FBD38D", name: "low" },
                        { from: 2, to: 2, color: "#F6AD55", name: "medium" },
                        { from: 3, to: 100, color: "#E53E3E", name: "high" }
                    ]
                }
            }
        },
        xaxis: {
            type: "category",
            labels: {
                style: {
                    fontSize: "12px"
                }
            }
        },
        yaxis: {
            labels: {
                style: {
                    fontSize: "12px"
                }
            }
        },
        tooltip: {
            y: {
                formatter: val => `${val} anomalies`
            }
        }
    }

    return (
        <GlassPanelSection
            title="Anomaly Heatmap"
            description="Anomaly frequency per zone over the last 12 days"
        >
            <Box>
                <ReactApexChart
                    options={options}
                    series={series}
                    type="heatmap"
                    height={350}
                />
            </Box >
        </GlassPanelSection >
    )
}