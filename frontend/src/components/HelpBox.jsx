import { Box, Heading, Text } from "@chakra-ui/react"

export default function HelpBox({
    title,
    children,
    active = false,
    boxRef,
}) {
    return (
        <Box
            ref={boxRef}
            bg={active ? "teal.700" : "teal.50"}
            p={4}
            borderRadius="md"
            textAlign="left"
            transition="background-color 0.2s ease"
        >
            <Heading
                fontSize="sm"
                fontWeight="bold"
                mb={2}
                color={active ? "whiteAlpha.900" : "teal.700"}
            >
                {title}
            </Heading>

            <Text
                fontSize="sm"
                color={active ? "whiteAlpha.800" : "fg.muted"}
            >
                {children}
            </Text>
        </Box>
    )
}
