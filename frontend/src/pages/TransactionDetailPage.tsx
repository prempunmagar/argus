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
  MessageSquareText,
  Clock,
  FileQuestion,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { StatusBadge } from "@/components/transactions/StatusBadge"
import { useTransactions } from "@/hooks/useTransactions"
import { formatCurrency } from "@/lib/utils"
import { api } from "@/lib/api"
import type { TransactionDetail } from "@/lib/types"

function toTitleCase(str: string): string {
  return str
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b\w/g, (c) => c.toUpperCase())
}

export function TransactionDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { updateTransaction } = useTransactions()
  const [txn, setTxn] = useState<TransactionDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const { data } = await api.get(`/transactions/${id}`)
        setTxn(data)
      } catch {
        setTxn(null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [id])

  async function handleApprove() {
    if (!txn) return
    try {
      await api.post(`/transactions/${txn.id}/respond`, { action: "APPROVE" })
      updateTransaction(txn.id, { status: "HUMAN_APPROVED" })
      setTxn((prev) => prev ? { ...prev, status: "HUMAN_APPROVED" } : prev)
    } catch {
      // handle error
    }
  }

  async function handleDeny() {
    if (!txn) return
    try {
      await api.post(`/transactions/${txn.id}/respond`, { action: "DENY" })
      updateTransaction(txn.id, { status: "HUMAN_DENIED" })
      setTxn((prev) => prev ? { ...prev, status: "HUMAN_DENIED" } : prev)
    } catch {
      // handle error
    }
  }

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
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
            <FileQuestion className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium">Transaction not found</p>
          <p className="text-xs text-muted-foreground mt-1 mb-4">
            This transaction may have been removed or the ID is invalid.
          </p>
          <Button variant="outline" size="sm" onClick={() => navigate("/")}>
            <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
            Back to Dashboard
          </Button>
        </div>
      </div>
    )
  }

  // Build timeline events
  const timeline: { label: string; time: string }[] = [
    { label: "Request created", time: txn.created_at },
  ]
  if (txn.evaluation) {
    const evalLabel =
      txn.evaluation.decision === "APPROVE"
        ? "AI approved"
        : txn.evaluation.decision === "DENY"
          ? "AI denied"
          : "Escalated to human review"
    timeline.push({
      label: evalLabel,
      time: txn.updated_at ?? txn.created_at,
    })
  }
  if (txn.virtual_card) {
    timeline.push({
      label: "Virtual card issued",
      time: txn.updated_at ?? txn.created_at,
    })
  }
  if (txn.status === "HUMAN_APPROVED") {
    timeline.push({ label: "Human approved", time: txn.updated_at ?? txn.created_at })
  } else if (txn.status === "HUMAN_DENIED") {
    timeline.push({ label: "Human denied", time: txn.updated_at ?? txn.created_at })
  } else if (txn.status === "HUMAN_TIMEOUT") {
    timeline.push({ label: "Approval timed out", time: txn.updated_at ?? txn.created_at })
  } else if (txn.status === "COMPLETED") {
    timeline.push({ label: "Transaction completed", time: txn.updated_at ?? txn.created_at })
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
          <h1 className="text-xl font-semibold">{txn.request_data.product_name}</h1>
          <div className="flex items-center gap-2 mt-1">
            <StatusBadge status={txn.status} />
            <span className="text-sm text-muted-foreground">
              {txn.request_data.merchant_name}
            </span>
            {txn.request_data.product_url && (
              <a
                href={txn.request_data.product_url}
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
          {formatCurrency(txn.request_data.price, txn.request_data.currency)}
        </p>
      </div>

      {/* Approve / Deny actions */}
      {txn.status === "HUMAN_NEEDED" && (
        <div className="flex gap-3">
          <Button
            variant="outline"
            className="flex-1 text-red-600 border-red-200 hover:bg-red-50"
            onClick={handleDeny}
          >
            Deny
          </Button>
          <Button
            className="flex-1 bg-green-600 hover:bg-green-700 text-white"
            onClick={handleApprove}
          >
            Approve
          </Button>
        </div>
      )}

      {/* Decision Reasoning */}
      {txn.evaluation?.decision_reasoning && (
        <Card>
          <CardContent className="p-4 text-sm">
            <p
              className={
                txn.evaluation.decision === "DENY"
                  ? "text-red-600"
                  : txn.evaluation.decision === "HUMAN_NEEDED"
                    ? "text-amber-700"
                    : "text-foreground"
              }
            >
              {txn.evaluation.decision_reasoning}
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
      {txn.evaluation?.rules_checked && txn.evaluation.rules_checked.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <ListChecks className="h-4 w-4 text-teal-600" />
              Rules Evaluation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {txn.evaluation.rules_checked.map((r, i) => (
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
                      {toTitleCase(r.rule_type)}
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
                  {new Date(txn.virtual_card.expires_at).toLocaleString(undefined, {
                    month: "short",
                    day: "numeric",
                    hour: "numeric",
                    minute: "2-digit",
                  })}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Conversation Context */}
      {txn.request_data.conversation_context && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <MessageSquareText className="h-4 w-4 text-teal-600" />
              Agent Context
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground italic">
              "{txn.request_data.conversation_context}"
            </p>
          </CardContent>
        </Card>
      )}

      {/* Timeline */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Clock className="h-4 w-4 text-teal-600" />
            Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative pl-5 space-y-4">
            {/* Vertical line */}
            <div className="absolute left-[3px] top-1 bottom-1 w-px bg-border" />
            {timeline.map((event, i) => (
              <div key={i} className="relative flex items-start gap-3">
                <div className="absolute -left-5 top-1.5 h-2 w-2 rounded-full bg-teal-600 ring-2 ring-background" />
                <div className="flex-1 flex items-center justify-between">
                  <span className="text-sm">{event.label}</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(event.time).toLocaleString(undefined, {
                      month: "short",
                      day: "numeric",
                      hour: "numeric",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
