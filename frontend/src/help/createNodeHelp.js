export const createNodeHelp = [
    {
        id: "what-is-node",
        title: "What is a Node?",
        description:
            "A node represents a physical irrigation controller responsible for managing one or more irrigation zones. Each node defines global behavior such as automation schedule, safety irrigation limits, and batching strategy. Zones created under a node inherit these settings and apply them during irrigation cycles."
    },
    {
        id: "automation-scheduling",
        title: "How does automation & scheduling work?",
        description:
            "When automation is enabled, the node evaluates irrigation needs once per day at the scheduled time. Based on weather data, zone configuration, and system limits, the node decides which zones should be irrigated and how much water should be applied."
    },
    {
        id: "batch-strategy",
        title: "What is Batch Strategy?",
        description:
            "The batch strategy defines how multiple irrigation zones are executed within one irrigation cycle. Sequential mode irrigates zones one after another, while concurrent mode allows multiple zones to run at the same time, depending on system limits and water flow capacity."
    },
    {
        id: "advanced-settings",
        title: "Do I need to configure advanced settings?",
        description:
            "Advanced settings are optional and provide finer control over irrigation behavior. Safe default values are applied upon node creation and can be modified later as needed."
    }
]

export const createNodeAdvancedHelp = [
    {
        id: "irrigation-limits",
        title: "How to configure irrigation limits?",
        description:
            "Irrigation limits define safe boundaries for how much water can be applied during a single irrigation cycle. These limits act as a protection layer when weather-based calculations would otherwise produce extremely low or high irrigation volumes."
    },
    {
        id: "water-supply-max-flow",
        title: "What is Water Supply Max Flow?",
        description:
            "This setting represents a physical limitation of your water supply connection. When multiple zones are irrigated concurrently, the system ensures that the total water flow does not exceed this limit. Leave this unset if your installation does not require flow-based restrictions."
    },
    {
        id: "weather-cache-settings",
        title: "What are weather cache settings?",
        description:
            "These settings control how often new weather data is fetched and how long it is considered valid. Longer cache durations improve system stability, while shorter intervals provide more up-to-date adjustments."
    },
    {
        id: "flow-control",
        title: "Flow control in batch strategy",
        description:
            "Enabling flow control helps manage water pressure when irrigating multiple zones concurrently. It dynamically adjusts valve openings to ensure the total flow remains within safe limits."
    }
]