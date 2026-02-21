import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { TransactionCard } from "./TransactionCard"
import type { TransactionListItem } from "@/lib/types"

interface Props {
  transactions: TransactionListItem[]
  loading: boolean
  onUpdate?: () => void
}

export function TransactionFeed({ transactions, loading, onUpdate }: Props) {
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
      <div className="flex flex-col items-center justify-center py-16 text-muted-foreground">
        <p className="text-sm">No transactions yet</p>
        <p className="text-xs mt-1">
          Transactions will appear here when your AI agent makes purchases.
        </p>
      </div>
    )
  }

  return (
    <ScrollArea className="h-[calc(100vh-12rem)]">
      <div className="space-y-3 pr-4">
        {transactions.map((t) => (
          <TransactionCard key={t.id} transaction={t} onUpdate={onUpdate} />
        ))}
      </div>
    </ScrollArea>
  )
}
