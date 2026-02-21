import { ShoppingBag } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { TransactionCard } from "./TransactionCard"
import type { Transaction } from "@/lib/types"

interface Props {
  transactions: Transaction[]
  loading: boolean
}

export function TransactionFeed({ transactions, loading }: Props) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-lg" />
        ))}
      </div>
    )
  }

  if (transactions.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
          <ShoppingBag className="h-6 w-6 text-muted-foreground" />
        </div>
        <p className="text-sm font-medium">No transactions yet</p>
        <p className="text-xs text-muted-foreground mt-1 max-w-xs">
          Transactions will appear here in real time when your AI agent makes purchases.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {transactions.map((t) => (
        <TransactionCard key={t.id} transaction={t} />
      ))}
    </div>
  )
}
