import {
    Box,
    Stack
} from "@chakra-ui/react"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import TimelineItem from "./TimelineItem"

export default function TodaysActivityCard({ items }) {

    return (
        <GlassPanelSection
            title="Today's Activity"
            description="Planned and completed irrigation tasks for today"
        >
            <Box position="relative" pl="28px">

                {/* Vertical timeline line */}
                <Box
                    position="absolute"
                    left="12px"
                    top="0"
                    bottom="0"
                    width="2px"
                    bg="rgba(56,178,172,0.12)"
                />

                <Stack gap={6}>
                    {items.map(item => (
                        <TimelineItem key={item.id} item={item} />
                    ))}
                </Stack>

            </Box>
        </GlassPanelSection>
    )
}
