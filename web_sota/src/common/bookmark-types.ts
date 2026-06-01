export type BrowserName = "firefox" | "chrome" | "edge" | "brave";

export interface BookmarkRow {
  id?: string | number;
  title?: string;
  url?: string;
  folder?: string;
  parent?: string | number;
  dateAdded?: number;
  lastModified?: number;
  tags?: string[];
}

export interface BookmarkListResult {
  success?: boolean;
  status?: string;
  bookmarks?: BookmarkRow[];
  total_count?: number;
  total?: number;
  count?: number;
  returned_count?: number;
  error?: string;
  message?: string;
  pagination?: {
    limit: number;
    offset: number;
    has_more: boolean;
    total_count?: number;
  };
}

export const BROWSERS: { value: BrowserName; label: string }[] = [
  { value: "firefox", label: "Firefox" },
  { value: "chrome", label: "Chrome" },
  { value: "edge", label: "Edge" },
  { value: "brave", label: "Brave" },
];

export function normalizeBookmarks(data: BookmarkListResult): BookmarkRow[] {
  const withResults = data as BookmarkListResult & { results?: BookmarkRow[] };
  return data.bookmarks ?? withResults.results ?? [];
}

export function hasMorePages(data: BookmarkListResult): boolean {
  return data.pagination?.has_more ?? false;
}

export function totalBookmarkCount(data: BookmarkListResult): number {
  return (
    data.total_count ??
    data.total ??
    data.count ??
    data.returned_count ??
    normalizeBookmarks(data).length
  );
}

export function isSuccess(
  data: Record<string, unknown> | BookmarkListResult,
): boolean {
  if ("success" in data && data.success === false) return false;
  if ("status" in data && data.status === "error") return false;
  return true;
}
