import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  useRef,
  type ReactNode,
} from "react"
import { api } from "@/lib/api"
import { mockTransactions } from "@/lib/mock-data"
import type { Transaction, TransactionStatus, WSMessage } from "@/lib/types"

const USE_MOCK = !import.meta.env.VITE_API_URL
const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/dashboard"

interface TransactionContextValue {
  transactions: Transaction[]
  loading: boolean
  connected: boolean
  pendingCount: number
  fetchTransactions: () => Promise<void>
  updateTransaction: (id: string, updates: Partial<Transaction>) => void
}

const TransactionContext = createContext<TransactionContextValue | null>(null)

export function TransactionProvider({ children }: { children: ReactNode }) {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined)

  const pendingCount = transactions.filter(
    (t) => t.status === "HUMAN_NEEDED"
  ).length

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

  const updateTransaction = useCallback(
    (id: string, updates: Partial<Transaction>) => {
      setTransactions((prev) =>
        prev.map((t) => (t.id === id ? { ...t, ...updates } : t))
      )
    },
    []
  )

  // WebSocket
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
                  virtual_card_last_four: msg.data.virtual_card_last_four ?? undefined,
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

  const connectWS = useCallback(() => {
    const token = localStorage.getItem("argus_token")
    if (!token) return

    const ws = new WebSocket(`${WS_URL}?token=${token}`)
    wsRef.current = ws

    ws.onopen = () => setConnected(true)

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data) as WSMessage
        handleWSMessage(msg)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = () => {
      setConnected(false)
      reconnectTimer.current = setTimeout(connectWS, 3000)
    }

    ws.onerror = () => {
      ws.close()
    }
  }, [handleWSMessage])

  // Fetch on mount, connect WebSocket
  useEffect(() => {
    fetchTransactions()
    connectWS()
    return () => {
      clearTimeout(reconnectTimer.current)
      wsRef.current?.close()
    }
  }, [fetchTransactions, connectWS])

  return (
    <TransactionContext.Provider
      value={{
        transactions,
        loading,
        connected,
        pendingCount,
        fetchTransactions,
        updateTransaction,
      }}
    >
      {children}
    </TransactionContext.Provider>
  )
}

export function useTransactions() {
  const ctx = useContext(TransactionContext)
  if (!ctx) throw new Error("useTransactions must be used within TransactionProvider")
  return ctx
}
