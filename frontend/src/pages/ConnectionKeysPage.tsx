import { useEffect, useState } from "react"
import { Plus } from "lucide-react"
import { toast } from "sonner"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { ConnectionKeyCard } from "@/components/connection-keys/ConnectionKeyCard"
import { ConnectionKeyCreateDialog } from "@/components/connection-keys/ConnectionKeyCreateDialog"
import { api } from "@/lib/api"
import { mockConnectionKeys } from "@/lib/mock-data"
import { useProfile } from "@/hooks/useProfile"
import type { ConnectionKey } from "@/lib/types"

const USE_MOCK = !import.meta.env.VITE_API_URL

function generateMockKey(): string {
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789"
  let key = "argus_ck_"
  for (let i = 0; i < 32; i++) {
    key += chars[Math.floor(Math.random() * chars.length)]
  }
  return key
}

export function ConnectionKeysPage() {
  const { currentProfile } = useProfile()
  const [keys, setKeys] = useState<ConnectionKey[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)

  useEffect(() => {
    async function load() {
      try {
        if (USE_MOCK) {
          setKeys(mockConnectionKeys)
        } else {
          const profileParam = currentProfile ? `?profile_id=${currentProfile.id}` : ""
          const { data } = await api.get(`/connection-keys${profileParam}`)
          setKeys(data.connection_keys ?? data)
        }
      } catch {
        setKeys(mockConnectionKeys)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [currentProfile])

  function handleGenerate(label: string): string {
    if (USE_MOCK) {
      const keyValue = generateMockKey()
      const newKey: ConnectionKey = {
        id: `ck-${Date.now()}`,
        key_prefix: keyValue.slice(0, 14),
        key_value: keyValue,
        label,
        is_active: true,
        last_used_at: null,
        created_at: new Date().toISOString(),
      }
      setKeys((prev) => [...prev, newKey])
      toast.success("Connection key generated")
      return keyValue
    }
    // API mode would be async; for now return mock
    const keyValue = generateMockKey()
    api
      .post("/connection-keys", { label })
      .then(({ data }) => {
        setKeys((prev) => [...prev, data])
      })
      .catch(() => {
        toast.error("Failed to generate key")
      })
    return keyValue
  }

  async function handleRevoke(key: ConnectionKey) {
    if (!confirm(`Revoke key "${key.label}"? This cannot be undone.`)) return

    try {
      if (USE_MOCK) {
        setKeys((prev) =>
          prev.map((k) =>
            k.id === key.id ? { ...k, is_active: false } : k
          )
        )
        toast.success("Key revoked")
      } else {
        await api.delete(`/connection-keys/${key.id}`)
        setKeys((prev) =>
          prev.map((k) =>
            k.id === key.id ? { ...k, is_active: false } : k
          )
        )
        toast.success("Key revoked")
      }
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
        <div className="text-center py-12 text-muted-foreground">
          <p className="text-sm">No connection keys yet. Generate one to get started.</p>
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
