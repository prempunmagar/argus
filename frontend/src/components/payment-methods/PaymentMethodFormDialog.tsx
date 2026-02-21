import { useState, useEffect, type ChangeEvent } from "react"
import { CreditCard, Landmark, Wallet } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { toast } from "sonner"
import type { PaymentMethod } from "@/lib/types"

export interface PaymentMethodFormData {
  nickname: string
  method_type: PaymentMethod["method_type"]
  detail: Record<string, any>
  is_default: boolean
}

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  method?: PaymentMethod
  onSave: (data: PaymentMethodFormData) => void
  onDelete?: (id: string) => void
}

function detectBrand(num: string): string {
  if (num.startsWith("4")) return "visa"
  if (/^5[1-5]/.test(num) || /^2[2-7]/.test(num)) return "mastercard"
  if (num.startsWith("3") && (num[1] === "4" || num[1] === "7")) return "amex"
  if (num.startsWith("6")) return "discover"
  return "unknown"
}

function formatCardNumber(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 16)
  return digits.replace(/(.{4})/g, "$1 ").trim()
}

export function PaymentMethodFormDialog({ open, onOpenChange, method, onSave, onDelete }: Props) {
  const isEdit = !!method

  const [nickname, setNickname] = useState("")
  const [methodType, setMethodType] = useState<PaymentMethod["method_type"]>("CARD")
  const [isDefault, setIsDefault] = useState(false)
  const [saving, setSaving] = useState(false)

  // Card fields
  const [cardNumber, setCardNumber] = useState("")
  const [expiry, setExpiry] = useState("")
  const [cvv, setCvv] = useState("")
  const [billingZip, setBillingZip] = useState("")

  const isCard = methodType === "CARD"
  const isBank = methodType === "BANK_ACCOUNT"
  const isCrypto = methodType === "CRYPTO_WALLET"

  useEffect(() => {
    if (open) {
      setNickname(method?.nickname ?? "")
      setMethodType(method?.method_type ?? "CARD")
      setIsDefault(method?.is_default ?? false)
      setSaving(false)

      const d = method?.detail ?? {}
      const last4 = (d.last4 as string) ?? ""
      setCardNumber(last4 ? `•••• •••• •••• ${last4}` : "")
      const em = d.exp_month != null ? String(d.exp_month).padStart(2, "0") : ""
      const ey = d.exp_year != null ? String(d.exp_year).slice(-2) : ""
      setExpiry(em && ey ? `${em}/${ey}` : "")
      setCvv("")
      setBillingZip((d.billing_zip as string) ?? "")
    }
  }, [open, method])

  function formatExpiry(raw: string): string {
    const digits = raw.replace(/\D/g, "").slice(0, 4)
    if (digits.length > 2) return digits.slice(0, 2) + "/" + digits.slice(2)
    return digits
  }

  function handleSubmit() {
    if (!nickname.trim()) return
    setSaving(true)

    const digits = cardNumber.replace(/\D/g, "")
    const [mm, yy] = expiry.split("/")
    const detail: Record<string, any> = {
      brand: detectBrand(digits),
      last4: digits.slice(-4),
      exp_month: parseInt(mm) || 0,
      exp_year: yy ? 2000 + parseInt(yy) : 0,
      billing_zip: billingZip,
      country: "US",
    }

    onSave({
      nickname: nickname.trim(),
      method_type: "CARD",
      detail,
      is_default: isDefault,
    })
    setSaving(false)
  }

  function handleConnectPlaid() {
    toast.info("Plaid integration coming soon", {
      description: "Bank account linking via Plaid will be available in production.",
    })
  }

  function handleConnectWallet() {
    toast.info("Wallet connection coming soon", {
      description: "WalletConnect / MetaMask integration will be available in production.",
    })
  }

  const cardValid =
    nickname.trim() &&
    cardNumber.replace(/\D/g, "").length >= 13 &&
    expiry.length === 5 &&
    cvv.length >= 3

  // ---- Card form (edit mode for card) ----
  if (isEdit && method?.method_type !== "CARD") {
    // Editing a bank/crypto — just show nickname + default toggle
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Edit Payment Method</DialogTitle>
            <DialogDescription>Update this payment method's details.</DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-1">
            <div className="space-y-2">
              <Label htmlFor="pm-nickname">Nickname</Label>
              <Input
                id="pm-nickname"
                value={nickname}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setNickname(e.target.value)}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="pm-default">Default payment method</Label>
              <Switch id="pm-default" checked={isDefault} onCheckedChange={setIsDefault} />
            </div>
          </div>

          <DialogFooter className="pt-2">
            {onDelete && (
              <Button
                variant="ghost"
                className="mr-auto text-red-600 hover:text-red-700 hover:bg-red-50"
                onClick={() => onDelete(method!.id)}
              >
                Remove
              </Button>
            )}
            <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button
              onClick={() => {
                onSave({
                  nickname: nickname.trim(),
                  method_type: method!.method_type,
                  detail: method!.detail,
                  is_default: isDefault,
                })
              }}
              disabled={!nickname.trim()}
              className="bg-teal-600 hover:bg-teal-700 text-white"
            >
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Payment Method" : "Add Payment Method"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update this payment method's details."
              : "Add a funding source for AI agent purchases."}
          </DialogDescription>
        </DialogHeader>

        {/* Type selector (only for create) */}
        {!isEdit && (
          <div className="flex gap-2">
            {([
              { type: "CARD" as const, icon: CreditCard, label: "Card" },
              { type: "BANK_ACCOUNT" as const, icon: Landmark, label: "Bank" },
              { type: "CRYPTO_WALLET" as const, icon: Wallet, label: "Crypto" },
            ]).map(({ type, icon: Icon, label }) => (
              <button
                key={type}
                type="button"
                onClick={() => setMethodType(type)}
                className={`flex-1 flex flex-col items-center gap-1.5 rounded-lg border-2 py-3 px-2 text-xs font-medium transition-colors ${
                  methodType === type
                    ? "border-teal-600 bg-teal-50 text-teal-700"
                    : "border-muted hover:border-muted-foreground/30 text-muted-foreground"
                }`}
              >
                <Icon className="h-5 w-5" />
                {label}
              </button>
            ))}
          </div>
        )}

        {/* ---- Card Form ---- */}
        {isCard && (
          <div className="space-y-4 py-1">
            <div className="space-y-2">
              <Label htmlFor="pm-nickname">Nickname</Label>
              <Input
                id="pm-nickname"
                placeholder="e.g., Work Visa Card"
                value={nickname}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setNickname(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pm-card-number">Card Number</Label>
              <Input
                id="pm-card-number"
                placeholder="1234 5678 9012 3456"
                inputMode="numeric"
                autoComplete="cc-number"
                value={cardNumber}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setCardNumber(formatCardNumber(e.target.value))
                }
              />
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-2">
                <Label htmlFor="pm-expiry">Expiry</Label>
                <Input
                  id="pm-expiry"
                  placeholder="MM/YY"
                  maxLength={5}
                  inputMode="numeric"
                  autoComplete="cc-exp"
                  value={expiry}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setExpiry(formatExpiry(e.target.value))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pm-cvv">CVV</Label>
                <Input
                  id="pm-cvv"
                  placeholder="123"
                  maxLength={4}
                  inputMode="numeric"
                  autoComplete="cc-csc"
                  type="password"
                  value={cvv}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setCvv(e.target.value.replace(/\D/g, "").slice(0, 4))
                  }
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="pm-zip">ZIP Code</Label>
                <Input
                  id="pm-zip"
                  placeholder="10001"
                  maxLength={10}
                  autoComplete="postal-code"
                  value={billingZip}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setBillingZip(e.target.value)
                  }
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="pm-default">Default payment method</Label>
              <Switch id="pm-default" checked={isDefault} onCheckedChange={setIsDefault} />
            </div>
          </div>
        )}

        {/* ---- Bank Account ---- */}
        {isBank && !isEdit && (
          <div className="space-y-4 py-1">
            <div className="space-y-2">
              <Label htmlFor="pm-nickname-bank">Nickname</Label>
              <Input
                id="pm-nickname-bank"
                placeholder="e.g., Chase Checking"
                value={nickname}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setNickname(e.target.value)}
              />
            </div>

            <div className="rounded-lg border border-dashed p-6 text-center">
              <Landmark className="h-8 w-8 mx-auto text-muted-foreground mb-3" />
              <p className="text-sm font-medium mb-1">Link your bank account</p>
              <p className="text-xs text-muted-foreground mb-4">
                Securely connect your bank through Plaid. We never store your login credentials.
              </p>
              <Button
                type="button"
                onClick={handleConnectPlaid}
                className="bg-slate-800 hover:bg-slate-900 text-white gap-2"
              >
                <Landmark className="h-4 w-4" />
                Connect with Plaid
              </Button>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="pm-default-bank">Default payment method</Label>
              <Switch id="pm-default-bank" checked={isDefault} onCheckedChange={setIsDefault} />
            </div>
          </div>
        )}

        {/* ---- Crypto Wallet ---- */}
        {isCrypto && !isEdit && (
          <div className="space-y-4 py-1">
            <div className="space-y-2">
              <Label htmlFor="pm-nickname-crypto">Nickname</Label>
              <Input
                id="pm-nickname-crypto"
                placeholder="e.g., My ETH Wallet"
                value={nickname}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setNickname(e.target.value)}
              />
            </div>

            <div className="rounded-lg border border-dashed p-6 text-center">
              <Wallet className="h-8 w-8 mx-auto text-muted-foreground mb-3" />
              <p className="text-sm font-medium mb-1">Connect your wallet</p>
              <p className="text-xs text-muted-foreground mb-4">
                Link your wallet through WalletConnect or MetaMask to fund agent purchases.
              </p>
              <Button
                type="button"
                onClick={handleConnectWallet}
                className="bg-slate-800 hover:bg-slate-900 text-white gap-2"
              >
                <Wallet className="h-4 w-4" />
                Connect Wallet
              </Button>
            </div>

            <div className="flex items-center justify-between">
              <Label htmlFor="pm-default-crypto">Default payment method</Label>
              <Switch id="pm-default-crypto" checked={isDefault} onCheckedChange={setIsDefault} />
            </div>
          </div>
        )}

        {/* Footer */}
        {isCard && (
          <DialogFooter className="pt-2">
            {isEdit && onDelete && (
              <Button
                variant="ghost"
                className="mr-auto text-red-600 hover:text-red-700 hover:bg-red-50"
                onClick={() => onDelete(method!.id)}
              >
                Remove
              </Button>
            )}
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!cardValid || saving}
              className="bg-teal-600 hover:bg-teal-700 text-white"
            >
              {saving ? "Saving..." : isEdit ? "Save Changes" : "Add Card"}
            </Button>
          </DialogFooter>
        )}

        {(isBank || isCrypto) && !isEdit && (
          <DialogFooter className="pt-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
