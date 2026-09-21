import { type FormEvent, useState } from "react";
import { useAuth } from "../../context/AuthContext";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { FormField } from "../../components/ui/FormField";
import { Button } from "../../components/ui/Button";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { api } from "../../lib/api";
import { errorMessage } from "../../lib/errors";
import type { User } from "../../lib/types";

export function SettingsPage() {
  const { user, updateUser, logout } = useAuth();

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileSaved, setProfileSaved] = useState(false);
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [changingPassword, setChangingPassword] = useState(false);

  async function handleProfileSubmit(event: FormEvent) {
    event.preventDefault();
    setProfileError(null);
    setProfileSaved(false);
    setSavingProfile(true);
    try {
      const updated = await api.patch<User>("/auth/me", { full_name: fullName });
      updateUser(updated);
      setProfileSaved(true);
    } catch (err) {
      setProfileError(errorMessage(err));
    } finally {
      setSavingProfile(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setPasswordError(null);
    setChangingPassword(true);
    try {
      await api.post("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      // Changing the password revokes every refresh token, this session
      // included, so the safest move is to sign out and ask for a fresh login.
      await logout();
    } catch (err) {
      setPasswordError(errorMessage(err));
      setChangingPassword(false);
    }
  }

  return (
    <div className="flex h-screen flex-col">
      <header className="flex h-16 shrink-0 items-center border-b border-slate-200 bg-white px-6">
        <h1 className="text-base font-semibold text-slate-900">Settings</h1>
      </header>

      <div className="mx-auto w-full max-w-xl flex-1 space-y-6 overflow-y-auto p-6">
        <Card>
          <h2 className="mb-1 text-sm font-semibold text-slate-900">Profile</h2>
          <p className="mb-5 text-sm text-slate-500">{user?.email}</p>

          <form onSubmit={handleProfileSubmit} className="space-y-4">
            {profileError && <ErrorBanner message={profileError} />}
            <FormField label="Full name" htmlFor="full_name">
              <Input id="full_name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
            </FormField>
            <div className="flex items-center gap-3">
              <Button type="submit" disabled={savingProfile}>
                {savingProfile ? "Saving…" : "Save changes"}
              </Button>
              {profileSaved && <span className="text-sm font-medium text-accent-600">Saved</span>}
            </div>
          </form>
        </Card>

        <Card>
          <h2 className="mb-1 text-sm font-semibold text-slate-900">Change password</h2>
          <p className="mb-5 text-sm text-slate-500">You&apos;ll be signed out after changing it.</p>

          <form onSubmit={handlePasswordSubmit} className="space-y-4">
            {passwordError && <ErrorBanner message={passwordError} />}
            <FormField label="Current password" htmlFor="current_password">
              <Input
                id="current_password"
                type="password"
                autoComplete="current-password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </FormField>
            <FormField label="New password" htmlFor="new_password">
              <Input
                id="new_password"
                type="password"
                autoComplete="new-password"
                minLength={8}
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </FormField>
            <Button type="submit" variant="secondary" disabled={changingPassword}>
              {changingPassword ? "Updating…" : "Change password"}
            </Button>
          </form>
        </Card>
      </div>
    </div>
  );
}
