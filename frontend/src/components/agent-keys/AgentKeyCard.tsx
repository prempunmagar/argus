import { KeyRound } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { formatRelativeTime } from "@/lib/utils"
import type { AgentKey } from "@/lib/types"

export function AgentKeyCard({
  agentKey,
  onRevoke,
}: {
  agentKey: AgentKey
  onRevoke?: (key: AgentKey) => void
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 py-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
          <KeyRound className="h-5 w-5 text-muted-foreground" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">{agentKey.label}</p>
            <Badge
              variant="outline"
              className={
                agentKey.is_active
                  ? "text-[10px] text-green-600 border-green-200 bg-green-50"
                  : "text-[10px] text-red-600 border-red-200 bg-red-50"
              }
            >
              {agentKey.is_active ? "Active" : "Revoked"}
            </Badge>
          </div>
          <div className="flex items-center gap-3 mt-0.5">
            <code className="text-xs text-muted-foreground font-mono">
              {agentKey.key_prefix}...
            </code>
            {agentKey.last_used_at && (
              <span className="text-xs text-muted-foreground">
                Last used {formatRelativeTime(agentKey.last_used_at)}
              </span>
            )}
          </div>
        </div>

        {onRevoke && agentKey.is_active && (
          <Button
            variant="ghost"
            size="sm"
            className="shrink-0 text-red-600 hover:text-red-700 hover:bg-red-50"
            onClick={() => onRevoke(agentKey)}
          >
            Revoke
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
