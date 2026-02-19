import { useState } from "react"
import {
    Box,
    Stack,
    Grid,
    Text,
    NativeSelect,
    Input,
    Button,
    VStack,
    HStack,
    Badge
} from "@chakra-ui/react"
import { Droplets } from "lucide-react"

import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import CurrentTaskCard from "../components/CurrentTaskCard"
import SelectableZoneCard from "../components/SelectableZoneCard"

export default function ManualControlPage() {

    const activeTasks = [
        {
            id: "1",
            zoneName: "South Lawn",
            progress: 35,
            currentVolume: 4,
            targetVolume: 12,
            remainingMinutes: 6,
            mode: "manual" // manual | automatic
        },
        {
            id: "2",
            zoneName: "Greenhouse",
            progress: 60,
            currentVolume: 8,
            targetVolume: 14,
            remainingMinutes: 3,
            mode: "automatic"
        }
    ]

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

    const [selectedZone, setSelectedZone] = useState(null)

    return (
        <Box>

            <GlassPageHeader
                title="Manual Control"
                subtitle="Override automatic irrigation"
            />

            <Stack gap={8} p={8}>

                {/* SECTION 1 – Start Manual */}
                <GlassPanelSection
                    title="Start Manual Irrigation"
                    description="Select zone and parameters to start immediate irrigation"
                >
                    <Grid
                        templateColumns={{ base: "1fr", xl: "2fr 1fr" }}
                        gap={8}
                    >

                        {/* Zone Selection */}
                        <Grid
                            templateColumns={{
                                base: "1fr",
                                md: "1fr 1fr"
                            }}
                            gap={4}
                        >
                            {zones.map(zone => (
                                <SelectableZoneCard
                                    key={zone.id}
                                    zone={zone}
                                    selected={selectedZone === zone.id}
                                    onClick={() =>
                                        zone.online && zone.status !== "error" &&
                                        setSelectedZone(zone.id)
                                    }
                                />
                            ))}
                        </Grid>

                        {/* Parameters */}
                        <VStack align="stretch" gap={4}>

                            <Text fontSize="sm" color="gray.600">
                                Mode
                            </Text>

                            <NativeSelect.Root>
                                <NativeSelect.Field>
                                    <option value="volume">By Volume (L)</option>
                                    <option value="time">By Duration (min)</option>
                                </NativeSelect.Field>
                                <NativeSelect.Indicator />
                            </NativeSelect.Root>

                            <Text fontSize="sm" color="gray.600">
                                Value
                            </Text>

                            <Input
                                placeholder="Enter value"
                                type="number"
                                isDisabled={!selectedZone}
                            />

                            <Button
                                colorPalette="orange"
                                variant="solid"
                                isDisabled={!selectedZone}
                            >
                                Start Manual Irrigation
                            </Button>

                            <Text fontSize="xs" color="gray.500">
                                Manual irrigation overrides scheduled automation.
                            </Text>

                        </VStack>

                    </Grid>


                </GlassPanelSection>

                {/* SECTION 2 – Active Irrigation */}
                <GlassPanelSection
                    title="Active Irrigation Tasks"
                    description="Currently running irrigation sessions"
                >
                    <Stack gap={6}>
                        {activeTasks.map(task => (
                            <Box key={task.id}>
                                {task.mode === "manual" && (
                                    <HStack mb={2}>
                                        <Badge
                                            size="sm"
                                            colorPalette="orange"
                                            variant="subtle"
                                        >
                                            Manual
                                        </Badge>
                                    </HStack>
                                )}
                                <CurrentTaskCard task={task} />
                            </Box>
                        ))}
                    </Stack>
                </GlassPanelSection>
            </Stack>

        </Box>
    )
}
