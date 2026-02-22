import { useState, type ChangeEvent } from "react"
import { useNavigate } from "react-router-dom"
import { ShieldCheck, Store, ExternalLink } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { useTransactions } from "@/hooks/useTransactions"
import { formatCurrency } from "@/lib/utils"
import { api } from "@/lib/api"

const USE_MOCK = !import.meta.env.VITE_API_URL

export function ApprovalsPage() {
  const navigate = useNavigate()
  const { transactions, loading, updateTransaction } = useTransactions()
  const [notes, setNotes] = useState<Record<string, string>>({})

  const pending = transactions.filter((t) => t.status === "HUMAN_NEEDED")

  async function handleApprove(id: string) {
    try {
      await api.post(`/transactions/${id}/approve`, {
        note: notes[id] || undefined,
      })
    } catch {
      // mock mode
    }
    if (USE_MOCK) {
      updateTransaction(id, { status: "HUMAN_APPROVED" })
    }
  }

  async function handleDeny(id: string) {
    try {
      await api.post(`/transactions/${id}/deny`, {
        note: notes[id] || undefined,
      })
    } catch {
      // mock mode
    }
    if (USE_MOCK) {
      updateTransaction(id, { status: "HUMAN_DENIED" })
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold flex items-center gap-2">
          Pending Approvals
          {!loading && pending.length > 0 && (
            <span className="text-sm font-normal text-muted-foreground">
              ({pending.length})
            </span>
          )}
        </h1>
        <p className="text-sm text-muted-foreground">
          Review and approve or deny purchases that require your authorization
        </p>
      </div>

      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-40 rounded-lg" />
          ))}
        </div>
      ) : pending.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
            <ShieldCheck className="h-6 w-6 text-green-500" />
          </div>
          <p className="text-sm font-medium">All clear</p>
          <p className="text-xs text-muted-foreground mt-1">
            No pending approvals right now.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {pending.map((t) => (
            <Card key={t.id}>
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium">{t.request_data.product_name}</h3>
                      <button
                        type="button"
                        onClick={() => navigate(`/transactions/${t.id}`)}
                        className="text-teal-600 hover:text-teal-700"
                        title="View details"
                      >
                        <ExternalLink className="h-3.5 w-3.5" />
                      </button>
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground mt-1">
                      <span className="flex items-center gap-1">
                        <Store className="h-3.5 w-3.5" />
                        {t.request_data.merchant_name}
                      </span>
                      {t.evaluation?.category_name && (
                        <span className="rounded-full bg-secondary px-2 py-0.5 text-xs font-medium">
                          {t.evaluation.category_name}
                        </span>
                      )}
                    </div>
                    {t.evaluation?.decision_reasoning && (
                      <p className="mt-2 text-sm text-amber-700">
                        {t.evaluation.decision_reasoning}
                      </p>
                    )}
                  </div>
                  <p className="text-lg font-semibold shrink-0">
                    {formatCurrency(t.request_data.price, t.request_data.currency)}
                  </p>
                </div>

                <div className="mt-4 flex items-center gap-3">
                  <Input
                    placeholder="Add a note (optional)"
                    className="text-sm"
                    value={notes[t.id] ?? ""}
                    onChange={(e: ChangeEvent<HTMLInputElement>) =>
                      setNotes((prev) => ({ ...prev, [t.id]: e.target.value }))
                    }
                  />
                  <Button
                    variant="outline"
                    className="text-red-600 border-red-200 hover:bg-red-50 shrink-0"
                    onClick={() => handleDeny(t.id)}
                  >
                    Deny
                  </Button>
                  <Button
                    className="bg-green-600 hover:bg-green-700 text-white shrink-0"
                    onClick={() => handleApprove(t.id)}
                  >
                    Approve
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
