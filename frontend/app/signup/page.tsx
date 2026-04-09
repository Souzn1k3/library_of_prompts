import { AuthShell } from "@/components/AuthShell";
import { SignupForm } from "@/components/SignupForm";

export default function SignupPage() {
  return (
    <AuthShell
      titleKey="signup.pageTitle"
      subtitleKey="signup.pageSubtitle"
      formTitleKey="signup.pageTitle"
      formSubtitleKey="signup.pageSubtitle"
    >
      <SignupForm />
    </AuthShell>
  );
}
