import { Stack } from "@chakra-ui/react";

export default function PageSectionStack({ children }) {
    return (
        <Stack gap={6}>
            {children}
        </Stack>
    );
}