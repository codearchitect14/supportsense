import { useEffect, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { api } from "../../lib/api";
import { errorMessage } from "../../lib/errors";
import type { Role, User } from "../../lib/types";

const roles: Role[] = ["admin", "agent", "viewer"];

export function UserManagementPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<User[]>("/users")
      .then(setUsers)
      .catch(() => setError("Could not load users."))
      .finally(() => setLoading(false));
  }, []);

  async function handleRoleChange(userId: string, role: Role) {
    setError(null);
    setUpdatingId(userId);
    try {
      const updated = await api.patch<User>(`/users/${userId}/role`, { role });
      setUsers((prev) => prev.map((u) => (u.id === userId ? updated : u)));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setUpdatingId(null);
    }
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-16 shrink-0 items-center border-b border-slate-200 bg-white px-6">
        <h1 className="text-base font-semibold text-slate-900">User Management</h1>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        {error && (
          <div className="mb-4">
            <ErrorBanner message={error} />
          </div>
        )}

        {!loading && (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Email</th>
                  <th className="px-4 py-3">Role</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="px-4 py-3 font-medium text-slate-900">{user.full_name}</td>
                    <td className="px-4 py-3 text-slate-600">{user.email}</td>
                    <td className="px-4 py-3">
                      <select
                        value={user.role}
                        disabled={user.id === currentUser?.id || updatingId === user.id}
                        onChange={(e) => handleRoleChange(user.id, e.target.value as Role)}
                        className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm capitalize disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400"
                      >
                        {roles.map((role) => (
                          <option key={role} value={role}>
                            {role}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={
                          user.is_active
                            ? "rounded-full bg-accent-500/10 px-2.5 py-1 text-xs font-medium text-accent-600"
                            : "rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-500"
                        }
                      >
                        {user.is_active ? "Active" : "Disabled"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
