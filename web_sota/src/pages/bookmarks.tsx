import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  ChevronLeft,
  ChevronRight,
  Link2Off,
  Loader2,
  MessageSquare,
  Pencil,
  Plus,
  RefreshCw,
  Star,
  Trash2,
  X,
  XCircle,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AuditJob } from "@/common/audit-api";
import {
  cancelAudit,
  getAuditStatus,
  getResultsForUrls,
  runAudit,
} from "@/common/audit-api";
import {
  addBookmark,
  deleteBookmark,
  deleteBookmarkByUrl,
  editBookmark,
  editBookmarkByUrl,
  listBookmarks,
  setComment,
  setStarred,
} from "@/common/bookmark-ops";
import { useBookmarkSettings } from "@/common/bookmark-settings";
import type { BookmarkRow } from "@/common/bookmark-types";
import {
  hasMorePages,
  isSuccess,
  normalizeBookmarks,
  totalBookmarkCount,
} from "@/common/bookmark-types";
import {
  addToCollection,
  bulkAddToCollection,
  type Collection,
  listCollections,
  removeFromCollection,
} from "@/common/collections-api";
import { BrowserBar } from "@/components/bookmarks/browser-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
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
import { useToast } from "@/components/ui/toast";

type SortKey = "title" | "url" | "folder" | "starred" | "auditStatus";
type SortDir = "asc" | "desc";

const STATUS_TONE: Record<string, string> = {
  ok: "text-emerald-300 bg-emerald-500/15 border-emerald-500/40",
  redirected: "text-sky-300 bg-sky-500/15 border-sky-500/40",
  dead: "text-rose-300 bg-rose-500/15 border-rose-500/40",
  blocked: "text-amber-300 bg-amber-500/15 border-amber-500/40",
  timeout: "text-amber-300 bg-amber-500/15 border-amber-500/40",
  dns_error: "text-rose-300 bg-rose-500/15 border-rose-500/40",
};

function rowKey(row: BookmarkRow): string {
  return String(row.id ?? row.url ?? "");
}

function sortRows(
  rows: BookmarkRow[],
  key: SortKey,
  dir: SortDir,
): BookmarkRow[] {
  const factor = dir === "asc" ? 1 : -1;
  return [...rows].sort((a, b) => {
    if (key === "starred") {
      return ((a.starred ?? 0) - (b.starred ?? 0)) * factor;
    }
    const av = String(a[key] ?? "").toLowerCase();
    const bv = String(b[key] ?? "").toLowerCase();
    return av.localeCompare(bv) * factor;
  });
}

function SortHeader({
  label,
  sortKey,
  active,
  dir,
  onSort,
}: {
  label: string;
  sortKey: SortKey;
  active: boolean;
  dir: SortDir;
  onSort: (key: SortKey) => void;
}) {
  return (
    <button
      type="button"
      onClick={() => onSort(sortKey)}
      className="flex items-center gap-1 hover:text-slate-200"
    >
      {label}
      {active ? (
        dir === "asc" ? (
          <ArrowUp className="h-3 w-3" />
        ) : (
          <ArrowDown className="h-3 w-3" />
        )
      ) : (
        <ArrowUpDown className="h-3 w-3 opacity-40" />
      )}
    </button>
  );
}

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
  const [editComment, setEditComment] = useState("");

  const [collections, setCollections] = useState<Collection[]>([]);
  const [collectionFilter, setCollectionFilter] = useState<string>("all");
  const [starredOnly, setStarredOnly] = useState(false);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [sortKey, setSortKey] = useState<SortKey>("title");
  const [sortDir, setSortDir] = useState<SortDir>("asc");
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkTargetCollection, setBulkTargetCollection] = useState<string>("");
  const [auditJob, setAuditJob] = useState<AuditJob | null>(null);
  const pollRef = useRef<number | null>(null);
  const rowsRef = useRef<BookmarkRow[]>([]);

  const loadCollections = useCallback(async () => {
    try {
      setCollections(await listCollections());
    } catch {
      // Collections are supplementary here; a failed fetch shouldn't block the page.
    }
  }, []);

  const mergeAuditResults = useCallback(
    async (loadedRows: BookmarkRow[]) => {
      const urls = loadedRows.map((r) => r.url).filter((u): u is string => !!u);
      if (urls.length === 0) return;
      try {
        const results = await getResultsForUrls(urls, callOptions);
        setRows((prev) =>
          prev.map((r) => {
            const hit = r.url ? results[r.url] : undefined;
            return hit
              ? {
                  ...r,
                  auditStatus: hit.status,
                  auditCheckedAt: hit.checked_at,
                }
              : r;
          }),
        );
      } catch {
        // Audit status is supplementary; a failed fetch shouldn't block the page.
      }
    },
    [callOptions],
  );

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
        const loaded = normalizeBookmarks(data);
        setRows(loaded);
        setTotal(totalBookmarkCount(data));
        setOffset(pageOffset);
        setHasMore(hasMorePages(data));
        setSelected(new Set());
        void mergeAuditResults(loaded);
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
    [callOptions, limit, toast, mergeAuditResults],
  );

  useEffect(() => {
    load(0);
    loadCollections();
  }, [load, loadCollections]);

  useEffect(() => {
    rowsRef.current = rows;
  }, [rows]);

  const runningJobId = auditJob?.status === "running" ? auditJob.job_id : null;

  useEffect(() => {
    if (!runningJobId) {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
      return undefined;
    }
    pollRef.current = window.setInterval(async () => {
      const updated = await getAuditStatus(runningJobId);
      if (!updated) return;
      setAuditJob(updated);
      if (updated.status !== "running") {
        void mergeAuditResults(rowsRef.current);
        toast({
          title:
            updated.status === "done"
              ? "Link audit complete"
              : updated.status === "cancelled"
                ? "Link audit cancelled"
                : "Link audit failed",
          description: `${updated.checked} of ${updated.total} checked`,
          variant: updated.status === "error" ? "error" : "success",
        });
      }
    }, 1500);
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, [runningJobId, mergeAuditResults, toast]);

  const startAudit = async (scope: {
    urls?: string[];
    folderPath?: string;
  }) => {
    const started = await runAudit(callOptions, {
      ...scope,
      limit: scope.urls ? undefined : Math.max(total, 5000),
    });
    if (!started.success || !started.job_id) {
      toast({
        title: "Could not start audit",
        description: started.error ?? "Unknown error",
        variant: "error",
      });
      return;
    }
    setAuditJob({
      job_id: started.job_id,
      browser: callOptions.browser,
      profile_name: callOptions.profileName ?? null,
      status: "running",
      total: started.total ?? scope.urls?.length ?? 0,
      checked: 0,
      counts_by_status: {},
      error: null,
      started_at: new Date().toISOString(),
      finished_at: null,
    });
  };

  const handleCheckPage = () =>
    startAudit({
      urls: rows.map((r) => r.url).filter((u): u is string => !!u),
    });

  const handleScanAll = () => startAudit({});

  const handleCancelAudit = async () => {
    if (!auditJob) return;
    await cancelAudit(auditJob.job_id);
  };

  const handleBulkRecheck = async () => {
    const urls = selectedRows.map((r) => r.url).filter((u): u is string => !!u);
    if (urls.length === 0) return;
    await startAudit({ urls });
  };

  const displayedRows = useMemo(() => {
    let out = rows;
    if (starredOnly) out = out.filter((r) => (r.starred ?? 0) > 0);
    if (collectionFilter !== "all") {
      out = out.filter((r) =>
        r.collections?.some((c) => String(c.id) === collectionFilter),
      );
    }
    if (statusFilter !== "all") {
      out =
        statusFilter === "unchecked"
          ? out.filter((r) => !r.auditStatus)
          : out.filter((r) => r.auditStatus === statusFilter);
    }
    return sortRows(out, sortKey, sortDir);
  }, [rows, starredOnly, collectionFilter, statusFilter, sortKey, sortDir]);

  const handleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

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
    setEditingKey(rowKey(row));
    setEditTitle(row.title ?? "");
    setEditFolder(typeof row.folder === "string" ? row.folder : "");
    setEditUrl(row.url ?? "");
    setEditComment(row.user_comment ?? "");
  };

  const handleSaveEdit = async () => {
    if (!editingKey) return;
    setLoading(true);
    try {
      const row = rows.find((r) => rowKey(r) === editingKey);
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
      if (row?.url && editComment !== (row.user_comment ?? "")) {
        await setComment(row.url, editComment, callOptions);
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

  const toggleStar = async (row: BookmarkRow) => {
    if (!row.url) return;
    const next = (row.starred ?? 0) > 0 ? 0 : 1;
    setRows((prev) =>
      prev.map((r) => (r.url === row.url ? { ...r, starred: next } : r)),
    );
    try {
      await setStarred(row.url, next, callOptions);
    } catch {
      await load(offset);
    }
  };

  const addRowToCollection = async (row: BookmarkRow, collectionId: string) => {
    if (!row.url || !collectionId) return;
    const result = await addToCollection(
      row.url,
      Number(collectionId),
      callOptions,
    );
    if (result.success === false) {
      toast({
        title: "Could not add to collection",
        description: String(result.error ?? ""),
        variant: "error",
      });
      return;
    }
    await load(offset);
  };

  const removeRowFromCollection = async (
    row: BookmarkRow,
    collectionId: number,
  ) => {
    if (!row.url) return;
    await removeFromCollection(row.url, collectionId, callOptions);
    await load(offset);
  };

  const toggleSelected = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const selectAllOnPage = (checked: boolean) => {
    setSelected(checked ? new Set(displayedRows.map(rowKey)) : new Set());
  };

  const selectedRows = displayedRows.filter((r) => selected.has(rowKey(r)));

  const handleBulkStar = async (value: 0 | 1) => {
    setLoading(true);
    try {
      for (const row of selectedRows) {
        if (row.url) await setStarred(row.url, value, callOptions);
      }
      toast({
        title: `${selectedRows.length} bookmark(s) updated`,
        variant: "success",
      });
      await load(offset);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkAddToCollection = async () => {
    if (!bulkTargetCollection) return;
    const urls = selectedRows.map((r) => r.url).filter((u): u is string => !!u);
    if (urls.length === 0) return;
    setLoading(true);
    try {
      await bulkAddToCollection(
        urls,
        Number(bulkTargetCollection),
        callOptions,
      );
      toast({
        title: `Added ${urls.length} bookmark(s) to collection`,
        variant: "success",
      });
      await load(offset);
    } finally {
      setLoading(false);
    }
  };

  const handleBulkDelete = async () => {
    if (!window.confirm(`Delete ${selectedRows.length} selected bookmark(s)?`))
      return;
    setLoading(true);
    try {
      // Loops the existing single-delete op for now - a real batch_delete op
      // lands in a later milestone once write-lock semantics are unified.
      for (const row of selectedRows) {
        const id = row.id != null ? String(row.id) : "";
        if (id) await deleteBookmark(callOptions, id);
        else if (row.url) await deleteBookmarkByUrl(callOptions, row.url);
      }
      toast({
        title: `${selectedRows.length} bookmark(s) deleted`,
        variant: "success",
      });
      await load(offset);
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
          Star, tag into collections, comment, and organize - the browser
          doesn't do any of this for you
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
        <CardContent className="pt-6 flex flex-wrap items-center gap-4">
          <div className="grid gap-1.5">
            <Label className="text-slate-400 text-xs">Collection</Label>
            <Select
              value={collectionFilter}
              onValueChange={setCollectionFilter}
            >
              <SelectTrigger className="w-44 bg-slate-900 border-slate-800 h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800">
                <SelectItem value="all">All collections</SelectItem>
                {collections.map((c) => (
                  <SelectItem key={c.id} value={String(c.id)}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="grid gap-1.5">
            <Label className="text-slate-400 text-xs">Status</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40 bg-slate-900 border-slate-800 h-9">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800">
                <SelectItem value="all">Any status</SelectItem>
                <SelectItem value="unchecked">Unchecked</SelectItem>
                <SelectItem value="ok">Ok</SelectItem>
                <SelectItem value="redirected">Redirected</SelectItem>
                <SelectItem value="dead">Dead</SelectItem>
                <SelectItem value="blocked">Blocked</SelectItem>
                <SelectItem value="timeout">Timeout</SelectItem>
                <SelectItem value="dns_error">DNS error</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-2 pt-4">
            <Switch
              checked={starredOnly}
              onCheckedChange={setStarredOnly}
              id="starred-only"
            />
            <Label htmlFor="starred-only" className="text-slate-300">
              Starred only
            </Label>
          </div>
          {selected.size > 0 && (
            <div className="flex flex-wrap items-center gap-2 ml-auto pt-4">
              <span className="text-sm text-slate-400">
                {selected.size} selected
              </span>
              <Select
                value={bulkTargetCollection}
                onValueChange={setBulkTargetCollection}
              >
                <SelectTrigger className="w-40 bg-slate-900 border-slate-800 h-8">
                  <SelectValue placeholder="add to..." />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800">
                  {collections.map((c) => (
                    <SelectItem key={c.id} value={String(c.id)}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Button
                size="sm"
                variant="outline"
                className="border-slate-800 h-8"
                onClick={handleBulkAddToCollection}
                disabled={!bulkTargetCollection}
              >
                Add
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-slate-800 h-8"
                onClick={() => handleBulkStar(1)}
              >
                <Star className="h-3.5 w-3.5 mr-1" /> Star
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-slate-800 h-8"
                onClick={handleBulkRecheck}
                disabled={auditJob?.status === "running"}
              >
                <Link2Off className="h-3.5 w-3.5 mr-1" /> Recheck links
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="border-slate-800 h-8 text-red-400 hover:text-red-300"
                onClick={handleBulkDelete}
              >
                <Trash2 className="h-3.5 w-3.5 mr-1" /> Delete
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Link2Off className="h-5 w-5 text-rose-400" /> Link audit
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {auditJob?.status === "running" ? (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm text-slate-300">
                <span>
                  Checking {auditJob.checked} of {auditJob.total}…
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-slate-800 h-7"
                  onClick={handleCancelAudit}
                >
                  <XCircle className="h-3.5 w-3.5 mr-1" /> Cancel
                </Button>
              </div>
              <Progress
                value={
                  auditJob.total > 0
                    ? (auditJob.checked / auditJob.total) * 100
                    : 0
                }
                className="h-2"
              />
              <div className="flex flex-wrap gap-2 text-xs text-slate-400">
                {Object.entries(auditJob.counts_by_status).map(
                  ([status, count]) => (
                    <span
                      key={status}
                      className={`rounded border px-1.5 py-0.5 ${STATUS_TONE[status] ?? "text-slate-400 border-slate-700"}`}
                    >
                      {status}: {count}
                    </span>
                  ),
                )}
              </div>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                className="border-slate-800"
                onClick={handleCheckPage}
                disabled={rows.length === 0}
              >
                Check this page ({rows.length})
              </Button>
              <Button
                variant="outline"
                className="border-slate-800"
                onClick={handleScanAll}
              >
                Scan entire bookmark set ({total || "?"})
              </Button>
            </div>
          )}
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
                  <th className="pb-2 pr-2 w-8">
                    <Checkbox
                      checked={
                        displayedRows.length > 0 &&
                        displayedRows.every((r) => selected.has(rowKey(r)))
                      }
                      onCheckedChange={(v) => selectAllOnPage(v === true)}
                    />
                  </th>
                  <th className="pb-2 pr-2 w-8" title="Starred" />
                  <th className="pb-2 pr-4">
                    <SortHeader
                      label="Title"
                      sortKey="title"
                      active={sortKey === "title"}
                      dir={sortDir}
                      onSort={handleSort}
                    />
                  </th>
                  <th className="pb-2 pr-4">
                    <SortHeader
                      label="URL"
                      sortKey="url"
                      active={sortKey === "url"}
                      dir={sortDir}
                      onSort={handleSort}
                    />
                  </th>
                  <th className="pb-2 pr-4">
                    <SortHeader
                      label="Folder"
                      sortKey="folder"
                      active={sortKey === "folder"}
                      dir={sortDir}
                      onSort={handleSort}
                    />
                  </th>
                  <th className="pb-2 pr-4">Collections</th>
                  <th className="pb-2 pr-4">
                    <SortHeader
                      label="Status"
                      sortKey="auditStatus"
                      active={sortKey === "auditStatus"}
                      dir={sortDir}
                      onSort={handleSort}
                    />
                  </th>
                  <th className="pb-2 w-28">Actions</th>
                </tr>
              </thead>
              <tbody>
                {displayedRows.map((row) => {
                  const key = rowKey(row);
                  const isEditing = editingKey === key;
                  const starred = (row.starred ?? 0) > 0;
                  return (
                    <tr
                      key={key}
                      className="border-b border-slate-900/80 align-top"
                    >
                      <td className="py-2 pr-2">
                        <Checkbox
                          checked={selected.has(key)}
                          onCheckedChange={() => toggleSelected(key)}
                        />
                      </td>
                      <td className="py-2 pr-2">
                        <button
                          type="button"
                          onClick={() => toggleStar(row)}
                          className="text-slate-500 hover:text-amber-400"
                        >
                          <Star
                            className={`h-4 w-4 ${starred ? "fill-amber-400 text-amber-400" : ""}`}
                          />
                        </button>
                      </td>
                      <td className="py-2 pr-4 text-slate-200 max-w-[200px]">
                        {isEditing ? (
                          <div className="space-y-1">
                            <Input
                              value={editTitle}
                              onChange={(e) => setEditTitle(e.target.value)}
                              className="bg-slate-900 border-slate-800 h-8"
                            />
                            <div className="flex items-start gap-1">
                              <MessageSquare className="h-3.5 w-3.5 text-slate-500 mt-1.5 shrink-0" />
                              <Input
                                value={editComment}
                                onChange={(e) => setEditComment(e.target.value)}
                                placeholder="comment"
                                className="bg-slate-900 border-slate-800 h-8 text-xs"
                              />
                            </div>
                          </div>
                        ) : (
                          <div>
                            <div>{row.title || "(untitled)"}</div>
                            {row.user_comment && (
                              <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                                <MessageSquare className="h-3 w-3" />{" "}
                                {row.user_comment}
                              </div>
                            )}
                          </div>
                        )}
                      </td>
                      <td className="py-2 pr-4 text-slate-400 max-w-[240px] truncate">
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
                      <td className="py-2 pr-4">
                        <div className="flex flex-wrap items-center gap-1">
                          {(row.collections ?? []).map((c) => (
                            <span
                              key={c.id}
                              className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs text-white"
                              style={{ backgroundColor: c.color ?? "#475569" }}
                            >
                              {c.name}
                              <button
                                type="button"
                                onClick={() =>
                                  removeRowFromCollection(row, c.id)
                                }
                                className="hover:opacity-70"
                              >
                                <X className="h-2.5 w-2.5" />
                              </button>
                            </span>
                          ))}
                          {collections.length > 0 && (
                            <select
                              value=""
                              onChange={(e) =>
                                addRowToCollection(row, e.target.value)
                              }
                              className="bg-slate-900 border border-slate-800 rounded text-xs text-slate-400 h-6 px-1"
                            >
                              <option value="">+ add</option>
                              {collections
                                .filter(
                                  (c) =>
                                    !(row.collections ?? []).some(
                                      (rc) => rc.id === c.id,
                                    ),
                                )
                                .map((c) => (
                                  <option key={c.id} value={c.id}>
                                    {c.name}
                                  </option>
                                ))}
                            </select>
                          )}
                        </div>
                      </td>
                      <td className="py-2 pr-4">
                        {row.auditStatus ? (
                          <span
                            className={`rounded border px-1.5 py-0.5 text-xs ${STATUS_TONE[row.auditStatus] ?? "text-slate-400 border-slate-700"}`}
                            title={
                              row.auditCheckedAt
                                ? `checked ${new Date(row.auditCheckedAt).toLocaleString()}`
                                : undefined
                            }
                          >
                            {row.auditStatus}
                          </span>
                        ) : (
                          <span className="text-slate-600 text-xs">
                            unchecked
                          </span>
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
                {!loading && displayedRows.length === 0 && (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-slate-500">
                      {rows.length === 0
                        ? "No bookmarks loaded"
                        : "No bookmarks match the current filter"}
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
              Showing {displayedRows.length} of {rows.length} loaded ({total}{" "}
              total)
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
