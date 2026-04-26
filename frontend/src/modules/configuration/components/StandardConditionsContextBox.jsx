import { useEffect, useState } from "react"
import { Box, SimpleGrid, Stack, Text } from "@chakra-ui/react"

import { fetchGlobalConfig } from "../../../api/globalConfig.api"
import DataUnavailableWarning from "../../../components/ui/DataUnavailableWarning"


export default function StandardConditionsContextBox({
    title = "Current standard conditions",
    helperText = "Use these baseline values when setting base irrigation volume.",
}) {
    const [standardConditions, setStandardConditions] = useState(null)

    useEffect(() => {
        fetchGlobalConfig()
            .then((response) => {
                setStandardConditions(response.data?.standard_conditions ?? null)
            })
            .catch(() => {
                setStandardConditions(null)
            })
    }, [])

    if (!standardConditions) {
        return <DataUnavailableWarning message="Standard conditions are temporarily unavailable." />
    }

    return (
        <Box
            borderRadius="md"
            p={4}
            bg="rgba(56,178,172,0.05)"
            border="1px solid rgba(56,178,172,0.12)"
        >
            <Stack gap={2}>
                <Text fontSize="sm" fontWeight="600" color="teal.700">
                    {title}
                </Text>
                <Text fontSize="sm" color="fg.muted">
                    {helperText}
                </Text>

                <SimpleGrid columns={{ base: 1, md: 3 }} gap={2}>
                    <Text fontSize="xs" color="fg.muted">
                        Solar total: <Text as="span" color="fg" fontWeight="600">{standardConditions.solar_total}</Text>
                    </Text>
                    <Text fontSize="xs" color="fg.muted">
                        Rain: <Text as="span" color="fg" fontWeight="600">{standardConditions.rain_mm} mm</Text>
                    </Text>
                    <Text fontSize="xs" color="fg.muted">
                        Temperature: <Text as="span" color="fg" fontWeight="600">{standardConditions.temperature_celsius} C</Text>
                    </Text>
                </SimpleGrid>
            </Stack>
        </Box>
    )
}
