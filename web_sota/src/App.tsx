import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { BookmarksPage } from "@/pages/bookmarks";
import { BulkOpsPage } from "@/pages/bulk-ops";
import { Chat } from "@/pages/chat";
import { Dashboard } from "@/pages/dashboard";
import { Help } from "@/pages/help";
import { LogsPage } from "@/pages/logs";
import { SearchPage } from "@/pages/search";
import { Settings } from "@/pages/settings";
import { TagsPage } from "@/pages/tags";
import { Tools } from "@/pages/tools";
import { TreePage } from "@/pages/tree";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/bookmarks" element={<BookmarksPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/tree" element={<TreePage />} />
          <Route path="/bulk" element={<BulkOpsPage />} />
          <Route path="/tags" element={<TagsPage />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/help" element={<Help />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
