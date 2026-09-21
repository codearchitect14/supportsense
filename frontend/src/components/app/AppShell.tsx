import {
  BarChart3,
  History,
  LogOut,
  MessageSquareText,
  Mic,
  Settings,
  Users,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";
import { Logo } from "../ui/Logo";
import { cn } from "../../lib/cn";

const navItems = [
  { to: "/app/chat", label: "Chat", icon: MessageSquareText, roles: ["admin", "agent"] },
  { to: "/app/voice", label: "Voice Agent", icon: Mic, roles: ["admin", "agent"] },
  { to: "/app/dashboard", label: "Dashboard", icon: BarChart3, roles: ["admin", "agent", "viewer"] },
  { to: "/app/history", label: "Conversation History", icon: History, roles: ["admin", "agent"] },
  { to: "/app/settings", label: "Settings", icon: Settings, roles: ["admin", "agent", "viewer"] },
];

export function AppShell() {
  const { user, logout } = useAuth();
  const visibleNavItems = navItems.filter((item) => !user || item.roles.includes(user.role));

  return (
    <div className="flex min-h-screen bg-[#fafafa]">
      <aside className="flex w-64 shrink-0 flex-col border-r border-slate-200 bg-white">
        <div className="flex h-16 items-center border-b border-slate-100 px-5">
          <Logo />
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {visibleNavItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                )
              }
            >
              <item.icon size={18} />
              {item.label}
            </NavLink>
          ))}

          {user?.role === "admin" && (
            <NavLink
              to="/app/admin/users"
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                )
              }
            >
              <Users size={18} />
              User Management
            </NavLink>
          )}
        </nav>

        <div className="border-t border-slate-100 p-3">
          <div className="mb-2 flex items-center gap-2.5 rounded-lg px-2 py-2">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-100 text-xs font-semibold text-brand-700">
              {user?.full_name
                .split(" ")
                .map((n) => n[0])
                .join("")
                .slice(0, 2)}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-900">{user?.full_name}</p>
              <p className="truncate text-xs capitalize text-slate-500">{user?.role}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => logout()}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-slate-900"
          >
            <LogOut size={17} />
            Log out
          </button>
        </div>
      </aside>

      <main className="min-w-0 flex-1">
        <Outlet />
      </main>
    </div>
  );
}
