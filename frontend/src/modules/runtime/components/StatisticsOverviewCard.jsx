import {
    Box,
    VStack,
    HStack,
    Text
} from "@chakra-ui/react"
import { keyframes } from "@emotion/react"
import { useState, useEffect } from "react"

// Animace při změně hodnoty - slide in s fade efektem
const slideInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`

function AnimatedValue({ value }) {
    const [animationKey, setAnimationKey] = useState(0)

    useEffect(() => {
        setAnimationKey((prev) => prev + 1)
    }, [value])

    return (
        <Text
            key={animationKey}
            fontSize="2xl"
            fontWeight="600"
            color="gray.800"
            letterSpacing="-0.02em"
            animation={`${slideInUp} 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)`}
        >
            {value}
        </Text>
    )
}

export default function StatisticsOverviewCard({
    icon: Icon,
    label,
    value,
    description,
    footer
}) {
    return (
        <Box
            bg="rgba(255,255,255,0.95)"
            borderWidth="1px"
            borderColor="rgba(56,178,172,0.06)"
            borderRadius="lg"
            p={5}
            boxShadow="0 4px 16px rgba(15, 23, 42, 0.05)"
            transition="all 0.15s ease"
            _hover={{
                borderColor: "rgba(56,178,172,0.18)",
                boxShadow: "0 6px 20px rgba(15,23,42,0.06)",
                transform: "translateY(-2px)"
            }}
        >
            <VStack align="start" spacing={3}>

                <HStack gap={3}>
                    {Icon && (
                        <Box bg="teal.50" p={2} borderRadius="md">
                            <Icon size={18} color="#319795" />
                        </Box>
                    )}

                    <Text
                        fontSize="sm"
                        fontWeight="600"
                        color="gray.700"
                    >
                        {label}
                    </Text>
                </HStack>

                <AnimatedValue value={value} />

                {description && (
                    <Text fontSize="sm" color="gray.500">
                        {description}
                    </Text>
                )}

                {footer && (
                    <Box pt={2}>
                        {footer}
                    </Box>
                )}

            </VStack>
        </Box>
    )
}