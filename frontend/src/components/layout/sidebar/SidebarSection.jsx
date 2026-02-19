// components/layout/sidebar/SidebarSection.jsx

import { VStack, Text } from "@chakra-ui/react"

export default function SidebarSection({ title, children }) {
    return (
        <VStack align="stretch" spacing={2}>
            <Text
                fontSize="xs"
                fontWeight="600"
                color="gray.500"
                textTransform="uppercase"
                letterSpacing="0.05em"
                px={2}
            >
                {title}
            </Text>

            <VStack align="stretch" spacing={1}>
                {children}
            </VStack>
        </VStack>
    )
}
