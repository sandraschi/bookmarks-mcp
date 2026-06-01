import { callTool, unwrapToolResult } from "@/common/api";
import type { BookmarkListResult, BrowserName } from "@/common/bookmark-types";

export interface BrowserCallOptions {
  browser: BrowserName;
  profileName?: string;
  forceAccess?: boolean;
}

export async function runBrowserBookmarks(
  operation: string,
  options: BrowserCallOptions,
  extra: Record<string, unknown> = {},
): Promise<Record<string, unknown>> {
  const args: Record<string, unknown> = {
    operation,
    browser: options.browser,
    ...extra,
  };
  if (options.browser === "firefox") {
    if (options.profileName) args.profile_name = options.profileName;
    if (options.forceAccess) args.force_access = true;
  }
  const response = await callTool("browser_bookmarks", args);
  return unwrapToolResult(response);
}

export async function listBookmarks(
  options: BrowserCallOptions,
  limit = 100,
  folderId?: number,
  offset = 0,
): Promise<BookmarkListResult> {
  const extra: Record<string, unknown> = { limit, offset };
  if (folderId != null) extra.folder_id = folderId;
  return (await runBrowserBookmarks(
    "list_bookmarks",
    options,
    extra,
  )) as BookmarkListResult;
}

export async function searchBookmarks(
  options: BrowserCallOptions,
  searchQuery: string,
  limit = 100,
  offset = 0,
  extra: Record<string, unknown> = {},
): Promise<BookmarkListResult> {
  return (await runBrowserBookmarks("search_bookmarks", options, {
    search_query: searchQuery,
    limit,
    offset,
    ...extra,
  })) as BookmarkListResult;
}

export async function addBookmark(
  options: BrowserCallOptions,
  title: string,
  url: string,
  folder?: string,
): Promise<Record<string, unknown>> {
  return runBrowserBookmarks("add_bookmark", options, { title, url, folder });
}

export async function editBookmark(
  options: BrowserCallOptions,
  bookmarkId: string,
  newTitle?: string,
  newFolder?: string,
): Promise<Record<string, unknown>> {
  const extra: Record<string, unknown> = { bookmark_id: bookmarkId };
  if (newTitle) extra.new_title = newTitle;
  if (newFolder) extra.new_folder = newFolder;
  return runBrowserBookmarks("edit_bookmark", options, extra);
}

export async function editBookmarkByUrl(
  options: BrowserCallOptions,
  url: string,
  newTitle?: string,
  newFolder?: string,
): Promise<Record<string, unknown>> {
  const extra: Record<string, unknown> = { url };
  if (newTitle) extra.new_title = newTitle;
  if (newFolder) extra.new_folder = newFolder;
  return runBrowserBookmarks("edit_bookmark", options, extra);
}

export async function deleteBookmark(
  options: BrowserCallOptions,
  bookmarkId: string,
  dryRun = false,
): Promise<Record<string, unknown>> {
  return runBrowserBookmarks("delete_bookmark", options, {
    bookmark_id: bookmarkId,
    dry_run: dryRun,
  });
}

export async function deleteBookmarkByUrl(
  options: BrowserCallOptions,
  url: string,
  dryRun = false,
): Promise<Record<string, unknown>> {
  return runBrowserBookmarks("delete_bookmark", options, {
    url,
    dry_run: dryRun,
  });
}

export async function getBookmarkStats(
  options: BrowserCallOptions,
): Promise<Record<string, unknown>> {
  return runBrowserBookmarks("get_bookmark_stats", options);
}

export async function findDuplicates(
  options: BrowserCallOptions,
  similarityThreshold = 0.85,
): Promise<Record<string, unknown>> {
  return runBrowserBookmarks("find_duplicates", options, {
    similarity_threshold: similarityThreshold,
  });
}

export async function exportBookmarks(
  options: BrowserCallOptions,
  exportFormat = "json",
  exportPath?: string,
): Promise<Record<string, unknown>> {
  const extra: Record<string, unknown> = { export_format: exportFormat };
  if (exportPath) extra.export_path = exportPath;
  return runBrowserBookmarks("export_bookmarks", options, extra);
}

export async function syncBrowsers(
  source: BrowserName,
  target: BrowserName,
  dryRun = false,
  limit = 500,
): Promise<Record<string, unknown>> {
  const response = await callTool("browser_bookmarks", {
    operation: "sync_bookmarks",
    browser: source,
    target_browser: target,
    dry_run: dryRun,
    limit,
  });
  return unwrapToolResult(response);
}

export async function findBrokenLinks(
  options: BrowserCallOptions,
  limit = 50,
): Promise<Record<string, unknown>> {
  return runBrowserBookmarks("find_broken_links", options, {
    limit,
    check_links: true,
  });
}

export async function listTags(
  options: BrowserCallOptions,
): Promise<Record<string, unknown>> {
  return runBrowserBookmarks("list_tags", options);
}

export async function cleanUpTags(
  options: BrowserCallOptions,
  dryRun = true,
): Promise<Record<string, unknown>> {
  return runBrowserBookmarks("clean_up_tags", options, { dry_run: dryRun });
}
