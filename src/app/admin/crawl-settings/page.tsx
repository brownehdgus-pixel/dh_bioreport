import { AdminLogin } from "@/components/admin/AdminLogin";
import { AdminCrawlSettings } from "@/components/admin/AdminCrawlSettings";
import { isAdminAuthenticated, isAdminPasswordConfigured } from "@/lib/adminAuth";

export const metadata = {
  title: "크롤 설정 | Bio Industry Daily Memo",
  description: "RSS·키워드·가중치 crawl_config.json 편집",
};

export default async function AdminCrawlSettingsPage() {
  const configured = isAdminPasswordConfigured();
  const authenticated = configured && (await isAdminAuthenticated());

  if (!authenticated) {
    return <AdminLogin configMissing={!configured} />;
  }

  return <AdminCrawlSettings />;
}
