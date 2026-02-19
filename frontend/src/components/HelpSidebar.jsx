import { Stack, Box, Heading } from "@chakra-ui/react"

export default function HelpSidebar({
    title = "Need Help?",
    sticky = false,
    stickyTop = "24px",
    maxHeight,
    scrollRef,
    children,
}) {
    return (
        <Stack
            spacing={4}
            gap={6}
            bg="bg.panel"
            borderWidth="1px"
            borderColor="bg.panel"
            borderRadius="md"
            p={4}
            h="fit-content"
            position={sticky ? "sticky" : "static"}
            top={sticky ? stickyTop : undefined}
            maxH={maxHeight}
            overflowY={maxHeight ? "auto" : undefined}
            pr={maxHeight ? 2 : undefined}
        >
            <Heading size="md" textAlign="left">
                {title}
            </Heading>

            <Stack spacing={6}>
                {children}
            </Stack>
        </Stack>
    )
}


