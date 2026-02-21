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
import { useAgent } from "@/hooks/useAgent"

export function AgentSwitcher() {
  const { agents, currentAgent, switchAgent, createAgent } = useAgent()
  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState("")
  const [newDesc, setNewDesc] = useState("")

  function handleCreate() {
    if (!newName.trim()) return
    createAgent(newName.trim(), newDesc.trim() || undefined)
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
                {currentAgent?.name ?? "Select Agent"}
              </span>
              <ChevronsUpDown className="ml-2 h-3.5 w-3.5 shrink-0 opacity-60" />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-56">
            {agents.map((agent) => (
              <DropdownMenuItem
                key={agent.id}
                onClick={() => switchAgent(agent.id)}
                className="gap-2"
              >
                {agent.id === currentAgent?.id ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <span className="w-3.5" />
                )}
                <span className="truncate">{agent.name}</span>
              </DropdownMenuItem>
            ))}
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => setCreateOpen(true)} className="gap-2">
              <Plus className="h-3.5 w-3.5" />
              Create Agent
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create Agent</DialogTitle>
            <DialogDescription>
              Add a new AI shopping agent with its own categories and rules.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-1">
            <div className="space-y-2">
              <Label htmlFor="agent-name">Name</Label>
              <Input
                id="agent-name"
                placeholder="e.g., Office Supplies"
                value={newName}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setNewName(e.target.value)
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="agent-desc">Description (optional)</Label>
              <Input
                id="agent-desc"
                placeholder="What this agent is used for"
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
