import { SignupForm } from "@/components/SignupForm";

export default function SignupPage() {
  return (
    <div className="mx-auto max-w-md space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-900">Create account</h1>
        <p className="text-sm text-zinc-600">
          Creates a user via the API and stores a JWT in your browser for dashboard access.
        </p>
      </div>
      <SignupForm />
    </div>
  );
}
