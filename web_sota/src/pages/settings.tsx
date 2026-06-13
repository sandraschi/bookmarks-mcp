import { Cpu, RefreshCw, Save, Shield } from "lucide-react";
import { useEffect, useState } from "react";
import {
  getHealth,
  getStoredAuth,
  setStoredAuth,
} from "@/common/api";
import { useBookmarkSettings } from "@/common/bookmark-settings";
import { BROWSERS } from "@/common/bookmark-types";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

function LLMSettings() {
    const [providers, setProviders] = useState<Record<string, {name:string}[]>>({});
    const [selectedProvider, setSelectedProvider] = useState("ollama");
    const [selectedModel, setSelectedModel] = useState("");
    useEffect(() => {
        fetch("/api/llm/providers").then(r => r.json()).then(d => {
            setProviders(d);
            const savedP = localStorage.getItem("llm_provider") || "ollama";
            const savedM = localStorage.getItem("llm_model") || "";
            setSelectedProvider(savedP);
            const models = d[savedP === "ollama" ? "ollama" : "lm_studio"] || [];
            setSelectedModel(savedM && models.some((m:{name:string}) => m.name === savedM) ? savedM : (models[0]?.name || ""));
        }).catch(() => {
            setProviders({ ollama: [{name:"llama3.2:3b"}] });
            setSelectedModel(localStorage.getItem("llm_model") || "llama3.2:3b");
        });
    }, []);
    const save = (p:string, m:string) => { localStorage.setItem("llm_provider", p); localStorage.setItem("llm_model", m); };
    const models = providers[selectedProvider === "ollama" ? "ollama" : "lm_studio"] || [];
    return (
        <div className="space-y-3">
            <Select value={selectedProvider} onValueChange={(v) => { setSelectedProvider(v); save(v, ""); }}>
                <SelectTrigger className="bg-slate-900 border-slate-800 text-slate-100">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                    <SelectItem value="ollama">Ollama</SelectItem>
                    <SelectItem value="lm_studio">LM Studio</SelectItem>
                </SelectContent>
            </Select>
            <Select value={selectedModel} onValueChange={(v) => { setSelectedModel(v); save(selectedProvider, v); }}>
                <SelectTrigger className="bg-slate-900 border-slate-800 text-slate-100">
                    <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
                    {models.map((m) => <SelectItem key={m.name} value={m.name}>{m.name}</SelectItem>)}
                </SelectContent>
            </Select>
        </div>
    );
}

export function Settings() {
  const {
    browser,
    profileName,
    forceAccess,
    setBrowser,
    setProfileName,
    setForceAccess,
  } = useBookmarkSettings();
  const [webUser, setWebUser] = useState(() => getStoredAuth()?.username ?? "");
  const [webPass, setWebPass] = useState(() => getStoredAuth()?.password ?? "");
  const [apiStatus, setApiStatus] = useState<string | null>(null);

  const saveWebAuth = () => {
    if (webUser) {
      setStoredAuth({ username: webUser, password: webPass });
    } else {
      setStoredAuth(null);
    }
    setApiStatus("Credentials saved locally");
  };

  const testApi = async () => {
    setApiStatus("Testing…");
    try {
      await getHealth();
      setApiStatus("API reachable");
    } catch (err) {
      setApiStatus(err instanceof Error ? err.message : "API test failed");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Settings
        </h2>
        <p className="text-slate-400">
          Browser defaults, API auth, and LLM preferences
        </p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Default browser</CardTitle>
          <CardDescription className="text-slate-400">
            Used across CRUD, search, tree, and bulk pages
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3">
          <div className="grid gap-2">
            <Label className="text-slate-300">Browser</Label>
            <Select
              value={browser}
              onValueChange={(v: string) => setBrowser(v as typeof browser)}
            >
              <SelectTrigger className="bg-slate-900 border-slate-800">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800">
                {BROWSERS.map((b) => (
                  <SelectItem key={b.value} value={b.value}>
                    {b.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          {browser === "firefox" && (
            <>
              <div className="grid gap-2">
                <Label className="text-slate-300">Profile name</Label>
                <Input
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  className="bg-slate-900 border-slate-800"
                />
              </div>
              <div className="flex items-center gap-2 pt-6">
                <input
                  type="checkbox"
                  checked={forceAccess}
                  onChange={(e) => setForceAccess(e.target.checked)}
                  id="settings-force"
                  className="rounded"
                />
                <Label htmlFor="settings-force" className="text-slate-300">
                  Force Firefox DB access
                </Label>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-emerald-500" />
            <CardTitle className="text-white">Web API authentication</CardTitle>
          </div>
          <CardDescription className="text-slate-400">
            Default backend credentials: admin / mcp. Set BOOKMARKS_WEB_AUTH=0
            to disable auth in dev.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="grid gap-2">
              <Label className="text-slate-300">Username</Label>
              <Input
                value={webUser}
                onChange={(e) => setWebUser(e.target.value)}
                className="bg-slate-900 border-slate-800"
              />
            </div>
            <div className="grid gap-2">
              <Label className="text-slate-300">Password</Label>
              <Input
                type="password"
                value={webPass}
                onChange={(e) => setWebPass(e.target.value)}
                className="bg-slate-900 border-slate-800"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={saveWebAuth}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Save className="mr-2 h-4 w-4" /> Save credentials
            </Button>
            <Button
              variant="outline"
              onClick={testApi}
              className="border-slate-800"
            >
              <RefreshCw className="mr-2 h-4 w-4" /> Test API
            </Button>
          </div>
          {apiStatus && <p className="text-sm text-slate-400">{apiStatus}</p>}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-blue-500" />
            <CardTitle className="text-white">
              Local LLM Configuration
            </CardTitle>
          </div>
          <CardDescription className="text-slate-400">
            Used by AI Command page
          </CardDescription>
        </CardHeader>
        <CardContent>
          <LLMSettings />
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">App Information</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-slate-400 space-y-1">
          <p>Bookmarks MCP v0.2.0 (SOTA)</p>
          <p>Frontend: 10802 · Backend: 10803</p>
        </CardContent>
      </Card>
    </div>
  );
}
