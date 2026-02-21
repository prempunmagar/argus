import { CreditCard, Landmark, Wallet, Star } from "lucide-react"
import type { PaymentMethod } from "@/lib/types"

const TYPE_LABELS: Record<PaymentMethod["method_type"], string> = {
  CARD: "Credit / Debit Card",
  BANK_ACCOUNT: "Bank Account",
  CRYPTO_WALLET: "Crypto Wallet",
}

function MethodIcon({ type }: { type: PaymentMethod["method_type"] }) {
  const cls = "h-5 w-5 text-white"
  if (type === "BANK_ACCOUNT") return <Landmark className={cls} />
  if (type === "CRYPTO_WALLET") return <Wallet className={cls} />
  return <CreditCard className={cls} />
}

function detailSummary(method: PaymentMethod): string {
  const d = method.detail ?? {}
  const type = method.method_type

  if (type === "CARD") {
    const brand = (d.brand as string) ?? ""
    const last4 = (d.last4 as string) ?? ""
    const parts: string[] = []
    if (brand && brand !== "unknown") parts.push(brand.charAt(0).toUpperCase() + brand.slice(1))
    if (last4) parts.push(`••${last4}`)
    return parts.length > 0 ? parts.join(" · ") : TYPE_LABELS[type]
  }

  if (type === "BANK_ACCOUNT") {
    const inst = (d.institution_name as string) ?? ""
    const sub = (d.account_subtype as string) ?? ""
    const mask = (d.account_mask as string) ?? ""
    const parts: string[] = []
    if (inst) parts.push(inst)
    if (sub) parts.push(sub.charAt(0).toUpperCase() + sub.slice(1))
    if (mask) parts.push(`••${mask}`)
    return parts.length > 0 ? parts.join(" · ") : "Bank Account"
  }

  if (type === "CRYPTO_WALLET") {
    const cur = (d.currency as string) ?? ""
    const net = (d.network as string) ?? ""
    const addr = (d.wallet_address as string) ?? ""
    const parts: string[] = []
    if (cur) parts.push(cur)
    if (net) parts.push(net.charAt(0).toUpperCase() + net.slice(1))
    if (addr) parts.push(addr.slice(0, 6) + "..." + addr.slice(-4))
    return parts.length > 0 ? parts.join(" · ") : "Crypto Wallet"
  }

  return TYPE_LABELS[type]
}

export function PaymentMethodCard({
  method,
  onEdit,
}: {
  method: PaymentMethod
  onEdit?: (method: PaymentMethod) => void
}) {
  return (
    <button
      type="button"
      onClick={() => onEdit?.(method)}
      className="w-full flex items-center gap-3 rounded-lg border px-4 py-3 text-left transition-colors hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
    >
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-slate-700">
        <MethodIcon type={method.method_type} />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-medium truncate">{method.nickname}</span>
          {method.is_default && (
            <Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500 shrink-0" />
          )}
        </div>
        <p className="text-xs text-muted-foreground truncate">
          {detailSummary(method)}
        </p>
      </div>
    </button>
  )
}
