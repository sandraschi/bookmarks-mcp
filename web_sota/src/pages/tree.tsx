import { FolderTree, Loader2, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { type BookmarkTreeNode, getBookmarkTree } from "@/common/api";
import { useBookmarkSettings } from "@/common/bookmark-settings";
import { BrowserBar } from "@/components/bookmarks/browser-bar";
import { TreeNode } from "@/components/bookmarks/tree-node";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";

export function TreePage() {
  const { browser, profileName } = useBookmarkSettings();
  const [tree, setTree] = useState<BookmarkTreeNode[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getBookmarkTree(browser, profileName || undefined);
      if (!data.success) {
        setError(data.error ?? "Failed to load tree");
        setTree([]);
        return;
      }
      setTree(data.tree ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Tree load failed");
      setTree([]);
    } finally {
      setLoading(false);
    }
  }, [browser, profileName]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Bookmark tree
          </h2>
          <p className="text-slate-400">
            Folder hierarchy for the active browser profile
          </p>
        </div>
        <Button
          variant="outline"
          onClick={load}
          disabled={loading}
          className="border-slate-800"
        >
          <RefreshCw
            className={`h-4 w-4 mr-2 ${loading ? "animate-spin" : ""}`}
          />
          Refresh
        </Button>
      </div>

      <BrowserBar />

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FolderTree className="h-5 w-5 text-amber-400" /> Folders
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && <p className="text-red-400 text-sm mb-4">{error}</p>}
          {loading && (
            <div className="flex items-center gap-2 text-slate-400 py-8 justify-center">
              <Loader2 className="h-5 w-5 animate-spin" /> Loading tree…
            </div>
          )}
          {!loading && tree.length === 0 && !error && (
            <p className="text-slate-500 text-sm py-8 text-center">
              No folder data
            </p>
          )}
          {!loading && tree.length > 0 && (
            <ScrollArea className="h-[min(70vh,720px)] pr-4">
              {tree.map((node, idx) => (
                <TreeNode
                  key={`${node.path ?? node.name ?? idx}`}
                  node={node}
                />
              ))}
            </ScrollArea>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
