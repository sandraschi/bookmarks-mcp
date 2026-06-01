import {
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Folder,
  Link2,
} from "lucide-react";
import { useState } from "react";
import type { BookmarkTreeNode } from "@/common/api";
import { cn } from "@/common/utils";

interface TreeNodeProps {
  node: BookmarkTreeNode;
  depth?: number;
}

export function TreeNode({ node, depth = 0 }: TreeNodeProps) {
  const [open, setOpen] = useState(depth < 2);
  const isFolder = node.type === "folder";

  if (!isFolder) {
    return (
      <div
        className="flex items-center gap-2 py-1.5 text-sm text-slate-300 hover:bg-slate-900/60 rounded px-2"
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        <Link2 className="h-3.5 w-3.5 shrink-0 text-blue-400" />
        <span className="truncate flex-1">{node.title || "(untitled)"}</span>
        {node.url && (
          <a
            href={node.url}
            target="_blank"
            rel="noreferrer"
            className="text-slate-500 hover:text-blue-400 shrink-0"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
        )}
      </div>
    );
  }

  const children = node.children ?? [];
  const bookmarkCount = children.filter((c) => c.type === "bookmark").length;
  const folderCount = children.filter((c) => c.type === "folder").length;

  return (
    <div>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={cn(
          "flex w-full items-center gap-2 py-1.5 text-sm text-slate-200 hover:bg-slate-900/60 rounded px-2 text-left",
        )}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-slate-500" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-slate-500" />
        )}
        <Folder className="h-4 w-4 shrink-0 text-amber-400" />
        <span className="font-medium truncate">
          {node.name || node.path || "Folder"}
        </span>
        <span className="text-xs text-slate-500 ml-auto shrink-0">
          {folderCount > 0 && `${folderCount} folders`}
          {folderCount > 0 && bookmarkCount > 0 && " · "}
          {bookmarkCount > 0 && `${bookmarkCount} links`}
        </span>
      </button>
      {open &&
        children.map((child, idx) => (
          <TreeNode
            key={`${child.type}-${child.id ?? child.url ?? idx}`}
            node={child}
            depth={depth + 1}
          />
        ))}
    </div>
  );
}
