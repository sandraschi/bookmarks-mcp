import { useEffect, useState } from "react";
import { type ActivityEntry, getActivity } from "@/common/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function ActivityFeed({ limit = 10 }: { limit?: number }) {
  const [entries, setEntries] = useState<ActivityEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const tick = async () => {
      try {
        const data = await getActivity(limit);
        if (cancelled) return;
        setEntries(data.entries);
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof Error ? err.message : "Failed to load activity",
        );
      }
    };

    void tick();
    const timer = window.setInterval(() => {
      void tick();
    }, 15_000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [limit]);

  return (
    <Card className="border-slate-800 bg-slate-950/50">
      <CardHeader>
        <CardTitle className="text-white">Recent activity</CardTitle>
      </CardHeader>
      <CardContent>
        {error && <p className="text-amber-400 text-sm mb-3">{error}</p>}
        <div className="space-y-2">
          {entries.map((entry) => (
            <div
              key={entry.id}
              className="flex items-start justify-between gap-3 p-2 rounded border border-slate-800 bg-slate-900/40 text-sm"
            >
              <div>
                <p className="text-slate-200">{entry.detail}</p>
                <p className="text-xs text-slate-500">{entry.kind}</p>
              </div>
              <time className="text-xs text-slate-600 shrink-0">
                {new Date(entry.timestamp).toLocaleTimeString()}
              </time>
            </div>
          ))}
          {entries.length === 0 && !error && (
            <p className="text-sm text-slate-500">No activity yet</p>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
