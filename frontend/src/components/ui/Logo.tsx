import { cn } from "../../lib/cn";

export function Logo({ className, dark }: { className?: string; dark?: boolean }) {
  return (
    <span className={cn("inline-flex items-center gap-2 font-heading font-bold", className)}>
      <svg width="28" height="28" viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="#5638DD" />
        <path
          d="M9 12.5C9 10.567 10.567 9 12.5 9H19.5C21.433 9 23 10.567 23 12.5V17.5C23 19.433 21.433 21 19.5 21H15.5L11.5 24V21H12.5C10.567 21 9 19.433 9 17.5V12.5Z"
          fill="white"
        />
        <circle cx="13" cy="15" r="1.3" fill="#5638DD" />
        <circle cx="16" cy="15" r="1.3" fill="#5638DD" />
        <circle cx="19" cy="15" r="1.3" fill="#5638DD" />
      </svg>
      <span className={cn("text-lg", dark ? "text-white" : "text-slate-900")}>
        SupportSense
      </span>
    </span>
  );
}
