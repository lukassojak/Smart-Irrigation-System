import {
    Drawer
} from "@chakra-ui/react"

import Sidebar from "./Sidebar"

export default function MobileSidebar({ isOpen, onClose }) {

    return (
        <Drawer.Root
            open={isOpen}
            placement="start"
            closeOnInteractOutside={true}
            closeOnEscape={true}
            onOpenChange={(e) => {
                if (!e.open) onClose()
            }}
        >
            <Drawer.Backdrop />

            <Drawer.Positioner>
                <Drawer.Content maxW="260px">

                    <Drawer.Body p={0}>
                        <Sidebar />
                    </Drawer.Body>

                </Drawer.Content>
            </Drawer.Positioner>
        </Drawer.Root>
    )
}