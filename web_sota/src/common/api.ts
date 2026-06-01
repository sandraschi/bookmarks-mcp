/**
 * REST bridge to bookmarks-mcp backend (proxied via Vite in dev).
 */

export interface HealthResponse {
  status: string;
  mcp?: string;
  server?: string;
}

export interface McpTool {
  name: string;
  description: string | null;
  inputSchema?: Record<string, unknown>;
}

export interface ToolsResponse {
  tools: McpTool[];
}

export interface ToolCallResponse {
  result: unknown;
  isError?: boolean;
}

export interface BookmarkTreeNode {
  type: "folder" | "bookmark";
  id?: string | number;
  name?: string;
  path?: string;
  title?: string;
  url?: string;
  children?: BookmarkTreeNode[];
}

export interface BookmarkTreeResponse {
  success: boolean;
  browser?: string;
  tree?: BookmarkTreeNode[];
  error?: string;
}

export interface ActivityEntry {
  id: string;
  timestamp: string;
  kind: string;
  detail: string;
  meta?: Record<string, unknown>;
}

export interface ActivityResponse {
  entries: ActivityEntry[];
}

export interface AiChatRequest {
  message: string;
  provider?: string;
  model?: string;
  endpoint?: string;
}

export interface AiChatResponse {
  response: string;
  tool_calls?: string[];
}

const API = "/api";
const AUTH_KEY = "bookmarks-web-auth";
const LLM_KEY = "bookmarks-llm-settings";

export interface LlmSettings {
  provider: string;
  model: string;
  endpoint: string;
}

export interface WebAuth {
  username: string;
  password: string;
}

export function getStoredAuth(): WebAuth | null {
  try {
    const raw = localStorage.getItem(AUTH_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as WebAuth;
  } catch {
    return null;
  }
}

export function setStoredAuth(auth: WebAuth | null): void {
  if (!auth?.username) {
    localStorage.removeItem(AUTH_KEY);
    return;
  }
  localStorage.setItem(AUTH_KEY, JSON.stringify(auth));
}

export function getLlmSettings(): LlmSettings {
  try {
    const raw = localStorage.getItem(LLM_KEY);
    if (raw) return JSON.parse(raw) as LlmSettings;
  } catch {
    /* ignore */
  }
  return {
    provider: "ollama",
    model: "gemini-2.0-flash-exp",
    endpoint: "http://localhost:11434",
  };
}

export function setLlmSettings(settings: LlmSettings): void {
  localStorage.setItem(LLM_KEY, JSON.stringify(settings));
}

function authHeaders(): HeadersInit {
  const auth = getStoredAuth();
  if (!auth?.username) return {};
  const token = btoa(`${auth.username}:${auth.password}`);
  return { Authorization: `Basic ${token}` };
}

async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  const auth = authHeaders();
  for (const [key, value] of Object.entries(auth)) {
    headers.set(key, value);
  }
  return fetch(`${API}${path}`, { ...init, headers });
}

export async function getHealth(): Promise<HealthResponse> {
  const r = await apiFetch("/health");
  if (!r.ok) throw new Error(`Health check failed: ${r.status}`);
  return r.json();
}

export async function getTools(): Promise<ToolsResponse> {
  const r = await apiFetch("/tools");
  if (!r.ok) throw new Error(`Tools list failed: ${r.status}`);
  return r.json();
}

export async function callTool(
  name: string,
  args: Record<string, unknown>,
): Promise<ToolCallResponse> {
  const r = await apiFetch("/tools/call", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, arguments: args }),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(text || `Tool call failed: ${r.status}`);
  }
  return r.json();
}

export async function getBookmarkTree(
  browser: string,
  profileName?: string,
): Promise<BookmarkTreeResponse> {
  const params = new URLSearchParams({ browser });
  if (profileName) params.set("profile_name", profileName);
  const r = await apiFetch(`/bookmarks/tree?${params.toString()}`);
  if (!r.ok) throw new Error(`Tree fetch failed: ${r.status}`);
  return r.json();
}

export async function getActivity(limit = 50): Promise<ActivityResponse> {
  const r = await apiFetch(`/activity?limit=${limit}`);
  if (!r.ok) throw new Error(`Activity fetch failed: ${r.status}`);
  return r.json();
}

export async function postAiChat(body: AiChatRequest): Promise<AiChatResponse> {
  const r = await apiFetch("/ai/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(text || `AI chat failed: ${r.status}`);
  }
  return r.json();
}

export async function downloadBookmarkExport(
  browser: string,
  profileName?: string,
): Promise<void> {
  const r = await apiFetch("/bookmarks/export", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      browser,
      profile_name: profileName,
      export_format: "json",
    }),
  });
  if (!r.ok) throw new Error(`Export failed: ${r.status}`);
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${browser}-bookmarks.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

export function unwrapToolResult(
  response: ToolCallResponse,
): Record<string, unknown> {
  const payload = response.result;
  if (payload && typeof payload === "object" && !Array.isArray(payload)) {
    return payload as Record<string, unknown>;
  }
  return { success: !response.isError, result: payload };
}
