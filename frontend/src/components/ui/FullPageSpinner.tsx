import { Loader2 } from "lucide-react";

export function FullPageSpinner() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-[#fafafa]">
      <Loader2 className="animate-spin text-brand-500" size={28} />
    </div>
  );
}
