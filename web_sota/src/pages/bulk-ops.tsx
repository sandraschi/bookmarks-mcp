import { Copy, Link2Off, Loader2, RefreshCw, Tags } from "lucide-react";
import { useState } from "react";
import { downloadBookmarkExport } from "@/common/api";
import {
  cleanUpTags,
  exportBookmarks,
  findBrokenLinks,
  findDuplicates,
  listTags,
  syncBrowsers,
} from "@/common/bookmark-ops";
import { useBookmarkSettings } from "@/common/bookmark-settings";
import { BROWSERS, type BrowserName, isSuccess } from "@/common/bookmark-types";
import { BrowserBar } from "@/components/bookmarks/browser-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";

function ResultPanel({ data }: { data: unknown }) {
  if (data == null) return null;
  return (
    <pre className="mt-4 p-3 text-xs font-mono rounded bg-slate-950 border border-slate-800 overflow-auto max-h-96 text-slate-300">
      {typeof data === "string" ? data : JSON.stringify(data, null, 2)}
    </pre>
  );
}

export function BulkOpsPage() {
  const { callOptions, browser } = useBookmarkSettings();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<unknown>(null);

  const [syncTarget, setSyncTarget] = useState<BrowserName>("chrome");
  const [syncDryRun, setSyncDryRun] = useState(true);
  const [syncStep, setSyncStep] = useState(1);
  const [tagsDryRun, setTagsDryRun] = useState(true);

  const run = async (fn: () => Promise<Record<string, unknown>>) => {
    setLoading(true);
    setProgress(30);
    setError(null);
    setResult(null);
    try {
      setProgress(60);
      const data = await fn();
      setProgress(100);
      if (!isSuccess(data)) {
        setError(String(data.error ?? data.message ?? "Operation failed"));
        toast({
          title: "Operation failed",
          description: String(data.error),
          variant: "error",
        });
      } else {
        toast({ title: "Operation complete", variant: "success" });
      }
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Operation failed");
      toast({
        title: "Operation failed",
        description: err instanceof Error ? err.message : "Error",
        variant: "error",
      });
    } finally {
      setLoading(false);
      window.setTimeout(() => setProgress(null), 800);
    }
  };

  const runExportDownload = async () => {
    setLoading(true);
    setProgress(40);
    try {
      await downloadBookmarkExport(browser, callOptions.profileName);
      toast({ title: "Export downloaded", variant: "success" });
    } catch (err) {
      toast({
        title: "Export failed",
        description: err instanceof Error ? err.message : "Error",
        variant: "error",
      });
    } finally {
      setLoading(false);
      setProgress(null);
    }
  };

  const firefoxOnly = browser !== "firefox";

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Bulk operations
        </h2>
        <p className="text-slate-400">
          Duplicates, export, tags, broken links, and cross-browser sync
        </p>
      </div>

      <BrowserBar />

      {error && <p className="text-red-400 text-sm">{error}</p>}
      {progress != null && <Progress value={progress} className="h-2" />}

      <Tabs defaultValue="sync" className="space-y-4">
        <TabsList className="bg-slate-900 border border-slate-800">
          <TabsTrigger value="sync">Sync</TabsTrigger>
          <TabsTrigger value="duplicates">Duplicates</TabsTrigger>
          <TabsTrigger value="export">Export</TabsTrigger>
          <TabsTrigger value="tags">Tags</TabsTrigger>
          <TabsTrigger value="broken">Broken links</TabsTrigger>
        </TabsList>

        <TabsContent value="sync">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <RefreshCw className="h-5 w-5 text-blue-400" /> Cross-browser
                sync
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <ol className="flex gap-4 text-sm">
                {[1, 2, 3].map((step) => (
                  <li
                    key={step}
                    className={`px-3 py-1 rounded border ${
                      syncStep === step
                        ? "border-blue-600 text-blue-300 bg-blue-950/30"
                        : "border-slate-800 text-slate-500"
                    }`}
                  >
                    Step {step}
                  </li>
                ))}
              </ol>
              <p className="text-sm text-slate-400">
                Copy bookmarks from the selected browser (top bar) to another
                browser.
              </p>
              {syncStep === 1 && (
                <div className="flex flex-wrap gap-4 items-end">
                  <div className="grid gap-2 min-w-[160px]">
                    <Label className="text-slate-300">Target browser</Label>
                    <Select
                      value={syncTarget}
                      onValueChange={(v: string) =>
                        setSyncTarget(v as BrowserName)
                      }
                    >
                      <SelectTrigger className="bg-slate-900 border-slate-800">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent className="bg-slate-900 border-slate-800">
                        {BROWSERS.filter((b) => b.value !== browser).map(
                          (b) => (
                            <SelectItem key={b.value} value={b.value}>
                              {b.label}
                            </SelectItem>
                          ),
                        )}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={syncDryRun}
                      onCheckedChange={setSyncDryRun}
                      id="sync-dry"
                    />
                    <Label htmlFor="sync-dry" className="text-slate-300">
                      Dry run
                    </Label>
                  </div>
                  <Button
                    disabled={loading || syncTarget === browser}
                    onClick={() => setSyncStep(2)}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    Next: preview
                  </Button>
                </div>
              )}
              {syncStep === 2 && (
                <div className="flex flex-wrap gap-4 items-end">
                  <p className="text-sm text-slate-300 w-full">
                    Dry-run sync from {browser} → {syncTarget}
                  </p>
                  <Button
                    disabled={loading || syncTarget === browser}
                    onClick={async () => {
                      await run(() => syncBrowsers(browser, syncTarget, true));
                      setSyncStep(3);
                    }}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    {loading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      "Run dry-run"
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    className="border-slate-800"
                    onClick={() => setSyncStep(1)}
                  >
                    Back
                  </Button>
                </div>
              )}
              {syncStep === 3 && (
                <div className="flex flex-wrap gap-4 items-end">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={syncDryRun}
                      onCheckedChange={setSyncDryRun}
                      id="sync-dry"
                    />
                    <Label htmlFor="sync-dry" className="text-slate-300">
                      Dry run (off = live sync)
                    </Label>
                  </div>
                  <Button
                    disabled={loading || syncTarget === browser}
                    onClick={() =>
                      run(() => syncBrowsers(browser, syncTarget, syncDryRun))
                    }
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    {loading ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      "Execute sync"
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    className="border-slate-800"
                    onClick={() => setSyncStep(2)}
                  >
                    Back
                  </Button>
                </div>
              )}
              <ResultPanel data={result} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="duplicates">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Copy className="h-5 w-5 text-amber-400" /> Find duplicates
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {firefoxOnly && (
                <p className="text-amber-400 text-sm">
                  Duplicate detection is Firefox-only. Switch browser to
                  Firefox.
                </p>
              )}
              <Button
                disabled={loading || firefoxOnly}
                onClick={() => run(() => findDuplicates(callOptions))}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Scan duplicates"
                )}
              </Button>
              <ResultPanel data={result} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="export">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white">Export bookmarks</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {firefoxOnly && (
                <p className="text-amber-400 text-sm">
                  Full export is Firefox-only in this tool surface.
                </p>
              )}
              <Button
                disabled={loading}
                onClick={runExportDownload}
                className="bg-blue-600 hover:bg-blue-700 mr-2"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Download JSON"
                )}
              </Button>
              <Button
                disabled={loading || firefoxOnly}
                onClick={() => run(() => exportBookmarks(callOptions, "json"))}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Export JSON"
                )}
              </Button>
              <ResultPanel data={result} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tags">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Tags className="h-5 w-5 text-purple-400" /> Tag management
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {firefoxOnly && (
                <p className="text-amber-400 text-sm">
                  Tag tools are Firefox-only.
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                <Button
                  disabled={loading || firefoxOnly}
                  variant="outline"
                  className="border-slate-800"
                  onClick={() => run(() => listTags(callOptions))}
                >
                  List tags
                </Button>
                <div className="flex items-center gap-2">
                  <Switch
                    checked={tagsDryRun}
                    onCheckedChange={setTagsDryRun}
                    id="tags-dry"
                  />
                  <Label htmlFor="tags-dry" className="text-slate-300">
                    Dry run cleanup
                  </Label>
                </div>
                <Button
                  disabled={loading || firefoxOnly}
                  onClick={() =>
                    run(() => cleanUpTags(callOptions, tagsDryRun))
                  }
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  Clean up tags
                </Button>
              </div>
              <ResultPanel data={result} />
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="broken">
          <Card className="border-slate-800 bg-slate-950/50">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Link2Off className="h-5 w-5 text-red-400" /> Broken links
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {firefoxOnly && (
                <p className="text-amber-400 text-sm">
                  Broken link scan is Firefox-only.
                </p>
              )}
              <Button
                disabled={loading || firefoxOnly}
                onClick={() => run(() => findBrokenLinks(callOptions, 25))}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {loading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Check links (sample)"
                )}
              </Button>
              <ResultPanel data={result} />
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
