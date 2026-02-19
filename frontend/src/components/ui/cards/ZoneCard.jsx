// ZoneCardStructural.jsx
import { Box, Heading, Text, Stack, HStack, Badge } from "@chakra-ui/react"
import { Link } from "react-router-dom"
import { LimitedCorrectionIndicator } from "../../CorrectionIndicator"

import { LandPlot } from "lucide-react"

export default function ZoneCard({ nodeId, zone }) {
    return (
        <Box
            as={Link}
            to={`/configuration/nodes/${nodeId}/zones/${zone.id}`}
            borderRadius="lg"
            p={6}
            bg="rgba(255,255,255,0.92)"
            border="1px solid rgba(56,178,172,0.06)"
            boxShadow="0 4px 16px rgba(15,23,42,0.05)"
            transition="border-color 0.12s ease, box-shadow 0.12s ease"
            _hover={{
                borderColor: "teal.300",
                boxShadow: "0 8px 24px rgba(15,23,42,0.08)"
            }}
            textAlign="left"
        >
            <HStack align="stretch" spacing={6}>
                {/* Icon */}
                <Box
                    w="36px"
                    h="36px"
                    borderRadius="md"
                    bg="rgba(56,178,172,0.08)"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                >
                    <LandPlot size={20} color="#319795" />
                </Box>

                {/* Main content */}
                <Stack flex="1" spacing={2}>
                    <Heading size="md" fontWeight="600">
                        Zone #{zone.id}
                    </Heading>

                    <Text fontSize="sm" color="gray.600">
                        {zone.name}
                    </Text>

                    <HStack spacing={2}>
                        <Badge colorPalette={zone.enabled ? "green" : "red"}>
                            {zone.enabled ? "Enabled" : "Disabled"}
                        </Badge>

                        <Badge colorPalette="teal">
                            {zone.irrigation_mode === "even_area"
                                ? "Even Area"
                                : "Per Plant"}
                        </Badge>
                    </HStack>

                    <Text fontSize="sm" color="gray.600">
                        Valve pin: {zone.relay_pin}
                    </Text>
                </Stack>

                {/* Corrections */}
                <Stack align="center" spacing={2}>
                    <LimitedCorrectionIndicator
                        label="Solar"
                        value={zone.local_correction_factors.solar}
                    />
                    <LimitedCorrectionIndicator
                        label="Rain"
                        value={zone.local_correction_factors.rain}
                    />
                    <LimitedCorrectionIndicator
                        label="Temp"
                        value={zone.local_correction_factors.temperature}
                    />
                </Stack>
            </HStack>
        </Box>
    )
}
