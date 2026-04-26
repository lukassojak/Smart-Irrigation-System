import {
    Box,
    Text,
    HStack,
    Badge,
    Stack,
    SimpleGrid,
} from "@chakra-ui/react"

export default function PerPlantAllocationCard({
    plantName,
    targetVolumeLiters,
    actualVolumeLiters,
    baseVolumeLiters,
    assignedDrippers = [],
}) {
    const hasVolumeComparison =
        Number.isFinite(targetVolumeLiters) && Number.isFinite(actualVolumeLiters)

    const diffPercent =
        hasVolumeComparison && targetVolumeLiters > 0
            ? ((actualVolumeLiters - targetVolumeLiters) / targetVolumeLiters) * 100
            : 0

    const hasBaseVolume = Number.isFinite(baseVolumeLiters)

    return (
        <Box
            p={5}
            borderRadius="xl"
            borderWidth="1px"
            borderColor="border.subtle"
            bg="bg.panel"
            boxShadow="sm"
        >
            <Stack gap={4}>
                <Text fontWeight="medium">
                    🌱 {plantName || "Unnamed plant"}
                </Text>

                {hasVolumeComparison && (
                    <SimpleGrid columns={2} gap={4} alignItems="baseline">
                        <Stack>
                            <Text fontSize="sm" color="fg.muted">
                                Target volume
                            </Text>
                            <Text fontSize="lg" color="fg.subtle" fontWeight="semibold">
                                {targetVolumeLiters.toFixed(2)} L
                            </Text>
                        </Stack>
                        <Stack>
                            <Text fontSize="sm" color="fg.muted" mt={2}>
                                Actual volume
                            </Text>
                            <HStack>
                                <Text fontSize="lg" fontWeight="semibold">
                                    {actualVolumeLiters.toFixed(2)} L
                                </Text>
                                <Badge colorPalette={diffPercent === 0 ? "gray" : "orange"}>
                                    {diffPercent > 0 ? "+" : ""}
                                    {diffPercent.toFixed(0)}%
                                </Badge>
                            </HStack>
                        </Stack>
                    </SimpleGrid>
                )}

                {hasBaseVolume && (
                    <Stack gap={1}>
                        <Text fontSize="sm" color="fg.muted">
                            Base volume
                        </Text>
                        <Text fontSize="lg" fontWeight="semibold">
                            {baseVolumeLiters.toFixed(2)} L
                        </Text>
                    </Stack>
                )}

                <Stack>
                    <Text fontSize="sm" color="fg.muted">
                        Assigned drippers
                    </Text>
                    <HStack wrap="wrap" gap={4}>
                        {assignedDrippers.map((dripper, index) => (
                            <HStack gap={1} key={index}>
                                <Text fontSize="sm" color="fg.muted">
                                    {dripper.count}×
                                </Text>
                                <Badge colorPalette="teal" variant="subtle">
                                    {dripper.flow_rate_lph} L/h
                                </Badge>
                            </HStack>
                        ))}
                    </HStack>
                </Stack>
            </Stack>
        </Box>
    )
}
