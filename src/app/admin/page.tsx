import { AdminLogin } from "@/components/admin/AdminLogin";
import { AdminPanel } from "@/components/admin/AdminPanel";
import { isAdminAuthenticated, isAdminPasswordConfigured } from "@/lib/adminAuth";

export const metadata = {
  title: "뉴스 입력 | Daily Bio",
  description: "뉴스 항목 입력 및 JSON 복사",
};

export default async function AdminPage() {
  const configured = isAdminPasswordConfigured();
  const authenticated = configured && (await isAdminAuthenticated());

  if (!authenticated) {
    return <AdminLogin configMissing={!configured} />;
  }

  return <AdminPanel />;
}
