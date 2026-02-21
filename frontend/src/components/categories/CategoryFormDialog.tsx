import { useState, useEffect, type KeyboardEvent, type ChangeEvent } from "react"
import { Plus, Trash2, X } from "lucide-react"
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
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import type { SpendingCategory, RuleType, PaymentMethod } from "@/lib/types"

export interface CategoryFormData {
  name: string
  description: string
  keywords: string[]
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

const RULE_LABELS: Record<RuleType, string> = {
  MAX_PER_TRANSACTION: "Max per transaction",
  DAILY_LIMIT: "Daily limit",
  WEEKLY_LIMIT: "Weekly limit",
  MONTHLY_LIMIT: "Monthly limit",
  AUTO_APPROVE_UNDER: "Auto-approve under",
  MERCHANT_WHITELIST: "Merchant whitelist",
  MERCHANT_BLACKLIST: "Merchant blacklist",
  ALWAYS_REQUIRE_APPROVAL: "Always require approval",
  BLOCK_CATEGORY: "Block category",
  CUSTOM_RULE: "Custom rule",
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

const ALL_RULE_TYPES = Object.keys(RULE_LABELS) as RuleType[]

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
  const [keywords, setKeywords] = useState<string[]>([])
  const [keywordInput, setKeywordInput] = useState("")
  const [rules, setRules] = useState<{ rule_type: RuleType; value: string }[]>([])
  const [paymentMethodId, setPaymentMethodId] = useState("")
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) {
      setName(category?.name ?? "")
      setDescription(category?.description ?? "")
      setKeywords(category?.keywords ?? [])
      setKeywordInput("")
      setRules(
        category?.rules.map((r) => ({ rule_type: r.rule_type, value: r.value })) ?? []
      )
      setPaymentMethodId(category?.payment_method?.id ?? "")
      setSaving(false)
    }
  }, [open, category])

  const usedRuleTypes = new Set(rules.map((r) => r.rule_type))
  const availableRuleTypes = ALL_RULE_TYPES.filter((rt) => !usedRuleTypes.has(rt))

  function addKeyword() {
    const kw = keywordInput.trim().toLowerCase()
    if (kw && !keywords.includes(kw)) {
      setKeywords((prev) => [...prev, kw])
    }
    setKeywordInput("")
  }

  function removeKeyword(kw: string) {
    setKeywords((prev) => prev.filter((k) => k !== kw))
  }

  function handleKeywordKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault()
      addKeyword()
    }
  }

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
        // If not already JSON, convert comma-separated to JSON
        if (!r.value.startsWith("[")) {
          return { ...r, value: stringToMerchantList(r.value) }
        }
      }
      return r
    })

    onSave({
      name: name.trim(),
      description: description.trim(),
      keywords,
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

            {/* Keywords */}
            <div className="space-y-2">
              <Label>Keywords</Label>
              <p className="text-xs text-muted-foreground">
                Keywords help match purchases to this category.
              </p>
              <div className="flex gap-2">
                <Input
                  placeholder="Type a keyword and press Enter"
                  value={keywordInput}
                  onChange={(e: ChangeEvent<HTMLInputElement>) =>
                    setKeywordInput(e.target.value)
                  }
                  onKeyDown={handleKeywordKeyDown}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addKeyword}
                  className="shrink-0"
                >
                  Add
                </Button>
              </div>
              {keywords.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {keywords.map((kw) => (
                    <Badge
                      key={kw}
                      variant="secondary"
                      className="text-xs gap-1 pr-1"
                    >
                      {kw}
                      <button
                        type="button"
                        onClick={() => removeKeyword(kw)}
                        className="ml-0.5 rounded-full hover:bg-foreground/10 p-0.5"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            <Separator />

            {/* Rules */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Spending Rules</Label>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Define limits and behaviors for this category.
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
        {ALL_RULE_TYPES.map((rt) => (
          <option
            key={rt}
            value={rt}
            disabled={usedTypes.has(rt) && rt !== rule.rule_type}
          >
            {RULE_LABELS[rt]}
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
          onChange={(e: ChangeEvent<HTMLInputElement>) => {
            if (isMerchantList) {
              onChange("value", e.target.value)
            } else {
              onChange("value", e.target.value)
            }
          }}
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
