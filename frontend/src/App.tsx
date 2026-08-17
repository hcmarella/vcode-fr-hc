import { Route, Routes } from "react-router-dom";

import AppShell from "./components/layout/AppShell";
import RequireAuth from "./components/layout/RequireAuth";
import AboutPage from "./pages/AboutPage";
import AdminSyncPage from "./pages/AdminSyncPage";
import CommandDetailPage from "./pages/CommandDetailPage";
import CommandsPage from "./pages/CommandsPage";
import HomePage from "./pages/HomePage";
import JiraPage from "./pages/JiraPage";
import KnowledgeDetailPage from "./pages/KnowledgeDetailPage";
import KnowledgePage from "./pages/KnowledgePage";
import LoginPage from "./pages/LoginPage";
import NewSessionPage from "./pages/NewSessionPage";
import PersonaDetailPage from "./pages/PersonaDetailPage";
import PersonasPage from "./pages/PersonasPage";
import ReportsPage from "./pages/ReportsPage";
import SessionChatPage from "./pages/SessionChatPage";
import SessionsListPage from "./pages/SessionsListPage";
import SignupPage from "./pages/SignupPage";
import SkillDetailPage from "./pages/SkillDetailPage";
import SkillsPage from "./pages/SkillsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route element={<RequireAuth />}>
        <Route element={<AppShell />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/personas" element={<PersonasPage />} />
          <Route path="/personas/:slug" element={<PersonaDetailPage />} />
          <Route path="/skills" element={<SkillsPage />} />
          <Route path="/skills/:slug" element={<SkillDetailPage />} />
          <Route path="/commands" element={<CommandsPage />} />
          <Route path="/commands/:slug" element={<CommandDetailPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/knowledge/:id" element={<KnowledgeDetailPage />} />
          <Route path="/jira" element={<JiraPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/admin/sync" element={<AdminSyncPage />} />
          <Route path="/sessions" element={<SessionsListPage />} />
          <Route path="/sessions/new" element={<NewSessionPage />} />
          <Route path="/sessions/:id" element={<SessionChatPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
