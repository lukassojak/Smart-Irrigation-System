// NodeCard.jsx
import { Box, Heading, Text, Stack, HStack, Badge } from "@chakra-ui/react"
import { Link } from "react-router-dom"

import {
    Router,
    RefreshCcw,
} from "lucide-react"

export default function NodeCard({ node }) {
    const isPushed = node?.config_sync_status === "PUSHED"

    return (
        <Box
            as={Link}
            to={`/configuration/nodes/${node.id}`}
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
        >
            <HStack spacing={4} align="stretch">
                <Box
                    w="36px"
                    h="36px"
                    borderRadius="md"
                    bg="rgba(56,178,172,0.08)"
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                >
                    <Router size={20} color="#319795" />
                </Box>

                <Stack spacing={1} flex="1">
                    <HStack justify="space-between" align="flex-start">
                        <Heading size="md" fontWeight="600">
                            Node #{node.id}
                        </Heading>
                        {!isPushed && (
                            <Badge colorPalette="orange" fontSize="0.75em">
                                <RefreshCcw size={14} style={{ marginRight: "4px" }} />
                                Not synced
                            </Badge>
                        )}
                    </HStack>

                    <Text fontSize="sm" color="gray.600">
                        {node.name}
                    </Text>

                    <Text fontSize="xs" color="gray.500">
                        {node.location || "No location defined"}
                    </Text>

                    <Text fontSize="xs" color="gray.500">
                        {node.zones?.length ?? 0} zones configured
                    </Text>
                </Stack>
            </HStack>
        </Box>
    )
}
