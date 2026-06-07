import { BrowserRouter, Navigate, Route, Routes, useSearchParams } from "react-router-dom";
import { ThemeProvider } from "@/theme/ThemeContext";
import LoginPage from "@/pages/LoginPage";
import DashboardShell from "@/workspace/DashboardShell";
import HomeTab from "@/workspace/HomeTab";
import CallTab from "@/workspace/CallTab";
import ChatsTab from "@/workspace/ChatsTab";
import StatsTab from "@/workspace/StatsTab";
import KbTab from "@/workspace/KbTab";
import UserProfilePage from "@/workspace/UserProfilePage";
import TicketPage from "@/workspace/TicketPage";

function RedirectLegacyChatsRoute() {
  const [params] = useSearchParams();
  const id = params.get("id")?.trim();
  return <Navigate to={id ? `/tickets/${encodeURIComponent(id)}` : "/tickets"} replace />;
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<DashboardShell />}>
            <Route index element={<HomeTab />} />
            <Route path="call" element={<CallTab />} />
            <Route path="tickets/:ticketId" element={<TicketPage />} />
            <Route path="tickets" element={<ChatsTab />} />
            <Route path="chats" element={<RedirectLegacyChatsRoute />} />
            <Route path="stats" element={<StatsTab />} />
            <Route path="kb" element={<KbTab />} />
            <Route path="users/:userId" element={<UserProfilePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
