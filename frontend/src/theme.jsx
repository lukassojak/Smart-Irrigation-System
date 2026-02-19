import { createSystem, defaultConfig } from "@chakra-ui/react"

export const theme = createSystem(defaultConfig, {
    semanticTokens: {
        colors: {
            background: {
                DEFAULT: {
                    value: {
                        _light: "#f7f9fb",
                        _dark: "#0f172a",
                    },
                },
            },
        },
    }
})
