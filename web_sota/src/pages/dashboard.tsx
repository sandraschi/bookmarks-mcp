import { Activity, Bookmark, Globe, Loader2, Zap } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHealth, getTools } from "@/common/api";
import { getBookmarkStats, listBookmarks } from "@/common/bookmark-ops";
import { useBookmarkSettings } from "@/common/bookmark-settings";
import {
  BROWSERS,
  isSuccess,
  normalizeBookmarks,
  totalBookmarkCount,
} from "@/common/bookmark-types";
import { ActivityFeed } from "@/components/bookmarks/activity-feed";
import { BrowserBar } from "@/components/bookmarks/browser-bar";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Dashboard() {
  const { callOptions, browser } = useBookmarkSettings();
  const [healthy, setHealthy] = useState(false);
  const [toolCount, setToolCount] = useState(0);
  const [bookmarkTotal, setBookmarkTotal] = useState<number | null>(null);
  const [recent, setRecent] = useState<{ title?: string; url?: string }[]>([]);
  const [browserTotals, setBrowserTotals] = useState<
    Record<string, number | null>
  >({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        await getHealth();
        if (cancelled) return;
        setHealthy(true);
        const tools = await getTools();
        if (cancelled) return;
        setToolCount(tools.tools.length);

        const list = await listBookmarks(callOptions, 5);
        if (!cancelled && isSuccess(list)) {
          setBookmarkTotal(totalBookmarkCount(list));
          setRecent(normalizeBookmarks(list).slice(0, 5));
        } else if (browser === "firefox") {
          const stats = await getBookmarkStats(callOptions);
          if (!cancelled && isSuccess(stats)) {
            const total = Number(stats.total_bookmarks ?? stats.total ?? 0);
            if (total > 0) setBookmarkTotal(total);
          }
        }

        const totals: Record<string, number | null> = {};
        await Promise.all(
          BROWSERS.map(async (b) => {
            try {
              const data = await listBookmarks(
                {
                  browser: b.value,
                  profileName: callOptions.profileName,
                  forceAccess: callOptions.forceAccess,
                },
                1,
                undefined,
                0,
              );
              totals[b.value] = isSuccess(data)
                ? totalBookmarkCount(data)
                : null;
            } catch {
              totals[b.value] = null;
            }
          }),
        );
        if (!cancelled) setBrowserTotals(totals);
      } catch (err) {
        if (!cancelled) {
          setHealthy(false);
          setError(err instanceof Error ? err.message : "Backend unreachable");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [callOptions, browser]);

  const stats = [
    {
      label: "Total Bookmarks",
      value:
        bookmarkTotal != null
          ? bookmarkTotal.toLocaleString()
          : loading
            ? "…"
            : "—",
      change: `Active browser: ${browser}`,
      icon: Bookmark,
      color: "text-blue-500",
    },
    {
      label: "API Status",
      value: healthy ? "Online" : "Offline",
      change: healthy ? "Backend connected" : "Start backend on 10803",
      icon: Activity,
      color: healthy ? "text-green-500" : "text-red-500",
    },
    {
      label: "MCP Tools",
      value: String(toolCount || "—"),
      change: "Portmanteau surface",
      icon: Globe,
      color: "text-purple-500",
    },
    {
      label: "Quick links",
      value: "4 pages",
      change: "CRUD · Search · Tree · Bulk",
      icon: Zap,
      color: "text-yellow-500",
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-white">
            Bookmark Master
          </h2>
          <p className="text-slate-400">Browser knowledge base management</p>
        </div>
        {loading && <Loader2 className="h-5 w-5 animate-spin text-slate-500" />}
      </div>

      <BrowserBar />

      {error && (
        <p className="text-amber-400 text-sm">
          {error} — run{" "}
          <code className="text-slate-300">web_sota/start.ps1</code> or check
          Settings for API auth.
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label} className="border-slate-800 bg-slate-950/50">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-slate-200">
                {stat.label}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{stat.value}</div>
              <p className="text-xs text-slate-400">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="border-slate-800 bg-slate-950/50">
          <CardHeader>
            <CardTitle className="text-white">Recent bookmarks</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recent.map((item, i) => (
                <div
                  key={item.url ?? i}
                  className="flex items-center gap-3 p-3 rounded-lg bg-slate-900/40 border border-slate-800"
                >
                  <Bookmark className="h-4 w-4 text-blue-500 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-slate-200 truncate">
                      {item.title || "(untitled)"}
                    </p>
                    <p className="text-xs text-slate-500 truncate">
                      {item.url}
                    </p>
                  </div>
                </div>
              ))}
              {!loading && recent.length === 0 && (
                <p className="text-sm text-slate-500">
                  No bookmarks loaded yet
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <ActivityFeed limit={8} />
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">All browsers</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {BROWSERS.map((b) => (
            <div
              key={b.value}
              className="p-3 rounded-lg border border-slate-800 bg-slate-900/40"
            >
              <p className="text-sm text-slate-300">{b.label}</p>
              <p className="text-xl font-semibold text-white">
                {browserTotals[b.value] != null
                  ? browserTotals[b.value]?.toLocaleString()
                  : loading
                    ? "…"
                    : "—"}
              </p>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">Workspace</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2">
          <Button
            asChild
            variant="outline"
            className="border-slate-800 justify-start"
          >
            <Link to="/bookmarks">Manage bookmarks (CRUD)</Link>
          </Button>
          <Button
            asChild
            variant="outline"
            className="border-slate-800 justify-start"
          >
            <Link to="/search">Search bookmarks</Link>
          </Button>
          <Button
            asChild
            variant="outline"
            className="border-slate-800 justify-start"
          >
            <Link to="/tree">Browse folder tree</Link>
          </Button>
          <Button
            asChild
            variant="outline"
            className="border-slate-800 justify-start"
          >
            <Link to="/bulk">Bulk operations & sync</Link>
          </Button>
          <Button
            asChild
            variant="outline"
            className="border-slate-800 justify-start"
          >
            <Link to="/tags">Tag manager</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
