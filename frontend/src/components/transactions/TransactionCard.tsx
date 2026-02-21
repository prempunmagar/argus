import { useNavigate } from "react-router-dom"
import { CreditCard, Clock, Store } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusBadge } from "./StatusBadge"
import { formatCurrency, formatRelativeTime } from "@/lib/utils"
import { useTransactions } from "@/hooks/useTransactions"
import type { Transaction } from "@/lib/types"
import { api } from "@/lib/api"

const USE_MOCK = !import.meta.env.VITE_API_URL

interface Props {
  transaction: Transaction
}

export function TransactionCard({ transaction: t }: Props) {
  const navigate = useNavigate()
  const { updateTransaction } = useTransactions()

  const handleApprove = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.post(`/transactions/${t.id}/approve`)
    } catch {
      // mock mode
    }
    if (USE_MOCK) {
      updateTransaction(t.id, { status: "HUMAN_APPROVED" })
    }
  }

  const handleDeny = async (e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await api.post(`/transactions/${t.id}/deny`)
    } catch {
      // mock mode
    }
    if (USE_MOCK) {
      updateTransaction(t.id, { status: "HUMAN_DENIED" })
    }
  }

  const showReasoning =
    t.evaluation?.decision_reasoning &&
    (t.status === "AI_DENIED" || t.status === "HUMAN_DENIED" || t.status === "HUMAN_NEEDED")

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={() => navigate(`/transactions/${t.id}`)}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h3 className="font-medium text-sm truncate">{t.request_data.product_name}</h3>
              <StatusBadge status={t.status} />
            </div>

            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Store className="h-3 w-3" />
                {t.request_data.merchant_name}
              </span>
              {t.evaluation?.category_name && (
                <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium">
                  {t.evaluation.category_name}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatRelativeTime(t.created_at)}
              </span>
              {t.virtual_card_last_four && (
                <span className="flex items-center gap-1">
                  <CreditCard className="h-3 w-3" />
                  Card ••{t.virtual_card_last_four}
                </span>
              )}
            </div>

            {showReasoning && (
              <p
                className={`mt-2 text-xs line-clamp-2 ${
                  t.status === "HUMAN_NEEDED"
                    ? "text-amber-700"
                    : "text-red-600"
                }`}
              >
                {t.evaluation!.decision_reasoning}
              </p>
            )}
          </div>

          <div className="text-right shrink-0">
            <p className="font-semibold text-sm">
              {formatCurrency(t.request_data.price, t.request_data.currency)}
            </p>
          </div>
        </div>

        {t.status === "HUMAN_NEEDED" && (
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
