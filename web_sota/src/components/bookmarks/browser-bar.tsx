import { useBookmarkSettings } from "@/common/bookmark-settings";
import { BROWSERS } from "@/common/bookmark-types";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";

export function BrowserBar() {
  const {
    browser,
    profileName,
    forceAccess,
    setBrowser,
    setProfileName,
    setForceAccess,
  } = useBookmarkSettings();

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
      <div className="grid gap-2 min-w-[160px]">
        <Label className="text-slate-300">Browser</Label>
        <Select
          value={browser}
          onValueChange={(v: string) => setBrowser(v as typeof browser)}
        >
          <SelectTrigger className="bg-slate-950 border-slate-800 text-slate-100">
            <SelectValue />
          </SelectTrigger>
          <SelectContent className="bg-slate-900 border-slate-800 text-slate-100">
            {BROWSERS.map((b) => (
              <SelectItem key={b.value} value={b.value}>
                {b.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {browser === "firefox" && (
        <>
          <div className="grid gap-2 min-w-[200px] flex-1">
            <Label className="text-slate-300">Firefox profile (optional)</Label>
            <Input
              value={profileName}
              onChange={(e) => setProfileName(e.target.value)}
              placeholder="default"
              className="bg-slate-950 border-slate-800 text-slate-100"
            />
          </div>
          <div className="flex items-center gap-2 pb-1">
            <Switch
              checked={forceAccess}
              onCheckedChange={setForceAccess}
              id="force-access"
            />
            <Label htmlFor="force-access" className="text-slate-300 text-sm">
              Force access (close lock)
            </Label>
          </div>
        </>
      )}
    </div>
  );
}
