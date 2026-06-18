import { Box } from "@chakra-ui/react";

export default function PageContainer({ children }) {
    return (
        <Box
            px={{ base: 4, md: 6 }}
            py={{ base: 4, md: 8 }}
            w="100%"
        >
            {children}
        </Box>
    );
}