import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { RequireAuth, RequireRole } from "./components/auth/RequireAuth";
import { AppShell } from "./components/app/AppShell";
import { MarketingHome } from "./pages/MarketingHome";
import { LoginPage } from "./pages/auth/LoginPage";
import { SignupPage } from "./pages/auth/SignupPage";
import { ChatPage } from "./pages/app/ChatPage";
import { VoicePage } from "./pages/app/VoicePage";
import { DashboardPage } from "./pages/app/DashboardPage";
import { HistoryPage } from "./pages/app/HistoryPage";
import { SettingsPage } from "./pages/app/SettingsPage";
import { UserManagementPage } from "./pages/app/UserManagementPage";

const CHAT_ROLES = ["admin", "agent"];

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<MarketingHome />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />

        <Route
          path="/app"
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="chat" replace />} />
          <Route
            path="chat"
            element={
              <RequireRole roles={CHAT_ROLES}>
                <ChatPage />
              </RequireRole>
            }
          />
          <Route
            path="chat/:conversationId"
            element={
              <RequireRole roles={CHAT_ROLES}>
                <ChatPage />
              </RequireRole>
            }
          />
          <Route
            path="voice"
            element={
              <RequireRole roles={CHAT_ROLES}>
                <VoicePage />
              </RequireRole>
            }
          />
          <Route
            path="voice/:conversationId"
            element={
              <RequireRole roles={CHAT_ROLES}>
                <VoicePage />
              </RequireRole>
            }
          />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route
            path="history"
            element={
              <RequireRole roles={CHAT_ROLES}>
                <HistoryPage />
              </RequireRole>
            }
          />
          <Route path="settings" element={<SettingsPage />} />
          <Route
            path="admin/users"
            element={
              <RequireRole roles={["admin"]}>
                <UserManagementPage />
              </RequireRole>
            }
          />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
