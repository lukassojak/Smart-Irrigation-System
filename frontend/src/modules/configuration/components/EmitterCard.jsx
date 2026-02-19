import {
    Box,
    VStack,
    HStack,
    Text,
    Badge
} from "@chakra-ui/react"
import { Droplet } from "lucide-react"

export default function EmitterCard({ emitter }) {

    return (
        <Box
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={4}
            boxShadow="0 4px 14px rgba(15,23,42,0.05)"
        >
            <VStack align="stretch" spacing={3}>

                <HStack justify="space-between">
                    <HStack spacing={2}>
                        <Droplet size={14} color="#319795" />
                        <Text fontWeight="600">
                            {emitter.type}
                        </Text>
                    </HStack>

                    <Badge
                        size="sm"
                        colorPalette="gray"
                        variant="subtle"
                    >
                        x{emitter.count}
                    </Badge>
                </HStack>

                <Text fontSize="sm" color="gray.600">
                    Flow rate: {emitter.flowRate} L/h
                </Text>

            </VStack>
        </Box>
    )
}
