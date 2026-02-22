import { useState, useEffect, type ChangeEvent } from "react"
import { Plus, Trash2 } from "lucide-react"
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
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { SpendingCategory, RuleType, PaymentMethod } from "@/lib/types"

export interface CategoryFormData {
  name: string
  description: string
  rules: { rule_type: RuleType; value: string }[]
  payment_method_id: string
}

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  category?: SpendingCategory
  onSave: (data: CategoryFormData) => void
  paymentMethods?: PaymentMethod[]
}

// Deterministic rule types shown in the "Spending Rules" section
const DETERMINISTIC_RULE_LABELS: Record<string, string> = {
  MAX_PER_TRANSACTION: "Max per transaction",
  DAILY_LIMIT: "Daily limit",
  WEEKLY_LIMIT: "Weekly limit",
  MONTHLY_LIMIT: "Monthly limit",
  AUTO_APPROVE_UNDER: "Auto-approve under",
  MERCHANT_WHITELIST: "Merchant whitelist",
  MERCHANT_BLACKLIST: "Merchant blacklist",
  ALWAYS_REQUIRE_APPROVAL: "Always require approval",
  BLOCK_CATEGORY: "Block category",
}

const MONETARY_RULES: RuleType[] = [
  "MAX_PER_TRANSACTION",
  "DAILY_LIMIT",
  "WEEKLY_LIMIT",
  "MONTHLY_LIMIT",
  "AUTO_APPROVE_UNDER",
]

const BOOLEAN_RULES: RuleType[] = [
  "ALWAYS_REQUIRE_APPROVAL",
  "BLOCK_CATEGORY",
]

const DETERMINISTIC_RULE_TYPES = Object.keys(DETERMINISTIC_RULE_LABELS) as RuleType[]

function merchantListToString(value: string): string {
  try {
    const arr = JSON.parse(value) as string[]
    return arr.join(", ")
  } catch {
    return value
  }
}

function stringToMerchantList(value: string): string {
  const arr = value
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean)
  return JSON.stringify(arr)
}

export function CategoryFormDialog({ open, onOpenChange, category, onSave, paymentMethods = [] }: Props) {
  const isEdit = !!category

  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [rules, setRules] = useState<{ rule_type: RuleType; value: string }[]>([])
  const [customRule, setCustomRule] = useState("")
  const [paymentMethodId, setPaymentMethodId] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      setName(category?.name ?? "")
      setDescription(category?.description ?? "")
      // Separate deterministic rules from custom rule
      const allRules = category?.rules.map((r) => ({ rule_type: r.rule_type, value: r.value })) ?? []
      setRules(allRules.filter((r) => r.rule_type !== "CUSTOM_RULE"))
      const existing = allRules.find((r) => r.rule_type === "CUSTOM_RULE")
      setCustomRule(existing?.value ?? "")
      setPaymentMethodId(category?.payment_method?.id ?? "")
      setSaving(false)
    }
  }, [open, category])

  const usedRuleTypes = new Set(rules.map((r) => r.rule_type))
  const availableRuleTypes = DETERMINISTIC_RULE_TYPES.filter((rt) => !usedRuleTypes.has(rt))

  function addRule() {
    if (availableRuleTypes.length === 0) return
    const defaultType = availableRuleTypes[0]
    const defaultValue = BOOLEAN_RULES.includes(defaultType) ? "true" : ""
    setRules((prev) => [...prev, { rule_type: defaultType, value: defaultValue }])
  }

  function updateRule(index: number, field: "rule_type" | "value", val: string) {
    setRules((prev) =>
      prev.map((r, i) => {
        if (i !== index) return r
        if (field === "rule_type") {
          const newType = val as RuleType
          const newValue = BOOLEAN_RULES.includes(newType) ? "true" : ""
          return { rule_type: newType, value: newValue }
        }
        return { ...r, value: val }
      })
    )
  }

  function removeRule(index: number) {
    setRules((prev) => prev.filter((_, i) => i !== index))
  }

  async function handleSubmit() {
    if (!name.trim()) return
    setSaving(true)

    const finalRules = rules.map((r) => {
      if (r.rule_type === "MERCHANT_WHITELIST" || r.rule_type === "MERCHANT_BLACKLIST") {
        if (!r.value.startsWith("[")) {
          return { ...r, value: stringToMerchantList(r.value) }
        }
      }
      return r
    })

    // Append custom rule if user wrote one
    if (customRule.trim()) {
      finalRules.push({ rule_type: "CUSTOM_RULE" as RuleType, value: customRule.trim() })
    }

    onSave({
      name: name.trim(),
      description: description.trim(),
      rules: finalRules,
      payment_method_id: paymentMethodId,
    })
    setSaving(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Edit Category" : "Create Category"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Modify this category's rules and description."
              : "Define a new spending category for your AI agent."}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="max-h-[65vh] pr-4">
          <div className="space-y-5 py-1">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="cat-name">Category Name</Label>
              <Input
                id="cat-name"
                placeholder="e.g., Travel, Electronics, Groceries"
                value={name}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
                maxLength={100}
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="cat-desc">Description</Label>
              <p className="text-xs text-muted-foreground">
                This description is sent to Gemini AI to determine how purchases are
                categorized and whether they should be approved. Be specific about what
                belongs here and any merchant preferences.
              </p>
              <Textarea
                id="cat-desc"
                rows={4}
                placeholder="e.g., This category covers flights, hotels, car rentals, and travel accessories. Only purchases from trusted booking sites like Marriott.com, Airbnb, and Booking.com should be allowed. Budget items under $200/night are fine to auto-approve."
                value={description}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                  setDescription(e.target.value)
                }
              />
            </div>

            {/* Payment Method */}
            {paymentMethods.length > 0 && (
              <div className="space-y-2">
                <Label htmlFor="cat-payment">Payment Method</Label>
                <select
                  id="cat-payment"
                  value={paymentMethodId}
                  onChange={(e) => setPaymentMethodId(e.target.value)}
                  className="h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  <option value="">None (use default)</option>
                  {paymentMethods.map((pm) => (
                    <option key={pm.id} value={pm.id}>
                      {pm.nickname}
                    </option>
                  ))}
                </select>
              </div>
            )}

            <Separator />

            {/* Spending Rules (deterministic only) */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Spending Rules</Label>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Define hard limits and behaviors. These are checked deterministically
                    before AI evaluation.
                  </p>
                </div>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addRule}
                  disabled={availableRuleTypes.length === 0}
                  className="shrink-0 gap-1"
                >
                  <Plus className="h-3.5 w-3.5" />
                  Add Rule
                </Button>
              </div>

              {rules.length === 0 && (
                <p className="text-xs text-muted-foreground italic py-2">
                  No rules defined. All purchases in this category will follow default
                  behavior.
                </p>
              )}

              <div className="space-y-2">
                {rules.map((rule, idx) => (
                  <RuleRow
                    key={idx}
                    rule={rule}
                    usedTypes={usedRuleTypes}
                    onChange={(field, val) => updateRule(idx, field, val)}
                    onRemove={() => removeRule(idx)}
                  />
                ))}
              </div>
            </div>

            <Separator />

            {/* Custom AI Rule (separate from deterministic rules) */}
            <div className="space-y-2">
              <Label htmlFor="cat-custom-rule">Custom AI Rule</Label>
              <p className="text-xs text-muted-foreground">
                Custom rule to evaluate. Leave blank if not needed.
              </p>
              <Textarea
                id="cat-custom-rule"
                rows={3}
                placeholder="e.g., Only approve if the product has 4+ star reviews and is from a US-based seller. Reject subscription-based products or recurring payments."
                value={customRule}
                onChange={(e: ChangeEvent<HTMLTextAreaElement>) =>
                  setCustomRule(e.target.value)
                }
              />
            </div>
          </div>
        </ScrollArea>

        <DialogFooter className="pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!name.trim() || saving}
            className="bg-teal-600 hover:bg-teal-700 text-white"
          >
            {saving
              ? "Saving..."
              : isEdit
                ? "Save Changes"
                : "Create Category"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function RuleRow({
  rule,
  usedTypes,
  onChange,
  onRemove,
}: {
  rule: { rule_type: RuleType; value: string }
  usedTypes: Set<RuleType>
  onChange: (field: "rule_type" | "value", val: string) => void
  onRemove: () => void
}) {
  const isMerchantList =
    rule.rule_type === "MERCHANT_WHITELIST" ||
    rule.rule_type === "MERCHANT_BLACKLIST"
  const isBoolean = BOOLEAN_RULES.includes(rule.rule_type)
  const isMonetary = MONETARY_RULES.includes(rule.rule_type)

  const displayValue = isMerchantList ? merchantListToString(rule.value) : rule.value

  return (
    <div className="flex items-center gap-2">
      <select
        value={rule.rule_type}
        onChange={(e) => onChange("rule_type", e.target.value)}
        className="h-9 rounded-md border border-input bg-transparent px-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring min-w-[160px]"
      >
        {DETERMINISTIC_RULE_TYPES.map((rt) => (
          <option
            key={rt}
            value={rt}
            disabled={usedTypes.has(rt) && rt !== rule.rule_type}
          >
            {DETERMINISTIC_RULE_LABELS[rt]}
          </option>
        ))}
      </select>

      {isBoolean ? (
        <Button
          type="button"
          variant={rule.value === "true" ? "default" : "outline"}
          size="sm"
          className={
            rule.value === "true"
              ? "bg-teal-600 hover:bg-teal-700 text-white"
              : ""
          }
          onClick={() => onChange("value", rule.value === "true" ? "false" : "true")}
        >
          {rule.value === "true" ? "On" : "Off"}
        </Button>
      ) : (
        <Input
          type={isMonetary ? "number" : "text"}
          step={isMonetary ? "0.01" : undefined}
          min={isMonetary ? "0" : undefined}
          placeholder={
            isMerchantList
              ? "amazon.com, nike.com, target.com"
              : isMonetary
                ? "0.00"
                : ""
          }
          value={displayValue}
          onChange={(e: ChangeEvent<HTMLInputElement>) =>
            onChange("value", e.target.value)
          }
          className="flex-1"
        />
      )}

      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="shrink-0 text-muted-foreground hover:text-destructive h-8 w-8"
        onClick={onRemove}
      >
        <Trash2 className="h-3.5 w-3.5" />
      </Button>
    </div>
  )
}
