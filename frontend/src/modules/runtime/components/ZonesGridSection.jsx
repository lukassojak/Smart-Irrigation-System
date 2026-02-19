import {
    Grid
} from "@chakra-ui/react"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import ZoneRuntimeCard from "./ZoneRuntimeCard"

const STATUS_PRIORITY = {
    irrigating: 1,
    idle: 2,
    error: 3,
    offline: 4
}

export default function ZonesGridSection({ zones }) {

    const sortedZones = [...zones].sort((a, b) => {
        return STATUS_PRIORITY[a.status] - STATUS_PRIORITY[b.status]
    })

    return (
        <GlassPanelSection
            title="Zones"
            description="Runtime status and quick controls"
        >
            <Grid
                templateColumns={{
                    base: "1fr",
                    md: "1fr 1fr"
                }}
                gap={6}
            >
                {sortedZones.map(zone => (
                    <ZoneRuntimeCard key={zone.id} zone={zone} />
                ))}
            </Grid>
        </GlassPanelSection>
    )
}
