export const wizardHelp = [
    {
        step: "basic",
        title: "What is a zone?",
        description: (
            <>
                A <strong>zone</strong> represents a single, independently controlled
                irrigation area connected to one physical valve.
                <br /><br />
                Each zone defines:
                <ul>
                    <li>how much water should be applied (<strong>base volume</strong>)</li>
                    <li>how often irrigation is allowed (<strong>frequency rules</strong>)</li>
                    <li>how weather influences irrigation (<strong>corrections</strong>)</li>
                </ul>
                <br />
                A zone is always attached to a specific <strong>node</strong> and uses
                one <strong>relay pin</strong> to control its valve.
            </>
        )
    },
    {
        step: "mode",
        title: "Irrigation Mode",
        description: (
            <>
                Irrigation mode defines <strong>how the base irrigation volume is calculated</strong> for this zone.
                <br /><br />
                <strong>Even Area</strong> mode is designed for uniform areas such as lawns
                or garden beds. The base volume is calculated from:
                <ul>
                    <li>zone area (m²)</li>
                    <li>target irrigation depth (mm)</li>
                </ul>
                <br />
                <strong>Per Plant</strong> mode is intended for zones with individual plants.
                In this mode, a predefined <strong>base target volume</strong> is distributed
                according to plant-level emitter configuration.
            </>
        )
    },
    {
        step: "irrigation",
        title: "Irrigation targets",
        description: (
            <>
                Irrigation targets define the <strong>base amount of water</strong> applied
                during one irrigation cycle, before any weather-based adjustments.
                <br /><br />
                This value represents an <strong>ideal reference volume</strong>.
                The final applied volume may be:
                <ul>
                    <li>reduced by rainfall</li>
                    <li>increased during hot or sunny conditions</li>
                    <li>skipped entirely if below the configured threshold</li>
                </ul>
                <br />
                All further behavior is calculated relative to this base target.
            </>
        )
    },
    {
        step: "emitters",
        title: "Emitters & Hardware Layout",
        description: (
            <>
                Emitters describe the <strong>physical irrigation
                    hardware</strong> used in this zone.
                <br /><br />
                Each emitter defines:
                <ul>
                    <li><strong>type</strong> (e.g. dripper, sprinkler)</li>
                    <li><strong>flow rate</strong> (liters per hour)</li>
                    <li><strong>count</strong> (number of identical emitters)</li>
                </ul>
                <br />
                The system uses this information to estimate irrigation duration
                and to validate hydraulic limits.
            </>
        )
    },
    {
        step: "behavior",
        title: "Frequency & Scheduling",
        description: (
            <>
                Frequency settings define <strong>when irrigation is allowed to occur</strong>.
                <br /><br />
                Irrigation is permitted only within a window defined by:
                <ul>
                    <li><strong>minimum interval</strong> (earliest possible day)</li>
                    <li><strong>maximum interval</strong> (latest allowed day)</li>
                </ul>
                <br />
                When <strong>dynamic interval</strong> is enabled, the system selects
                the optimal irrigation day inside this window based on:
                <ul>
                    <li>weather conditions</li>
                    <li>calculated irrigation volume</li>
                    <li>volume threshold rules</li>
                </ul>
            </>
        )
    },
    {
        step: "behavior",
        title: "Carry-over & Threshold",
        description: (
            <>
                Very small irrigation volumes are often ineffective.
                <br /><br />
                If the calculated volume is below the configured
                <strong>irrigation volume threshold</strong>, irrigation is skipped.
                <br /><br />
                When <strong>carry-over volume</strong> is enabled, the skipped volume
                is <strong>accumulated</strong> and added to the next irrigation cycle.
                <br /><br />
                This prevents frequent micro-irrigation and helps maintain
                stable soil moisture over time.
            </>
        )
    },
    {
        step: "behavior",
        title: "Weather Corrections",
        description: (
            <>
                Local correction factors adjust how strongly weather data influences
                this specific zone.
                <br /><br />
                They are applied <strong>after</strong> the base irrigation volume
                is calculated.
                <ul>
                    <li><strong>Solar</strong> – sensitivity to sunlight</li>
                    <li><strong>Rain</strong> – impact of rainfall</li>
                    <li><strong>Temperature</strong> – response to air temperature</li>
                </ul>
                <br />
                These factors allow compensating for <strong>microclimates</strong>,
                such as shaded areas, covered zones, or different soil types.
            </>
        )
    },
    {
        step: "behavior",
        title: "Weather Data Fallback",
        description: (
            <>
                Adaptive irrigation relies on fresh weather data, but data may
                occasionally be unavailable.
                <br /><br />
                The fallback strategy defines how the system behaves when:
                <ul>
                    <li>weather data is missing</li>
                    <li>cached data is expired</li>
                    <li>data cannot be refreshed</li>
                </ul>
                <br />
                Possible strategies include using cached values,
                falling back to base volume, or skipping irrigation
                to avoid unsafe behavior.
            </>
        )
    }
]