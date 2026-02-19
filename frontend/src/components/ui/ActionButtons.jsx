import { Button } from "@chakra-ui/react"

export function HeaderAction(props) {
    return (
        <PanelButton
            size="sm"
            variant="subtle"
            colorPalette="gray"
            borderRadius="md"
            fontWeight="500"
            transition="background 0.2s ease, transform 0.06s ease"
            _focusVisible={{
                boxShadow: "0 0 0 2px rgba(56,178,172,0.35)"
            }}
            {...props}
        />
    )
}

export function HeaderActionDanger(props) {
    return (
        <HeaderAction
            colorPalette="red"
            {...props}
        />
    )
}

export function PanelButton(props) {
    return (
        <Button
            size="sm"
            borderRadius="md"
            fontWeight="500"
            variant="solid"
            colorPalette="gray"
            boxShadow="0 2px 6px rgba(15,23,42,0.05)"
            transition="background 0.12s ease, box-shadow 0.12s ease, transform 0.06s ease"
            _hover={{
                boxShadow: "0 4px 12px rgba(15,23,42,0.08)",
            }}
            _active={{
                transform: "translateY(0px)"
            }}
            _focusVisible={{
                boxShadow: "0 0 0 2px rgba(56,178,172,0.35)"
            }}
            {...props}
        />
    )
}

export function PanelButtonDanger(props) {
    return (
        <PanelButton
            colorPalette="red"
            {...props}
        />
    )
}