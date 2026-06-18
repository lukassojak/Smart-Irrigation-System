import { Stack, Spinner, Text } from "@chakra-ui/react";

export default function LoadingState({
    message = "Loading..."
}) {
    return (
        <Stack
            align="center"
            gap={4}
            py={20}
        >
            <Spinner
                color="teal.500"
                size="lg"
            />

            <Text
                fontSize="md"
                fontWeight="medium"
                color="teal.700"
            >
                {message}
            </Text>
        </Stack>
    );
}