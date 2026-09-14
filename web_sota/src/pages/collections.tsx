import { FolderPlus, Loader2, Pencil, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import {
  type Collection,
  createCollection,
  deleteCollection,
  listCollections,
  updateCollection,
} from "@/common/collections-api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/toast";

const SWATCHES = [
  "#3b82f6",
  "#22c55e",
  "#f59e0b",
  "#ef4444",
  "#a855f7",
  "#06b6d4",
];

export function CollectionsPage() {
  const { toast } = useToast();
  const [items, setItems] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);

  const [newName, setNewName] = useState("");
  const [newDescription, setNewDescription] = useState("");
  const [newColor, setNewColor] = useState(SWATCHES[0]);

  const [editingId, setEditingId] = useState<number | null>(null);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setItems(await listCollections());
    } catch (err) {
      toast({
        title: "Load failed",
        description: err instanceof Error ? err.message : "Load failed",
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!newName.trim()) {
      toast({
        title: "Name required",
        description: "Collections need a name",
        variant: "error",
      });
      return;
    }
    setLoading(true);
    try {
      const result = await createCollection(
        newName.trim(),
        newDescription.trim() || undefined,
        newColor,
      );
      if (result.success === false) {
        toast({
          title: "Create failed",
          description: String(result.error ?? "Create failed"),
          variant: "error",
        });
        return;
      }
      toast({
        title: `Collection "${newName.trim()}" created`,
        variant: "success",
      });
      setNewName("");
      setNewDescription("");
      await load();
    } finally {
      setLoading(false);
    }
  };

  const startEdit = (c: Collection) => {
    setEditingId(c.id);
    setEditName(c.name);
    setEditDescription(c.description ?? "");
  };

  const handleSaveEdit = async () => {
    if (editingId == null) return;
    setLoading(true);
    try {
      const result = await updateCollection(editingId, {
        name: editName.trim(),
        description: editDescription.trim(),
      });
      if (result.success === false) {
        toast({
          title: "Update failed",
          description: String(result.error ?? "Update failed"),
          variant: "error",
        });
        return;
      }
      setEditingId(null);
      await load();
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (c: Collection) => {
    const memberNote =
      c.member_count > 0
        ? ` It has ${c.member_count} bookmark(s) - they will not be deleted, only removed from this collection.`
        : "";
    if (!window.confirm(`Delete collection "${c.name}"?${memberNote}`)) return;
    setLoading(true);
    try {
      await deleteCollection(c.id);
      toast({ title: `Collection "${c.name}" deleted`, variant: "success" });
      await load();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold tracking-tight text-white">
          Collections
        </h2>
        <p className="text-slate-400">
          Named groups for curating bookmarks - your "ai", "music", "politics"
          faves, independent of any browser's folders
        </p>
      </div>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <FolderPlus className="h-5 w-5 text-blue-400" /> New collection
          </CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-4">
          <div className="grid gap-2">
            <Label className="text-slate-300">Name</Label>
            <Input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="bg-slate-900 border-slate-800"
            />
          </div>
          <div className="grid gap-2 md:col-span-2">
            <Label className="text-slate-300">Description (optional)</Label>
            <Input
              value={newDescription}
              onChange={(e) => setNewDescription(e.target.value)}
              className="bg-slate-900 border-slate-800"
            />
          </div>
          <div className="grid gap-2">
            <Label className="text-slate-300">Color</Label>
            <div className="flex gap-1.5 items-center h-9">
              {SWATCHES.map((swatch) => (
                <button
                  key={swatch}
                  type="button"
                  aria-label={`color ${swatch}`}
                  onClick={() => setNewColor(swatch)}
                  className={`h-5 w-5 rounded-full border-2 ${
                    newColor === swatch ? "border-white" : "border-transparent"
                  }`}
                  style={{ backgroundColor: swatch }}
                />
              ))}
            </div>
          </div>
          <div className="md:col-span-4">
            <Button
              onClick={handleCreate}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <Plus className="mr-2 h-4 w-4" /> Create collection
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card className="border-slate-800 bg-slate-950/50">
        <CardHeader>
          <CardTitle className="text-white">
            All collections ({items.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {items.map((c) => (
              <div
                key={c.id}
                className="flex items-center gap-3 rounded border border-slate-800 bg-slate-900/50 px-3 py-2"
              >
                <span
                  className="h-3 w-3 shrink-0 rounded-full"
                  style={{ backgroundColor: c.color ?? "#64748b" }}
                />
                {editingId === c.id ? (
                  <div className="flex flex-1 gap-2">
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      className="h-8 bg-slate-900 border-slate-800"
                    />
                    <Input
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      placeholder="description"
                      className="h-8 bg-slate-900 border-slate-800"
                    />
                  </div>
                ) : (
                  <div className="flex-1 min-w-0">
                    <span className="text-slate-200 font-medium">{c.name}</span>
                    {c.description && (
                      <span className="text-slate-500 text-sm ml-2">
                        {c.description}
                      </span>
                    )}
                  </div>
                )}
                <span className="text-slate-500 text-xs shrink-0">
                  {c.member_count} bookmark{c.member_count === 1 ? "" : "s"}
                </span>
                <div className="flex gap-1 shrink-0">
                  {editingId === c.id ? (
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
                      onClick={() => startEdit(c)}
                      className="h-8"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDelete(c)}
                    className="h-8 text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))}
            {!loading && items.length === 0 && (
              <p className="text-center text-slate-500 py-8 text-sm">
                No collections yet - create one above.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
