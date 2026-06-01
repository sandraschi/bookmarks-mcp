import { Bookmark, Bot, RefreshCw, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Help() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            System Documentation
          </h2>
          <p className="text-slate-400">
            Guides and reference for Bookmark Master
          </p>
        </div>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Bookmark className="h-5 w-5 text-blue-500" />
              Getting Started
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-400 space-y-4">
            <p>
              Bookmark Master provides a unified interface for managing browser
              knowledge. It supports Edge, Chrome, and Firefox through the
              Bookmark Master MCP.
            </p>
            <div className="space-y-2">
              <h4 className="font-semibold text-slate-200">Core Features</h4>
              <ul className="list-disc list-inside space-y-1">
                <li>Cross-browser search and retrieval</li>
                <li>Automated organization and tagging</li>
                <li>AI-powered content summarization</li>
                <li>Real-time synchronization</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Bot className="h-5 w-5 text-purple-500" />
              AI Integration
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-400 space-y-4">
            <p>
              Leverage Local LLMs (Ollama, LM Studio) to interact with your
              bookmarks using natural language.
            </p>
            <div className="space-y-2 font-mono bg-slate-900/50 p-3 rounded text-xs border border-slate-800">
              <p className="text-blue-400">{"// Example AI command"}</p>
              <p className="text-slate-300">
                "Summarize all my bookmarks about React hooks from last month"
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <RefreshCw className="h-5 w-5 text-green-500" />
              Sync Protocol
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-400 space-y-4">
            <p>
              To sync bookmarks between browsers, ensure you have the necessary
              permissions configured in the MCP transport settings.
            </p>
            <div className="bg-slate-900/80 p-3 rounded text-xs border border-slate-800">
              <p className="font-medium text-slate-200 mb-2">
                Sync Rule Example:
              </p>
              <code className="text-emerald-400">
                browser_bookmarks(sync_bookmarks, edge → firefox)
              </code>
            </div>
          </CardContent>
        </Card>

        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-white">
              <Zap className="h-5 w-5 text-yellow-500" />
              Troubleshooting
            </CardTitle>
          </CardHeader>
          <CardContent className="text-sm text-slate-400 space-y-4">
            <div className="space-y-3">
              <div>
                <h4 className="font-semibold text-slate-200">
                  Local LLM not responding
                </h4>
                <p>
                  Check that Ollama or LM Studio is running and the endpoint
                  matches the settings page.
                </p>
              </div>
              <div>
                <h4 className="font-semibold text-slate-200">
                  Browser not found
                </h4>
                <p>
                  Ensure the browser path is correctly configured in your
                  environment variables.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
