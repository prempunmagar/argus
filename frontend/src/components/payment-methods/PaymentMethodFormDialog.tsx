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
  label: string
  type: PaymentMethod["type"]
  provider: string
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

  const [label, setLabel] = useState("")
  const [type, setType] = useState<PaymentMethod["type"]>("CREDIT_CARD")
  const [provider, setProvider] = useState("visa")
  const [isDefault, setIsDefault] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      setLabel(method?.label ?? "")
      setType(method?.type ?? "CREDIT_CARD")
      setProvider(method?.provider ?? "visa")
      setIsDefault(method?.is_default ?? false)
      setSaving(false)
    }
  }, [open, method])

  function handleSubmit() {
    if (!label.trim()) return
    setSaving(true)
    onSave({
      label: label.trim(),
      type,
      provider,
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
            <Label htmlFor="pm-label">Label</Label>
            <Input
              id="pm-label"
              placeholder="e.g., Work Visa Card"
              value={label}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setLabel(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="pm-type">Type</Label>
            <select
              id="pm-type"
              value={type}
              onChange={(e) => setType(e.target.value as PaymentMethod["type"])}
              className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <option value="CREDIT_CARD">Credit Card</option>
              <option value="DEBIT_CARD">Debit Card</option>
              <option value="BANK_ACCOUNT">Bank Account</option>
              <option value="CRYPTO_WALLET">Crypto Wallet</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="pm-provider">Provider</Label>
            <Input
              id="pm-provider"
              placeholder="e.g., visa, bitcoin, ethereum"
              value={provider}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setProvider(e.target.value)}
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
            disabled={!label.trim() || saving}
            className="bg-teal-600 hover:bg-teal-700 text-white"
          >
            {saving ? "Saving..." : isEdit ? "Save Changes" : "Add Payment Method"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
