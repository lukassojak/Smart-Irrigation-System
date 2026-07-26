import PageContainer from "../../../components/layout/PageContainer"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"
import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import PageNotImplementedWarning from "../../../components/ui/PageNotImplementedWarning"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import { useOutletContext } from "react-router-dom"

export default function NotificationsPage() {
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    return (
        <>
            <GlassPageHeader
                title="Notifications"
                onMobileMenuClick={openMobileSidebar}
            />
            <PageContainer>
                <DashboardPageSectionStack>
                    <GlassPanelSection>
                        <PageNotImplementedWarning
                            message="The notifications page is not available yet."
                            detail="This feature is not supported in the current version."
                        />
                    </GlassPanelSection>
                </DashboardPageSectionStack>
            </PageContainer>
        </>
    )
}