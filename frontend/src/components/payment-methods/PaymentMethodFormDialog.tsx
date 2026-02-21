import { useState, useEffect, type ChangeEvent } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
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
}

export function PaymentMethodFormDialog({ open, onOpenChange, method, onSave }: Props) {
  const isEdit = !!method

  const [nickname, setNickname] = useState("")
  const [methodType, setMethodType] = useState<PaymentMethod["method_type"]>("CREDIT_CARD")
  const [brand, setBrand] = useState("visa")
  const [lastFour, setLastFour] = useState("")
  const [isDefault, setIsDefault] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      setNickname(method?.nickname ?? "")
      setMethodType(method?.method_type ?? "CREDIT_CARD")
      setBrand(method?.detail?.brand ?? "visa")
      setLastFour(method?.detail?.last_four ?? "")
      setIsDefault(method?.is_default ?? false)
      setSaving(false)
    }
  }, [open, method])

  function handleSubmit() {
    if (!nickname.trim()) return
    setSaving(true)
    onSave({
      nickname: nickname.trim(),
      method_type: methodType,
      detail: {
        brand,
        ...(lastFour ? { last_four: lastFour } : {}),
      },
      is_default: isDefault,
    })
    setSaving(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Payment Method" : "Add Payment Method"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Update this payment method's details."
              : "Add a new payment method for AI agent purchases."}
          </DialogDescription>
        </DialogHeader>

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
            <Label htmlFor="pm-type">Type</Label>
            <select
              id="pm-type"
              value={methodType}
              onChange={(e) => setMethodType(e.target.value as PaymentMethod["method_type"])}
              className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="CREDIT_CARD">Credit Card</option>
              <option value="DEBIT_CARD">Debit Card</option>
              <option value="BANK_ACCOUNT">Bank Account</option>
              <option value="CRYPTO_WALLET">Crypto Wallet</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="pm-brand">Brand</Label>
            <Input
              id="pm-brand"
              placeholder="e.g., visa, mastercard, bitcoin"
              value={brand}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setBrand(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="pm-last-four">Last 4 Digits (optional)</Label>
            <Input
              id="pm-last-four"
              placeholder="e.g., 4242"
              maxLength={4}
              value={lastFour}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setLastFour(e.target.value)}
            />
          </div>

          <div className="flex items-center gap-3">
            <Label htmlFor="pm-default">Set as Default</Label>
            <Button
              id="pm-default"
              type="button"
              variant={isDefault ? "default" : "outline"}
              size="sm"
              className={isDefault ? "bg-teal-600 hover:bg-teal-700 text-white" : ""}
              onClick={() => setIsDefault(!isDefault)}
            >
              {isDefault ? "Yes" : "No"}
            </Button>
          </div>
        </div>

        <DialogFooter className="pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!nickname.trim() || saving}
            className="bg-teal-600 hover:bg-teal-700 text-white"
          >
            {saving ? "Saving..." : isEdit ? "Save Changes" : "Add Payment Method"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
