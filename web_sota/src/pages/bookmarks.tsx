import {
  ChevronLeft,
  ChevronRight,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Trash2,
} from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  addBookmark,
  deleteBookmark,
  deleteBookmarkByUrl,
  editBookmark,
  editBookmarkByUrl,
  listBookmarks,
} from "@/common/bookmark-ops";
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

export function BookmarksPage() {
  const { callOptions } = useBookmarkSettings();
  const { toast } = useToast();
  const [rows, setRows] = useState<BookmarkRow[]>([]);
  const [total, setTotal] = useState(0);
  const [limit, setLimit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);

  const [newTitle, setNewTitle] = useState("");
  const [newUrl, setNewUrl] = useState("");
  const [newFolder, setNewFolder] = useState("");

  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editFolder, setEditFolder] = useState("");
  const [editUrl, setEditUrl] = useState("");

  const load = useCallback(
    async (pageOffset = 0) => {
      setLoading(true);
      try {
        const data = await listBookmarks(
          callOptions,
          limit,
          undefined,
          pageOffset,
        );
        if (!isSuccess(data)) {
          toast({
            title: "Load failed",
            description: String(
              data.error ?? data.message ?? "Failed to load bookmarks",
            ),
            variant: "error",
          });
          setRows([]);
          return;
        }
        setRows(normalizeBookmarks(data));
        setTotal(totalBookmarkCount(data));
        setOffset(pageOffset);
        setHasMore(hasMorePages(data));
      } catch (err) {
        toast({
          title: "Load failed",
          description: err instanceof Error ? err.message : "Load failed",
          variant: "error",
        });
      } finally {
        setLoading(false);
      }
    },
    [callOptions, limit, toast],
  );

  useEffect(() => {
    load(0);
  }, [load]);

  const handleAdd = async () => {
    if (!newTitle.trim() || !newUrl.trim()) {
      toast({
        title: "Missing fields",
        description: "Title and URL are required",
        variant: "error",
      });
      return;
    }
    setLoading(true);
    try {
      const result = await addBookmark(
        callOptions,
        newTitle.trim(),
        newUrl.trim(),
        newFolder || undefined,
      );
      if (!isSuccess(result)) {
        toast({
          title: "Add failed",
          description: String(result.error ?? "Add failed"),
          variant: "error",
        });
        return;
      }
      toast({ title: "Bookmark added", variant: "success" });
      setNewTitle("");
      setNewUrl("");
      setNewFolder("");
      await load(0);
    } catch (err) {
      toast({
        title: "Add failed",
        description: err instanceof Error ? err.message : "Add failed",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (row: BookmarkRow) => {
    setEditingKey(String(row.id ?? row.url ?? ""));
    setEditTitle(row.title ?? "");
    setEditFolder(typeof row.folder === "string" ? row.folder : "");
    setEditUrl(row.url ?? "");
  };

  const handleSaveEdit = async () => {
    if (!editingKey) return;
    setLoading(true);
    try {
      const row = rows.find((r) => String(r.id ?? r.url ?? "") === editingKey);
      const hasId = row?.id != null && String(row.id) !== "";
      const result =
        hasId && row?.id != null
          ? await editBookmark(
              callOptions,
              String(row.id),
              editTitle || undefined,
              editFolder || undefined,
            )
          : await editBookmarkByUrl(
              callOptions,
              editUrl || row?.url || "",
              editTitle || undefined,
              editFolder || undefined,
            );
      if (!isSuccess(result)) {
        toast({
          title: "Edit failed",
          description: String(result.error ?? "Edit failed"),
          variant: "error",
        });
        return;
      }
      toast({ title: "Bookmark updated", variant: "success" });
      setEditingKey(null);
      await load(offset);
    } catch (err) {
      toast({
        title: "Edit failed",
        description: err instanceof Error ? err.message : "Edit failed",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (row: BookmarkRow) => {
    const id = row.id != null ? String(row.id) : "";
    const url = row.url;
    if (!id && !url) {
      toast({
        title: "Cannot delete",
        description: "No id or URL on this row",
        variant: "error",
      });
      return;
    }
    if (!window.confirm(`Delete "${row.title ?? row.url}"?`)) return;
    setLoading(true);
    try {
      const result = id
        ? await deleteBookmark(callOptions, id)
        : await deleteBookmarkByUrl(callOptions, url ?? "");
      if (!isSuccess(result)) {
        toast({
          title: "Delete failed",
          description: String(result.error ?? "Delete failed"),
          variant: "error",
        });
        return;
      }
      toast({ title: "Bookmark deleted", variant: "success" });
      await load(offset);
    } catch (err) {
      toast({
        title: "Delete failed",
        description: err instanceof Error ? err.message : "Delete failed",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Bookmarks
        </h2>
        <p className="text-slate-400">
          Create, read, update, and delete bookmarks
        </p>
      </div>

      <BrowserBar />

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Plus className="h-5 w-5 text-blue-400" /> Add bookmark
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-4">
          <div className="grid gap-2">
            <Label className="text-slate-300">Title</Label>
            <Input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              className="bg-slate-900 border-slate-800"
            />
          </div>
          <div className="grid gap-2 md:col-span-2">
            <Label className="text-slate-300">URL</Label>
            <Input
              value={newUrl}
              onChange={(e) => setNewUrl(e.target.value)}
              className="bg-slate-900 border-slate-800"
            />
          </div>
          <div className="grid gap-2">
            <Label className="text-slate-300">Folder</Label>
            <Input
              value={newFolder}
              onChange={(e) => setNewFolder(e.target.value)}
              className="bg-slate-900 border-slate-800"
            />
          </div>
          <div className="md:col-span-4">
            <Button
              onClick={handleAdd}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "Add bookmark"
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-white">
            Bookmarks ({total}) — page {Math.floor(offset / limit) + 1}
          </CardTitle>
          <div className="flex items-center gap-2">
            <Input
              type="number"
              min={10}
              max={500}
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value) || 50)}
              className="w-24 bg-slate-900 border-slate-800"
            />
            <Button
              variant="outline"
              onClick={() => load(offset)}
              disabled={loading}
              className="border-slate-800"
            >
              <RefreshCw
                className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
              />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-slate-500 border-b border-slate-800">
                  <th className="pb-2 pr-4">Title</th>
                  <th className="pb-2 pr-4">URL</th>
                  <th className="pb-2 pr-4">Folder</th>
                  <th className="pb-2 w-28">Actions</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => {
                  const key = String(row.id ?? row.url ?? Math.random());
                  const isEditing =
                    editingKey === String(row.id ?? row.url ?? "");
                  return (
                    <tr key={key} className="border-b border-slate-900/80">
                      <td className="py-2 pr-4 text-slate-200 max-w-[200px]">
                        {isEditing ? (
                          <Input
                            value={editTitle}
                            onChange={(e) => setEditTitle(e.target.value)}
                            className="bg-slate-900 border-slate-800 h-8"
                          />
                        ) : (
                          row.title || "(untitled)"
                        )}
                      </td>
                      <td className="py-2 pr-4 text-slate-400 max-w-[280px] truncate">
                        <a
                          href={row.url}
                          target="_blank"
                          rel="noreferrer"
                          className="hover:text-blue-400"
                        >
                          {row.url}
                        </a>
                      </td>
                      <td className="py-2 pr-4 text-slate-500">
                        {isEditing ? (
                          <Input
                            value={editFolder}
                            onChange={(e) => setEditFolder(e.target.value)}
                            className="bg-slate-900 border-slate-800 h-8"
                          />
                        ) : (
                          (row.folder ?? row.parent ?? "—")
                        )}
                      </td>
                      <td className="py-2">
                        <div className="flex gap-1">
                          {isEditing ? (
                            <Button
                              size="sm"
                              onClick={handleSaveEdit}
                              className="h-8 bg-blue-600"
                            >
                              Save
                            </Button>
                          ) : (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => startEdit(row)}
                              className="h-8"
                            >
                              <Pencil className="h-3.5 w-3.5" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => handleDelete(row)}
                            className="h-8 text-red-400 hover:text-red-300"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
                {!loading && rows.length === 0 && (
                  <tr>
                    <td colSpan={4} className="py-8 text-center text-slate-500">
                      No bookmarks loaded
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between mt-4">
            <Button
              variant="outline"
              className="border-slate-800"
              disabled={loading || offset === 0}
              onClick={() => load(Math.max(0, offset - limit))}
            >
              <ChevronLeft className="h-4 w-4 mr-1" /> Previous
            </Button>
            <span className="text-xs text-slate-500">
              Showing {rows.length} of {total}
            </span>
            <Button
              variant="outline"
              className="border-slate-800"
              disabled={loading || !hasMore}
              onClick={() => load(offset + limit)}
            >
              Next <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
