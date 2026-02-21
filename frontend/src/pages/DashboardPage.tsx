import { useEffect } from "react"
import { Wifi, WifiOff } from "lucide-react"
import { TransactionFeed } from "@/components/transactions/TransactionFeed"
import { useTransactions } from "@/hooks/useTransactions"
import { useWebSocket } from "@/hooks/useWebSocket"

export function DashboardPage() {
  const { transactions, loading, fetchTransactions, handleWSMessage } =
    useTransactions()
  const { connected } = useWebSocket(handleWSMessage)

  useEffect(() => {
    fetchTransactions()
  }, [fetchTransactions])

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-muted-foreground">
            Live transaction feed from your AI agents
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs">
          {connected ? (
            <>
              <Wifi className="h-3.5 w-3.5 text-green-600" />
              <span className="text-green-600 font-medium">Live</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-muted-foreground">Offline</span>
            </>
          )}
        </div>
      </div>

      <TransactionFeed
        transactions={transactions}
        loading={loading}
        onUpdate={fetchTransactions}
      />
    </div>
  )
}
