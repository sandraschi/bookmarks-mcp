import { callTool, unwrapToolResult } from "@/common/api";
import {
  type BrowserCallOptions,
  resolveProfileName,
} from "@/common/bookmark-ops";
import type { CollectionRef } from "@/common/bookmark-types";

export interface Collection extends CollectionRef {
  description?: string | null;
  member_count: number;
  created_at: string;
  updated_at: string;
}

async function callCollections(
  args: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const response = await callTool("collections", args);
  return unwrapToolResult(response);
}

export async function listCollections(): Promise<Collection[]> {
  const data = await callCollections({ operation: "list_collections" });
  return (data.collections as Collection[] | undefined) ?? [];
}

export async function createCollection(
  name: string,
  description?: string,
  color?: string,
): Promise<Record<string, unknown>> {
  return callCollections({
    operation: "create_collection",
    name,
    description,
    color,
  });
}

export async function updateCollection(
  collectionId: number,
  fields: { name?: string; description?: string; color?: string },
): Promise<Record<string, unknown>> {
  return callCollections({
    operation: "update_collection",
    collection_id: collectionId,
    ...fields,
  });
}

export async function deleteCollection(
  collectionId: number,
): Promise<Record<string, unknown>> {
  return callCollections({
    operation: "delete_collection",
    collection_id: collectionId,
  });
}

export async function addToCollection(
  url: string,
  collectionId: number,
  options: BrowserCallOptions,
): Promise<Record<string, unknown>> {
  return callCollections({
    operation: "add_to_collection",
    url,
    collection_id: collectionId,
    browser: options.browser,
    profile_name: resolveProfileName(options),
  });
}

export async function removeFromCollection(
  url: string,
  collectionId: number,
  options: BrowserCallOptions,
): Promise<Record<string, unknown>> {
  return callCollections({
    operation: "remove_from_collection",
    url,
    collection_id: collectionId,
    browser: options.browser,
    profile_name: resolveProfileName(options),
  });
}

export async function bulkAddToCollection(
  urls: string[],
  collectionId: number,
  options: BrowserCallOptions,
): Promise<Record<string, unknown>> {
  return callCollections({
    operation: "bulk_add_to_collection",
    urls,
    collection_id: collectionId,
    browser: options.browser,
    profile_name: resolveProfileName(options),
  });
}

export async function getCollectionsForUrls(
  urls: string[],
  options: BrowserCallOptions,
): Promise<Record<string, CollectionRef[]>> {
  const data = await callCollections({
    operation: "get_collections_for_urls",
    urls,
    browser: options.browser,
    profile_name: resolveProfileName(options),
  });
  return (
    (data.collections_by_url as Record<string, CollectionRef[]> | undefined) ??
    {}
  );
}
