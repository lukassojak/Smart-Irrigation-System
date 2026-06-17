import { Stack } from "@chakra-ui/react";

export default function PageSectionStack({ children }) {
    return (
        <Stack gap={8}>
            {children}
        </Stack>
    );
}