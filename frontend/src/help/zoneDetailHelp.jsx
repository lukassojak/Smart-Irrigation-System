export const zoneDetailHelp = [
    {
        id: "zone-overview",
        title: "What is a Zone?",
        description: (
            <>
                A zone represents a <strong>specific area in your irrigation system that is managed independently</strong>.
                Each zone can have its own configuration, including the type and number of emitters, irrigation mode,
                and scheduling.
                <br /><br />
                Each zone is controlled by a relay valve connected to a specific pin on your irrigation controller.
            </>
        )
    },
    {
        id: "irrigation-mode",
        title: "Understanding Irrigation Modes",
        description: (
            <>
                Irrigation mode defines <strong>how the base water volume is calculated</strong> for this zone.
                <br /><br />
                <strong>Even Area</strong> mode is suitable for uniform areas such as lawns or garden beds.
                The base volume is calculated from:
                <ul>
                    <li>zone area (m²)</li>
                    <li>target water depth (mm)</li>
                </ul>
                <br />
                <strong>Per Plant</strong> mode is designed for zones with individual plants (e.g. pots or mixed crops).
                In this mode, the zone uses a predefined base target volume and distributes water based on plant-level
                emitter configuration.
            </>
        )
    },
    {
        id: "frequency-scheduling",
        title: "Frequency & Scheduling",
        description: (
            <>
                Frequency settings define <strong>how often this zone is allowed to irrigate</strong>.
                <br /><br />
                When dynamic intervals are enabled, the node decides the irrigation day dynamically between the minimum
                and maximum interval based on:
                <strong>weather conditions</strong>, <strong>calculated irrigation volume</strong>, and a
                <strong>minimum volume threshold</strong>.
                <br /><br />
                The timeline below visualizes the allowed irrigation window and helps you understand when irrigation
                may be skipped or delayed.
            </>
        )
    },
    {
        id: "weather-fallback",
        title: "Weather Data Fallback Strategy",
        description: (
            <>
                Weather data is critical for adaptive irrigation, but it may occasionally be unavailable. Depending on
                configuration, the system can respond to missing or outdated weather data in different ways:
                <ul>
                    <li>use cached data</li>
                    <li>fall back to base volume</li>
                    <li>apply a reduced volume</li>
                    <li>or skip irrigation entirely</li>
                </ul>
            </>
        )
    },
    {
        id: "carry-over",
        title: "Carry-over Volume & Threshold",
        description: (
            <>
                Sometimes the calculated irrigation volume is too small to be meaningful.
                <br /><br />
                If the volume is below the configured threshold, irrigation is skipped. When
                <strong>carry-over volume</strong> is enabled, the skipped volume is <strong>accumulated</strong> and
                added to the next irrigation cycle.
                <br /><br />
                This prevents frequent micro-irrigation cycles and helps maintain stable soil moisture. Disabling
                carry-over may lead to under-watering and is generally not recommended.
            </>
        )
    },
    {
        id: "local-correction",
        title: "Local Correction Factors",
        description: (
            <>
                Correction factors fine-tune how strongly different weather conditions affect this zone.
                <br /><br />
                They are applied <strong>after</strong> the base irrigation volume is calculated.
                <ul>
                    <li><strong>Solar</strong> – adjusts sensitivity to sunlight</li>
                    <li><strong>Rain</strong> – adjusts impact of rainfall</li>
                    <li><strong>Temperature</strong> – adjusts response to air temperature</li>
                </ul>
                <br />
                These values allow compensating for microclimate differences between zones (e.g. shade, roof coverage,
                or soil type).
            </>
        )
    },
    {
        id: "emitters",
        title: "Emitters Configuration",
        description: (
            <>
                Emitters define how water is delivered to plants and are used to calculate irrigation volumes.
            </>
        )
    },
    {
        id: "review",
        title: "Review & Diagnostics",
        description: (
            <>
                This section shows the computed configuration and helps validate that the zone behaves as expected.
            </>
        )
    }
]