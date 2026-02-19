// BaseCard.jsx
import { Box } from "@chakra-ui/react"

export default function BaseCard({
    children,
    variant = "solid",
    ...props
}) {

    const variants = {
        solid: {
            bg: "rgba(255,255,255,0.92)",
            border: "1px solid rgba(56,178,172,0.06)",
            boxShadow: "0 4px 16px rgba(15,23,42,0.05)",
        },

        glass: {
            backdropFilter: "blur(10px) saturate(140%)",
            bg: "rgba(255,255,255,0.75)",
            border: "1px solid rgba(56,178,172,0.08)",
            boxShadow: "0 6px 20px rgba(15,23,42,0.04)",
        },

        edge: {
            bg: "rgba(255,255,255,0.92)",
            border: "1px solid rgba(56,178,172,0.06)",
            boxShadow: "0 4px 16px rgba(15,23,42,0.05)",
            _hover: {
                borderColor: "teal.300",
                boxShadow: "0 6px 20px rgba(15,23,42,0.08)",
            },
        },
    }

    return (
        <Box
            borderRadius="lg"
            p={5}
            transition="all 0.12s ease"
            {...variants[variant]}
            {...props}
        >
            {children}
        </Box>
    )
}
