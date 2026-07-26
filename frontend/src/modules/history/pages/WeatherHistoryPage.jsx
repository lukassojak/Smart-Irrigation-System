import PageContainer from "../../../components/layout/PageContainer"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"
import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import PageNotImplementedWarning from "../../../components/ui/PageNotImplementedWarning"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import { useOutletContext } from "react-router-dom"

export default function WeatherHistoryPage() {
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    return (
        <>
            <GlassPageHeader
                title="Weather History"
                onMobileMenuClick={openMobileSidebar}
            />
            <PageContainer>
                <DashboardPageSectionStack>
                    <GlassPanelSection>
                        <PageNotImplementedWarning
                            message="The weather history page is not available yet."
                            detail="This feature is not supported in the current version."
                        />
                    </GlassPanelSection>
                </DashboardPageSectionStack>
            </PageContainer>
        </>
    )
}