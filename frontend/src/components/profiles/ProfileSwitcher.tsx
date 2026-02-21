import { useState, type ChangeEvent } from "react"
import { Check, ChevronsUpDown, Plus } from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useProfile } from "@/hooks/useProfile"

export function ProfileSwitcher() {
  const { profiles, currentProfile, switchProfile, createProfile } = useProfile()
  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState("")
  const [newDesc, setNewDesc] = useState("")

  function handleCreate() {
    if (!newName.trim()) return
    createProfile(newName.trim(), newDesc.trim() || undefined)
    setNewName("")
    setNewDesc("")
    setCreateOpen(false)
  }

  return (
    <>
      <div className="px-4 py-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex w-full items-center justify-between rounded-md border border-sidebar-border bg-sidebar-accent/50 px-3 py-2 text-sm text-sidebar-foreground hover:bg-sidebar-accent transition-colors">
              <span className="truncate font-medium">
                {currentProfile?.name ?? "Select Profile"}
              </span>
              <ChevronsUpDown className="ml-2 h-3.5 w-3.5 shrink-0 opacity-60" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            {profiles.map((profile) => (
              <DropdownMenuItem
                key={profile.id}
                onClick={() => switchProfile(profile.id)}
                className="gap-2"
              >
                {profile.id === currentProfile?.id ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <span className="w-3.5" />
                )}
                <span className="truncate">{profile.name}</span>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setCreateOpen(true)} className="gap-2">
              <Plus className="h-3.5 w-3.5" />
              Create Profile
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create Profile</DialogTitle>
            <DialogDescription>
              Add a new profile with its own spending categories and rules.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-1">
            <div className="space-y-2">
              <Label htmlFor="profile-name">Name</Label>
              <Input
                id="profile-name"
                placeholder="e.g., Office Supplies"
                value={newName}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setNewName(e.target.value)
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="profile-desc">Description (optional)</Label>
              <Input
                id="profile-desc"
                placeholder="What this profile is used for"
                value={newDesc}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setNewDesc(e.target.value)
                }
              />
            </div>
          </div>
          <DialogFooter className="pt-2">
            <Button variant="outline" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={!newName.trim()}
              className="bg-teal-600 hover:bg-teal-700 text-white"
            >
              Create
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
