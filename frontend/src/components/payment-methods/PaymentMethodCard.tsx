import { CreditCard, Landmark, Wallet, Pencil } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { PaymentMethod } from "@/lib/types"

const TYPE_LABELS: Record<PaymentMethod["type"], string> = {
  CREDIT_CARD: "Credit Card",
  DEBIT_CARD: "Debit Card",
  BANK_ACCOUNT: "Bank Account",
  CRYPTO_WALLET: "Crypto Wallet",
}

function ProviderIcon({ type }: { type: PaymentMethod["type"] }) {
  if (type === "BANK_ACCOUNT") return <Landmark className="h-5 w-5 text-muted-foreground" />
  if (type === "CRYPTO_WALLET") return <Wallet className="h-5 w-5 text-muted-foreground" />
  return <CreditCard className="h-5 w-5 text-muted-foreground" />
}

export function PaymentMethodCard({
  method,
  onEdit,
}: {
  method: PaymentMethod
  onEdit?: (method: PaymentMethod) => void
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 py-4">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100">
          <ProviderIcon type={method.type} />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-medium truncate">{method.label}</p>
            {method.is_default && (
              <Badge variant="secondary" className="text-[10px]">
                Default
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2 mt-0.5">
            <Badge variant="outline" className="text-[10px] font-normal">
              {TYPE_LABELS[method.type]}
            </Badge>
            <span className="text-xs text-muted-foreground capitalize">
              {method.provider}
            </span>
          </div>
        </div>

        {onEdit && (
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8 shrink-0 text-muted-foreground hover:text-foreground"
            onClick={() => onEdit(method)}
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
