import PageContainer from "../../../components/layout/PageContainer"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"
import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import PageNotImplementedWarning from "../../../components/ui/PageNotImplementedWarning"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"
import { useOutletContext } from "react-router-dom"

export default function SettingsPage() {
    const { isMobile, openMobileSidebar } = useOutletContext() || {}

    return (
        <>
            <GlassPageHeader
                title="Settings"
                subtitle="Manage your system settings and preferences."
                onMobileMenuClick={openMobileSidebar}
            />
            <PageContainer>
                <DashboardPageSectionStack>
                    <GlassPanelSection>
                        <PageNotImplementedWarning message="The settings page is not available yet." />
                    </GlassPanelSection>
                </DashboardPageSectionStack>
            </PageContainer>
        </>
    )
}