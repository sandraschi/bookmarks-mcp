import { Bot, Loader2, Send, User } from "lucide-react";
import { useRef, useState } from "react";
import { getLlmSettings, postAiChat } from "@/common/api";
import { searchBookmarks } from "@/common/bookmark-ops";
import { useBookmarkSettings } from "@/common/bookmark-settings";
import { isSuccess, normalizeBookmarks } from "@/common/bookmark-types";
import { BrowserBar } from "@/components/bookmarks/browser-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useToast } from "@/components/ui/toast";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  bookmarks?: { title?: string; url?: string }[];
}

export function Chat() {
  const { callOptions } = useBookmarkSettings();
  const { toast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const send = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const lower = text.toLowerCase();
      if (lower.startsWith("search ") || lower.includes("find bookmark")) {
        const query = text.replace(/^search\s+/i, "").trim();
        const data = await searchBookmarks(callOptions, query, 10);
        const rows = isSuccess(data) ? normalizeBookmarks(data) : [];
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: "assistant",
            content:
              rows.length > 0
                ? `Found ${rows.length} bookmark(s) for "${query}":`
                : `No bookmarks matched "${query}".`,
            bookmarks: rows.map((r) => ({ title: r.title, url: r.url })),
          },
        ]);
        return;
      }

      const llm = getLlmSettings();
      const reply = await postAiChat({
        message: text,
        provider: llm.provider,
        model: llm.model,
        endpoint: llm.endpoint,
      });
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: reply.response,
        },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Chat failed";
      toast({ title: "Chat error", description: message, variant: "error" });
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "assistant", content: message },
      ]);
    } finally {
      setLoading(false);
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Bookmark Interface
        </h2>
        <p className="text-slate-400">
          Natural language control — prefix with{" "}
          <code className="text-slate-300">search</code> for direct bookmark
          lookup, or ask the LLM (Settings).
        </p>
      </div>

      <BrowserBar />

      <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
        <CardContent
          ref={listRef}
          className="flex-1 overflow-y-auto p-4 space-y-4"
        >
          {messages.length === 0 && (
            <p className="text-sm text-slate-500">
              Try: search FastMCP — or ask the LLM to summarize your workflow.
            </p>
          )}
          {messages.map((msg) => (
            <div key={msg.id} className="flex gap-3">
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center border shrink-0 ${
                  msg.role === "user"
                    ? "bg-slate-800 border-slate-700"
                    : "bg-blue-900/20 border-blue-800"
                }`}
              >
                {msg.role === "user" ? (
                  <User className="h-4 w-4 text-slate-400" />
                ) : (
                  <Bot className="h-4 w-4 text-blue-400" />
                )}
              </div>
              <div className="flex-1 space-y-2 min-w-0">
                <p
                  className={`text-sm p-3 rounded-md border inline-block max-w-full whitespace-pre-wrap ${
                    msg.role === "user"
                      ? "text-slate-300 bg-slate-900/50 border-slate-800"
                      : "text-slate-300 bg-blue-950/10 border-blue-900/30"
                  }`}
                >
                  {msg.content}
                </p>
                {msg.bookmarks?.map((b) => (
                  <a
                    key={b.url}
                    href={b.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block text-xs text-blue-300 truncate hover:underline"
                  >
                    {b.title ?? b.url}
                  </a>
                ))}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex items-center gap-2 text-slate-500 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" /> Thinking…
            </div>
          )}
        </CardContent>
        <div className="p-4 border-t border-slate-800 bg-slate-900/30">
          <div className="flex gap-2">
            <input
              className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500"
              placeholder="Enter a bookmark command..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              disabled={loading}
            />
            <Button
              size="icon"
              className="bg-blue-600 hover:bg-blue-700"
              onClick={send}
              disabled={loading}
            >
              <Send className="h-4 w-4 text-white" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
