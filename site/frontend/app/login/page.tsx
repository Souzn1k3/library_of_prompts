import { LoginForm } from "@/components/LoginForm";

export default function LoginPage() {
  return (
    <div className="mx-auto max-w-md space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Log in</h1>
        <p className="text-sm text-zinc-600">
          Uses JWT access tokens from the Prompts Vault API. Your session is stored in this
          browser only.
        </p>
      </div>
      <LoginForm />
    </div>
  );
}
