import { useState, useCallback } from "react"
import { api } from "@/lib/api"
import { mockTransactions } from "@/lib/mock-data"
import type { Transaction, TransactionStatus, WSMessage } from "@/lib/types"

const USE_MOCK = !import.meta.env.VITE_API_URL

export function useTransactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)

  const fetchTransactions = useCallback(async () => {
    setLoading(true)
    try {
      if (USE_MOCK) {
        setTransactions(mockTransactions)
      } else {
        const { data } = await api.get("/transactions", {
          params: { limit: 50, sort: "created_at_desc" },
        })
        setTransactions(data.transactions)
      }
    } catch {
      if (USE_MOCK) setTransactions(mockTransactions)
    } finally {
      setLoading(false)
    }
  }, [])

  const handleWSMessage = useCallback((msg: WSMessage) => {
    switch (msg.type) {
      case "TRANSACTION_CREATED":
        setTransactions((prev) => [
          {
            id: msg.data.transaction_id,
            status: "PENDING_EVALUATION",
            request_data: {
              product_name: msg.data.product_name,
              price: msg.data.price,
              currency: "USD",
              merchant_name: msg.data.merchant_name,
              merchant_domain: "",
              merchant_url: "",
            },
            created_at: new Date().toISOString(),
          },
          ...prev,
        ])
        break

      case "TRANSACTION_DECIDED": {
        const newStatus: TransactionStatus =
          msg.data.decision === "APPROVE"
            ? "AI_APPROVED"
            : msg.data.decision === "DENY"
              ? "AI_DENIED"
              : "HUMAN_NEEDED"
        setTransactions((prev) =>
          prev.map((t) =>
            t.id === msg.data.transaction_id
              ? {
                  ...t,
                  status: newStatus,
                  evaluation: {
                    decision: msg.data.decision,
                    category_name: msg.data.category_name,
                    decision_reasoning: msg.data.reason,
                  },
                  virtual_card_last_four: msg.data.virtual_card_last_four,
                }
              : t
          )
        )
        break
      }

      case "APPROVAL_REQUIRED":
        setTransactions((prev) =>
          prev.map((t) =>
            t.id === msg.data.transaction_id
              ? {
                  ...t,
                  status: "HUMAN_NEEDED" as const,
                  evaluation: {
                    decision: "HUMAN_NEEDED" as const,
                    category_name: msg.data.category_name,
                    decision_reasoning: msg.data.reason,
                  },
                }
              : t
          )
        )
        break

      case "VIRTUAL_CARD_USED":
        setTransactions((prev) =>
          prev.map((t) =>
            t.id === msg.data.transaction_id
              ? { ...t, status: "COMPLETED" as const, virtual_card_status: "USED" }
              : t
          )
        )
        break
    }
  }, [])

  return { transactions, loading, fetchTransactions, handleWSMessage }
}
