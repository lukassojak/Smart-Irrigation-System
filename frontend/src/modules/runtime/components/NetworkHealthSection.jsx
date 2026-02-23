import {
    Box,
    Grid,
    Stack,
    VStack,
    HStack,
    Text,
    Badge,
    Progress
} from "@chakra-ui/react"
import {
    Router,
    Activity,
    Wifi,
    Timer,
    Signal
} from "lucide-react"

import GlassPanelSection from "../../../components/layout/GlassPanelSection"

export default function NetworkHealthSection({ data }) {

    return (
        <GlassPanelSection
            title="Network Health"
            description="MQTT broker and node connectivity monitoring"
        >
            <Stack gap={8}>

                {/* MQTT Broker Status */}
                <Grid
                    templateColumns={{ base: "1fr", xl: "1fr 1fr" }}
                    gap={8}
                >

                    <VStack align="stretch" gap={4}>
                        <HStack justify="space-between">
                            <HStack>
                                <Router size={16} />
                                <Text fontWeight="600">
                                    MQTT Broker
                                </Text>
                            </HStack>

                            <Badge
                                colorPalette={data.broker.online ? "green" : "red"}
                                variant="subtle"
                            >
                                {data.broker.online ? "online" : "offline"}
                            </Badge>
                        </HStack>

                        <Text fontSize="sm" color="gray.600">
                            Uptime: {data.broker.uptime}
                        </Text>

                        <Text fontSize="sm" color="gray.600">
                            Connected nodes: {data.broker.connectedNodes} / {data.broker.totalNodes}
                        </Text>

                        <Text fontSize="sm" color="gray.600">
                            Messages/sec: {data.broker.msgPerSec}
                        </Text>
                    </VStack>

                    {/* Latency */}
                    <VStack align="stretch" gap={4}>
                        <HStack>
                            <Timer size={14} />
                            <Text fontSize="sm" fontWeight="600">
                                Average Latency
                            </Text>
                        </HStack>

                        <Progress.Root
                            value={data.latency.avg}
                            max={200}
                            height="8px"
                            borderRadius="md"
                        >
                            <Progress.Track bg="gray.100">
                                <Progress.Range bg="teal.500" />
                            </Progress.Track>
                        </Progress.Root>

                        <Text fontSize="xs" color="gray.500">
                            {data.latency.avg} ms (max {data.latency.max} ms)
                        </Text>
                    </VStack>

                </Grid>

                {/* Signal Distribution */}
                <Box>
                    <HStack mb={4}>
                        <Signal size={14} />
                        <Text fontSize="sm" fontWeight="600">
                            WiFi Signal Distribution
                        </Text>
                    </HStack>

                    <Grid
                        templateColumns={{ base: "1fr", md: "1fr 1fr 1fr" }}
                        gap={4}
                    >

                        <SignalBar
                            label="Strong (-60 dBm)"
                            value={data.signal.strong}
                            total={data.signal.total}
                            color="teal.500"
                        />

                        <SignalBar
                            label="Medium (-60 to -75)"
                            value={data.signal.medium}
                            total={data.signal.total}
                            color="orange.400"
                        />

                        <SignalBar
                            label="Weak (< -75)"
                            value={data.signal.weak}
                            total={data.signal.total}
                            color="red.400"
                        />

                    </Grid>
                </Box>

            </Stack>
        </GlassPanelSection>
    )
}

function SignalBar({ label, value, total, color }) {
    const percent = total > 0 ? (value / total) * 100 : 0

    return (
        <VStack
            align="stretch"
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={4}
            boxShadow="0 4px 14px rgba(15,23,42,0.05)"
        >
            <Text fontSize="sm" fontWeight="500">
                {label}
            </Text>

            <Progress.Root
                value={percent}
                height="6px"
                borderRadius="md"
            >
                <Progress.Track bg="gray.100">
                    <Progress.Range bg={color} />
                </Progress.Track>
            </Progress.Root>

            <Text fontSize="xs" color="gray.500">
                {value} nodes ({percent.toFixed(0)}%)
            </Text>
        </VStack>
    )
}