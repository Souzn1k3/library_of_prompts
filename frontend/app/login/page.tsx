import { AuthShell } from "@/components/AuthShell";
import { LoginForm } from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <AuthShell
      titleKey="login.pageTitle"
      subtitleKey="login.pageSubtitle"
      formTitleKey="login.pageTitle"
      formSubtitleKey="login.pageSubtitle"
    >
      <LoginForm />
    </AuthShell>
  );
}
