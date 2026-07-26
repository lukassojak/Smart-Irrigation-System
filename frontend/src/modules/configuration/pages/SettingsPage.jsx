import PageContainer from "../../../components/layout/PageContainer"
import DashboardPageSectionStack from "../../../components/layout/DashboardPageSectionStack"
import GlassPageHeader from "../../../components/layout/GlassPageHeader"
import PageNotImplementedWarning from "../../../components/ui/PageNotImplementedWarning"
import GlassPanelSection from "../../../components/layout/GlassPanelSection"

export default function SettingsPage() {
    return (
        <>
            <GlassPageHeader title="Settings" description="Manage your system settings and preferences." />
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