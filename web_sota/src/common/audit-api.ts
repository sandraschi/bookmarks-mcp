import { callTool, unwrapToolResult } from "@/common/api";
import {
  type BrowserCallOptions,
  resolveProfileName,
} from "@/common/bookmark-ops";

export type AuditStatus =
  | "ok"
  | "redirected"
  | "dead"
  | "blocked"
  | "timeout"
  | "dns_error";

export interface AuditResult {
  url: string;
  status: AuditStatus;
  http_status: number | null;
  final_url: string | null;
  checked_via: string;
  error_detail: string | null;
  job_id: string;
  checked_at: string;
}

export interface AuditJob {
  job_id: string;
  browser: string;
  profile_name: string | null;
  status: "running" | "done" | "cancelled" | "error";
  total: number;
  checked: number;
  counts_by_status: Record<string, number>;
  error: string | null;
  started_at: string;
  finished_at: string | null;
}

async function callAudit(
  args: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const response = await callTool("bookmark_audit", args);
  return unwrapToolResult(response);
}

export async function runAudit(
  options: BrowserCallOptions,
  scope: { urls?: string[]; folderPath?: string; limit?: number } = {},
): Promise<{
  success: boolean;
  job_id?: string;
  total?: number;
  error?: string;
}> {
  const data = await callAudit({
    operation: "run_audit",
    browser: options.browser,
    profile_name: resolveProfileName(options),
    urls: scope.urls,
    folder_path: scope.folderPath,
    limit: scope.limit,
  });
  return data as {
    success: boolean;
    job_id?: string;
    total?: number;
    error?: string;
  };
}

export async function getAuditStatus(jobId: string): Promise<AuditJob | null> {
  const data = await callAudit({
    operation: "get_audit_status",
    job_id: jobId,
  });
  if (data.success === false) return null;
  return data.job as AuditJob;
}

export async function cancelAudit(jobId: string): Promise<boolean> {
  const data = await callAudit({ operation: "cancel_audit", job_id: jobId });
  return data.cancelled === true;
}

export async function getResultsForUrls(
  urls: string[],
  options: BrowserCallOptions,
): Promise<Record<string, AuditResult>> {
  if (urls.length === 0) return {};
  const data = await callAudit({
    operation: "get_results_for_urls",
    urls,
    browser: options.browser,
    profile_name: resolveProfileName(options),
  });
  return (data.results_by_url as Record<string, AuditResult> | undefined) ?? {};
}
