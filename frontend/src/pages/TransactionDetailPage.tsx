import { useEffect, useState } from "react"
import { useParams, useNavigate } from "react-router-dom"
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  CreditCard,
  Brain,
  ListChecks,
  ExternalLink,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { StatusBadge } from "@/components/transactions/StatusBadge"
import { formatCurrency } from "@/lib/utils"
import { api } from "@/lib/api"
import { mockTransactionDetail } from "@/lib/mock-data"
import type { TransactionDetail } from "@/lib/types"

const USE_MOCK = !import.meta.env.VITE_API_URL

export function TransactionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [txn, setTxn] = useState<TransactionDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        if (USE_MOCK) {
          setTxn({ ...mockTransactionDetail, id: id! })
        } else {
          const { data } = await api.get(`/transactions/${id}`)
          setTxn(data)
        }
      } catch {
        setTxn({ ...mockTransactionDetail, id: id! })
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  if (loading) {
    return (
      <div className="p-6 max-w-3xl mx-auto space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-48 w-full rounded-lg" />
        <Skeleton className="h-64 w-full rounded-lg" />
      </div>
    )
  }

  if (!txn) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <p className="text-muted-foreground">Transaction not found.</p>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-5">
      <Button
        variant="ghost"
        size="sm"
        className="gap-1.5 -ml-2"
        onClick={() => navigate(-1)}
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </Button>

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">{txn.product_name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <StatusBadge status={txn.status} />
            <span className="text-sm text-muted-foreground">
              {txn.merchant_name}
            </span>
            {txn.product_url && (
              <a
                href={txn.product_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-teal-600 hover:underline"
                onClick={(e) => e.stopPropagation()}
              >
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            )}
          </div>
        </div>
        <p className="text-2xl font-bold">
          {formatCurrency(txn.price, txn.currency)}
        </p>
      </div>

      {txn.decision_reason && (
        <Card>
          <CardContent className="p-4 text-sm">
            <p
              className={
                txn.decision === "DENY" ? "text-red-600" : "text-foreground"
              }
            >
              {txn.decision_reason}
            </p>
          </CardContent>
        </Card>
      )}

      {/* AI Evaluation */}
      {txn.ai_evaluation && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Brain className="h-4 w-4 text-teal-600" />
              AI Evaluation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs text-muted-foreground">Category</p>
                <p className="font-medium">{txn.ai_evaluation.category_name}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Confidence</p>
                <p className="font-medium">
                  {(txn.ai_evaluation.category_confidence * 100).toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Intent Match</p>
                <p className="font-medium">
                  {(txn.ai_evaluation.intent_match * 100).toFixed(0)}%
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Risk Flags</p>
                <p className="font-medium">
                  {txn.ai_evaluation.risk_flags.length === 0
                    ? "None"
                    : txn.ai_evaluation.risk_flags.join(", ")}
                </p>
              </div>
            </div>
            <Separator />
            <div>
              <p className="text-xs text-muted-foreground mb-1">
                Intent Summary
              </p>
              <p>{txn.ai_evaluation.intent_summary}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground mb-1">Reasoning</p>
              <p>{txn.ai_evaluation.reasoning}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Rules Evaluation */}
      {txn.rules_checked && txn.rules_checked.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <ListChecks className="h-4 w-4 text-teal-600" />
              Rules Evaluation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {txn.rules_checked.map((r, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between text-sm py-1.5"
                >
                  <div className="flex items-center gap-2">
                    {r.passed ? (
                      <CheckCircle2 className="h-4 w-4 text-green-600 shrink-0" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500 shrink-0" />
                    )}
                    <span className="font-medium">
                      {r.rule_type.replace(/_/g, " ")}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground max-w-[50%] text-right">
                    {r.detail}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Virtual Card */}
      {txn.virtual_card && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <CreditCard className="h-4 w-4 text-teal-600" />
              Virtual Card Issued
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div>
                <p className="text-xs text-muted-foreground">Card Number</p>
                <p className="font-mono font-medium">
                  •••• •••• •••• {txn.virtual_card.last_four}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Spend Limit</p>
                <p className="font-medium">
                  {formatCurrency(txn.virtual_card.spend_limit)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Merchant Lock</p>
                <p className="font-medium">
                  {txn.virtual_card.merchant_lock ?? "None"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Expires</p>
                <p className="font-medium">
                  {new Date(txn.virtual_card.expires_at).toLocaleTimeString()}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Conversation Context */}
      {txn.conversation_context && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Agent Context
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground italic">
              "{txn.conversation_context}"
            </p>
          </CardContent>
        </Card>
      )}

      {/* Timeline */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <TimelineItem
              label="Created"
              time={txn.created_at}
            />
            {txn.decided_at && (
              <TimelineItem
                label={
                  txn.decision === "APPROVE"
                    ? "Approved"
                    : txn.decision === "DENY"
                      ? "Denied"
                      : "Decision made"
                }
                time={txn.decided_at}
              />
            )}
            {txn.approval_requested_at && (
              <TimelineItem
                label="Approval requested"
                time={txn.approval_requested_at}
              />
            )}
            {txn.approval_responded_at && (
              <TimelineItem
                label={`User ${txn.approved_by === "USER_APPROVE" ? "approved" : "denied"}`}
                time={txn.approval_responded_at}
              />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function TimelineItem({ label, time }: { label: string; time: string }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className="h-2 w-2 rounded-full bg-teal-600" />
        <span>{label}</span>
      </div>
      <span className="text-xs text-muted-foreground">
        {new Date(time).toLocaleString()}
      </span>
    </div>
  )
}
