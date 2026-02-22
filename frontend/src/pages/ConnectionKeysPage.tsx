import { useEffect, useState } from "react"
import { Plus, KeyRound } from "lucide-react"
import { toast } from "sonner"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { ConnectionKeyCard } from "@/components/connection-keys/ConnectionKeyCard"
import { ConnectionKeyCreateDialog } from "@/components/connection-keys/ConnectionKeyCreateDialog"
import { api } from "@/lib/api"
import { useProfile } from "@/hooks/useProfile"
import type { ConnectionKey } from "@/lib/types"

export function ConnectionKeysPage() {
  const { currentProfile } = useProfile()
  const [keys, setKeys] = useState<ConnectionKey[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        const profileParam = currentProfile ? `?profile_id=${currentProfile.id}` : ""
        const { data } = await api.get(`/connection-keys${profileParam}`)
        setKeys(data.connection_keys ?? data.keys ?? data)
      } catch {
        setKeys([])
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [currentProfile])

  async function handleGenerate(label: string): Promise<string> {
    try {
      const profileId = currentProfile?.id
      const { data } = await api.post("/connection-keys", {
        label,
        ...(profileId ? { profile_id: profileId } : {}),
      })
      setKeys((prev) => [...prev, data])
      toast.success("Connection key generated")
      return data.key_value ?? data.key_prefix ?? ""
    } catch {
      toast.error("Failed to generate key")
      return ""
    }
  }

  async function handleRevoke(key: ConnectionKey) {
    if (!confirm(`Revoke key "${key.label}"? This cannot be undone.`)) return

    try {
      await api.delete(`/connection-keys/${key.id}`)
      setKeys((prev) =>
        prev.map((k) =>
          k.id === key.id ? { ...k, is_active: false } : k
        )
      )
      toast.success("Key revoked")
    } catch {
      toast.error("Failed to revoke key")
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Connection Keys</h1>
          <p className="text-sm text-muted-foreground">
            Manage connection keys for your AI shopping agents
          </p>
        </div>
        <Button
          onClick={() => setDialogOpen(true)}
          className="bg-teal-600 hover:bg-teal-700 text-white gap-1.5"
        >
          <Plus className="h-4 w-4" />
          Generate Key
        </Button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 1 }).map((_, i) => (
            <Skeleton key={i} className="h-20 rounded-lg" />
          ))}
        </div>
      ) : keys.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
            <KeyRound className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium">No connection keys yet</p>
          <p className="text-xs text-muted-foreground mt-1 max-w-xs">
            Generate a connection key to let your AI shopping agent connect to Argus.
          </p>
          <Button
            onClick={() => setDialogOpen(true)}
            className="mt-4 bg-teal-600 hover:bg-teal-700 text-white gap-1.5"
            size="sm"
          >
            <Plus className="h-4 w-4" />
            Generate Key
          </Button>
        </div>
      ) : (
        <div className="space-y-3">
          {keys.map((k) => (
            <ConnectionKeyCard key={k.id} connectionKey={k} onRevoke={handleRevoke} />
          ))}
        </div>
      )}

      <ConnectionKeyCreateDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onGenerate={handleGenerate}
      />
    </div>
  )
}
