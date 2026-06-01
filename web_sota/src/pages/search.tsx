import {
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Loader2,
  Search,
} from "lucide-react";
import { useState } from "react";
import { searchBookmarks } from "@/common/bookmark-ops";
import { useBookmarkSettings } from "@/common/bookmark-settings";
import type { BookmarkRow } from "@/common/bookmark-types";
import {
  hasMorePages,
  isSuccess,
  normalizeBookmarks,
  totalBookmarkCount,
} from "@/common/bookmark-types";
import { BrowserBar } from "@/components/bookmarks/browser-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/toast";

function filterRows(
  rows: BookmarkRow[],
  folder: string,
  tag: string,
): BookmarkRow[] {
  let out = rows;
  if (folder.trim()) {
    const f = folder.trim().toLowerCase();
    out = out.filter((r) =>
      String(r.folder ?? r.parent ?? "")
        .toLowerCase()
        .includes(f),
    );
  }
  if (tag.trim()) {
    const t = tag.trim().toLowerCase();
    out = out.filter((r) => r.tags?.some((x) => x.toLowerCase().includes(t)));
  }
  return out;
}

export function SearchPage() {
  const { callOptions, browser } = useBookmarkSettings();
  const { toast } = useToast();
  const [query, setQuery] = useState("");
  const [folderFilter, setFolderFilter] = useState("");
  const [tagFilter, setTagFilter] = useState("");
  const [limit, setLimit] = useState(100);
  const [offset, setOffset] = useState(0);
  const [rows, setRows] = useState<BookmarkRow[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const runSearch = async (pageOffset = 0) => {
    if (!query.trim()) {
      toast({ title: "Enter a query", variant: "error" });
      return;
    }
    setLoading(true);
    setSearched(true);
    try {
      const extra: Record<string, unknown> = {};
      if (browser === "firefox" && tagFilter.trim()) {
        extra.tags = [tagFilter.trim()];
      }
      const data = await searchBookmarks(
        callOptions,
        query.trim(),
        limit,
        pageOffset,
        extra,
      );
      if (!isSuccess(data)) {
        toast({
          title: "Search failed",
          description: String(data.error ?? data.message ?? "Search failed"),
          variant: "error",
        });
        setRows([]);
        return;
      }
      const normalized = filterRows(
        normalizeBookmarks(data),
        folderFilter,
        tagFilter,
      );
      setRows(normalized);
      setTotal(totalBookmarkCount(data));
      setOffset(pageOffset);
      setHasMore(hasMorePages(data));
    } catch (err) {
      toast({
        title: "Search failed",
        description: err instanceof Error ? err.message : "Search failed",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">Search</h2>
        <p className="text-slate-400">
          Find bookmarks by title, URL, folder, or tag
        </p>
      </div>

      <BrowserBar />

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Search className="h-5 w-5 text-blue-400" /> Query
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 items-end">
          <div className="grid gap-2 lg:col-span-2">
            <Label className="text-slate-300">Search text</Label>
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && runSearch(0)}
              placeholder="title or URL fragment"
              className="bg-slate-900 border-slate-800"
            />
          </div>
          <div className="grid gap-2">
            <Label className="text-slate-300">Folder contains</Label>
            <Input
              value={folderFilter}
              onChange={(e) => setFolderFilter(e.target.value)}
              placeholder="optional"
              className="bg-slate-900 border-slate-800"
            />
          </div>
          <div className="grid gap-2">
            <Label className="text-slate-300">Tag (Firefox)</Label>
            <Input
              value={tagFilter}
              onChange={(e) => setTagFilter(e.target.value)}
              placeholder="optional"
              className="bg-slate-900 border-slate-800"
              disabled={browser !== "firefox"}
            />
          </div>
          <div className="grid gap-2 w-28">
            <Label className="text-slate-300">Limit</Label>
            <Input
              type="number"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value) || 100)}
              className="bg-slate-900 border-slate-800"
            />
          </div>
          <Button
            onClick={() => runSearch(0)}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700"
          >
            {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Search"}
          </Button>
        </CardContent>
      </Card>

      {searched && (
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-white">
              {rows.length} shown / {total} matched
            </CardTitle>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="border-slate-800"
                disabled={loading || offset === 0}
                onClick={() => runSearch(Math.max(0, offset - limit))}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="border-slate-800"
                disabled={loading || !hasMore}
                onClick={() => runSearch(offset + limit)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {rows.map((row) => (
              <div
                key={String(row.id ?? row.url)}
                className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/40 border border-slate-800"
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-slate-200 truncate">
                    {row.title || "(untitled)"}
                  </p>
                  <p className="text-xs text-slate-500 truncate">{row.url}</p>
                  {(row.folder || row.parent) && (
                    <p className="text-xs text-slate-600 mt-0.5">
                      Folder: {row.folder ?? row.parent}
                    </p>
                  )}
                  {row.tags && row.tags.length > 0 && (
                    <p className="text-xs text-purple-400 mt-0.5">
                      Tags: {row.tags.join(", ")}
                    </p>
                  )}
                </div>
                {row.url && (
                  <a
                    href={row.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-slate-500 hover:text-blue-400"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </a>
                )}
              </div>
            ))}
            {!loading && rows.length === 0 && (
              <p className="text-slate-500 text-sm py-4 text-center">
                No matches
              </p>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
