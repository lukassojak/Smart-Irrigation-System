import {
    Box,
    Grid,
    Heading,
    HStack,
    Text,
    VStack,
} from "@chakra-ui/react"

const PIN_TYPE_COLOR = {
    gpio_free: "green.500",
    gpio_used: "red.500",
    power: "cyan.500",
    ground: "blue.600",
    other: "gray.500",
}

const PIN_TYPE_LABEL = {
    gpio_free: "GPIO",
    gpio_used: "GPIO",
    power: "Power",
    ground: "Ground",
    other: "Other",
}

const getStatusLabel = (type) => {
    if (type === "gpio_free") return "FREE"
    if (type === "gpio_used") return "OCCUPIED"
    return null
}

const getPinColor = (pin, mode) => {
    if (mode === "select") {
        if (pin.type === "gpio_free") return "green.500"
        return "gray.500"
    }
    return PIN_TYPE_COLOR[pin.type] || "gray.500"
}

const isSelectablePin = (pin, mode) => {
    if (mode !== "select") return false
    return pin.type === "gpio_free"
}

function HeaderPin({ pin, mode, selectedBoardPinId, onPinSelect }) {
    const selectable = isSelectablePin(pin, mode)
    const viewOnly = mode === "view"
    const isSelected = selectedBoardPinId === pin.boardPinId

    const typeLabel = PIN_TYPE_LABEL[pin.type] || "Other"
    const statusLabel = getStatusLabel(pin.type)

    const tooltipContent = `${typeLabel}${statusLabel ? ` - ${statusLabel}` : ""}\nPin ${pin.boardPinId}${pin.bcmPinId !== null && pin.bcmPinId !== undefined ? ` (BCM ${pin.bcmPinId})` : ""}${pin.label ? `\n${pin.label}` : ""}`

    return (
        <Box
            as={selectable ? "button" : "div"}
            type={selectable ? "button" : undefined}
            onClick={selectable ? () => onPinSelect?.(pin) : undefined}
            bg={getPinColor(pin, mode)}
            w={6}
            h={6}
            borderRadius="sm"
            cursor={selectable ? "pointer" : viewOnly ? "default" : "not-allowed"}
            opacity={mode === "select" && !selectable ? 0.75 : 1}
            transition="transform 0.1s ease, box-shadow 0.1s ease"
            _hover={selectable || viewOnly ? { transform: "scale(1.08)", boxShadow: "sm" } : undefined}
            display="flex"
            alignItems="center"
            justifyContent="center"
            fontSize="sm"
            fontWeight="600"
            color="white"
            title={tooltipContent}
            border={isSelected ? "2px solid" : "1px solid"}
            borderColor={isSelected ? "white" : "transparent"}
            boxShadow={isSelected ? "0 0 0 2px rgba(49,151,149,0.45)" : "none"}
        >
            {pin.boardPinId}
        </Box>
    )
}

export default function GPIOHeaderVisualizer({
    pins,
    mode = "view",
    selectedBoardPinId = null,
    onPinSelect,
    showLegend = true,
}) {
    const rows = []
    for (let i = 0; i < pins.length; i += 2) {
        rows.push([pins[i], pins[i + 1]])
    }

    return (
        <HStack align="start" gap={10} w="100%">
            <Box
                bg="bg.subtle"
                border="2px solid"
                borderColor="border.muted"
                borderRadius="lg"
                p={4}
            >
                <VStack gap={1}>
                    {rows.map((row, idx) => (
                        <HStack key={idx} gap={4}>
                            <HeaderPin
                                pin={row[0]}
                                mode={mode}
                                selectedBoardPinId={selectedBoardPinId}
                                onPinSelect={onPinSelect}
                            />
                            <HeaderPin
                                pin={row[1]}
                                mode={mode}
                                selectedBoardPinId={selectedBoardPinId}
                                onPinSelect={onPinSelect}
                            />
                        </HStack>
                    ))}
                </VStack>
            </Box>

            {showLegend && (
                <Box w="100%" maxW="250px" alignSelf="flex-start">
                    <Heading size="sm" mb={3}>
                        Legend
                    </Heading>
                    <Grid templateColumns="repeat(auto-fit, minmax(170px, 1fr))" gap={2}>
                        <HStack spacing={2}>
                            <Box bg="green.500" w={4} h={4} borderRadius="sm" />
                            <Text fontSize="sm">GPIO - Available</Text>
                        </HStack>
                        <HStack spacing={2}>
                            <Box bg={mode === "select" ? "gray.500" : "red.500"} w={4} h={4} borderRadius="sm" />
                            <Text fontSize="sm">GPIO - {mode === "select" ? "Unavailable" : "In Use"}</Text>
                        </HStack>
                        <HStack spacing={2}>
                            <Box bg={mode === "select" ? "gray.500" : "cyan.500"} w={4} h={4} borderRadius="sm" />
                            <Text fontSize="sm">Power (5V)</Text>
                        </HStack>
                        <HStack spacing={2}>
                            <Box bg={mode === "select" ? "gray.500" : "blue.600"} w={4} h={4} borderRadius="sm" />
                            <Text fontSize="sm">Ground (GND)</Text>
                        </HStack>
                        <HStack spacing={2}>
                            <Box bg="gray.500" w={4} h={4} borderRadius="sm" />
                            <Text fontSize="sm">Reserved</Text>
                        </HStack>
                    </Grid>
                </Box>
            )}
        </HStack>
    )
}
