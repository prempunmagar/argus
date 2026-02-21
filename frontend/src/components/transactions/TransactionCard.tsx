import { useNavigate } from "react-router-dom"
import { CreditCard, Clock, Store } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "./StatusBadge"
import { formatCurrency, formatRelativeTime } from "@/lib/utils"
import type { TransactionListItem } from "@/lib/types"
import { api } from "@/lib/api"

interface Props {
  transaction: TransactionListItem
  onUpdate?: () => void
}

export function TransactionCard({ transaction: t, onUpdate }: Props) {
  const navigate = useNavigate()

  const handleApprove = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.post(`/transactions/${t.id}/approve`)
      onUpdate?.()
    } catch {
      // silently fail for mock mode
    }
  }

  const handleDeny = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.post(`/transactions/${t.id}/deny`)
      onUpdate?.()
    } catch {
      // silently fail for mock mode
    }
  }

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={() => navigate(`/transactions/${t.id}`)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium text-sm truncate">{t.product_name}</h3>
              <StatusBadge status={t.status} />
            </div>

            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Store className="h-3 w-3" />
                {t.merchant_name}
              </span>
              {t.detected_category_name && (
                <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium">
                  {t.detected_category_name}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatRelativeTime(t.created_at)}
              </span>
              {t.virtual_card_last_four && (
                <span className="flex items-center gap-1">
                  <CreditCard className="h-3 w-3" />
                  ••{t.virtual_card_last_four}
                </span>
              )}
            </div>

            {t.decision_reason && t.status === "DENIED" && (
              <p className="mt-2 text-xs text-red-600 line-clamp-2">
                {t.decision_reason}
              </p>
            )}
          </div>

          <div className="text-right shrink-0">
            <p className="font-semibold text-sm">
              {formatCurrency(t.price, t.currency)}
            </p>
          </div>
        </div>

        {t.status === "PENDING_APPROVAL" && (
          <div className="mt-3 flex gap-2 justify-end">
            <Button
              size="sm"
              variant="outline"
              className="text-red-600 border-red-200 hover:bg-red-50"
              onClick={handleDeny}
            >
              Deny
            </Button>
            <Button
              size="sm"
              className="bg-green-600 hover:bg-green-700 text-white"
              onClick={handleApprove}
            >
              Approve
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
