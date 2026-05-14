import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { ThemeProvider } from "@/theme/ThemeContext";
import LoginPage from "@/pages/LoginPage";
import DashboardShell from "@/workspace/DashboardShell";
import HomeTab from "@/workspace/HomeTab";
import CallTab from "@/workspace/CallTab";
import ChatsTab from "@/workspace/ChatsTab";
import StatsTab from "@/workspace/StatsTab";
import KbTab from "@/workspace/KbTab";
import UserProfileStub from "@/workspace/UserProfileStub";

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<DashboardShell />}>
            <Route index element={<HomeTab />} />
            <Route path="call" element={<CallTab />} />
            <Route path="chats" element={<ChatsTab />} />
            <Route path="stats" element={<StatsTab />} />
            <Route path="kb" element={<KbTab />} />
            <Route path="users/:userId" element={<UserProfileStub />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
