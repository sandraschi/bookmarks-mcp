import { Loader2, Tags } from "lucide-react";
import { useState } from "react";
import { cleanUpTags, listTags } from "@/common/bookmark-ops";
import { useBookmarkSettings } from "@/common/bookmark-settings";
import { isSuccess } from "@/common/bookmark-types";
import { BrowserBar } from "@/components/bookmarks/browser-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/components/ui/toast";

export function TagsPage() {
  const { callOptions, browser } = useBookmarkSettings();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [tags, setTags] = useState<string[]>([]);
  const [dryRun, setDryRun] = useState(true);
  const firefoxOnly = browser !== "firefox";

  const loadTags = async () => {
    setLoading(true);
    try {
      const data = await listTags(callOptions);
      if (!isSuccess(data)) {
        toast({
          title: "List tags failed",
          description: String(data.error ?? "Unknown error"),
          variant: "error",
        });
        return;
      }
      const raw = data.tags ?? data.results ?? [];
      const names = Array.isArray(raw)
        ? raw.map((t) =>
            typeof t === "string"
              ? t
              : String((t as { name?: string }).name ?? t),
          )
        : [];
      setTags(names);
      toast({
        title: "Tags loaded",
        description: `${names.length} tag(s)`,
        variant: "success",
      });
    } catch (err) {
      toast({
        title: "List tags failed",
        description: err instanceof Error ? err.message : "Error",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const runCleanup = async () => {
    setLoading(true);
    try {
      const data = await cleanUpTags(callOptions, dryRun);
      if (!isSuccess(data)) {
        toast({
          title: "Cleanup failed",
          description: String(data.error ?? "Unknown error"),
          variant: "error",
        });
        return;
      }
      toast({
        title: dryRun ? "Dry run complete" : "Tags cleaned",
        description: String(data.message ?? "Done"),
        variant: "success",
      });
    } catch (err) {
      toast({
        title: "Cleanup failed",
        description: err instanceof Error ? err.message : "Error",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Tags</h2>
        <p className="text-slate-400">Firefox tag inventory and cleanup</p>
      </div>

      <BrowserBar />

      {firefoxOnly && (
        <p className="text-amber-400 text-sm">
          Tag management is Firefox-only. Switch browser in the bar above.
        </p>
      )}

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Tags className="h-5 w-5 text-purple-400" /> Tag manager
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button
              disabled={loading || firefoxOnly}
              onClick={loadTags}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Load tags"
              )}
            </Button>
            <div className="flex items-center gap-2">
              <Switch
                checked={dryRun}
                onCheckedChange={setDryRun}
                id="tags-dry"
              />
              <Label htmlFor="tags-dry" className="text-slate-300">
                Dry run cleanup
              </Label>
            </div>
            <Button
              disabled={loading || firefoxOnly}
              variant="outline"
              className="border-slate-800"
              onClick={runCleanup}
            >
              Clean up unused tags
            </Button>
          </div>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag) => (
              <span
                key={tag}
                className="px-2 py-1 rounded text-xs bg-purple-950/40 border border-purple-900/50 text-purple-200"
              >
                {tag}
              </span>
            ))}
            {!loading && tags.length === 0 && (
              <p className="text-sm text-slate-500">No tags loaded</p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
