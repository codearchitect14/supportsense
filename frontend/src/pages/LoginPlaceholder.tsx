import { ArrowLeft } from "lucide-react";
import { Link } from "react-router-dom";
import { Logo } from "../components/ui/Logo";
import { Card } from "../components/ui/Card";

export function LoginPlaceholder() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-[#fafafa] px-6">
      <Link to="/" className="mb-8">
        <Logo />
      </Link>

      <Card className="w-full max-w-sm text-center">
        <h1 className="text-lg font-semibold text-slate-900">Sign in to SupportSense</h1>
        <p className="mt-2 text-sm leading-relaxed text-slate-600">
          The authenticated app, including sign in, sign up, and the chat, voice, and analytics
          workspace, is built in the next phase of this project.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-700"
        >
          <ArrowLeft size={15} />
          Back to the homepage
        </Link>
      </Card>
    </div>
  );
}
