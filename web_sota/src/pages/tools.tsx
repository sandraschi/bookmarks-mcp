import { Bookmark, Loader2, Play, Terminal } from "lucide-react";
import { useEffect, useState } from "react";
import { callTool, getTools, unwrapToolResult } from "@/common/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function Tools() {
  const [executing, setExecuting] = useState<{ [key: string]: boolean }>({});
  const [results, setResults] = useState<{ [key: string]: unknown }>({});
  const [tools, setTools] = useState<
    { name: string; description: string | null }[]
  >([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getTools()
      .then((data) => setTools(data.tools))
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load tools"),
      )
      .finally(() => setLoading(false));
  }, []);

  const handleExecute = async (toolName: string) => {
    setExecuting((prev) => ({ ...prev, [toolName]: true }));
    try {
      const response = await callTool(toolName, {});
      const payload = unwrapToolResult(response);
      setResults((prev) => ({ ...prev, [toolName]: payload }));
    } catch (err) {
      setResults((prev) => ({
        ...prev,
        [toolName]: err instanceof Error ? err.message : "Execution failed",
      }));
    } finally {
      setExecuting((prev) => ({ ...prev, [toolName]: false }));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          MCP Tools
        </h2>
        <p className="text-slate-400">
          Registered portmanteau tools on the bookmarks-mcp server
        </p>
      </div>

      {error && <p className="text-red-400 text-sm">{error}</p>}
      {loading && <Loader2 className="h-6 w-6 animate-spin text-slate-500" />}

      <div className="grid gap-4 md:grid-cols-2">
        {tools.map((tool) => (
          <Card
            key={tool.name}
            className="bg-slate-900/40 border-slate-800 hover:border-blue-500/50 transition-colors flex flex-col"
          >
            <CardHeader className="flex flex-row items-center space-y-0 gap-4">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <Bookmark className="h-5 w-5 text-blue-500" />
              </div>
              <div className="flex-1 min-w-0">
                <CardTitle className="text-sm font-mono text-slate-100 truncate">
                  {tool.name}
                </CardTitle>
                <CardDescription className="text-xs text-slate-500 mt-1 line-clamp-3">
                  {tool.description || "No description"}
                </CardDescription>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono bg-slate-950/50 p-2 rounded">
                <Terminal className="h-3 w-3" />
                <span>POST /api/tools/call</span>
              </div>
              <Button
                onClick={() => handleExecute(tool.name)}
                disabled={executing[tool.name]}
                className="w-full bg-slate-800 hover:bg-slate-700 text-slate-200"
              >
                {executing[tool.name] ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                {executing[tool.name] ? "Calling…" : "Ping (empty args)"}
              </Button>
              {results[tool.name] != null && (
                <pre className="p-3 text-xs font-mono rounded bg-slate-950 border border-slate-800 overflow-auto max-h-32 text-slate-300">
                  {typeof results[tool.name] === "string"
                    ? (results[tool.name] as string)
                    : JSON.stringify(results[tool.name], null, 2)}
                </pre>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
