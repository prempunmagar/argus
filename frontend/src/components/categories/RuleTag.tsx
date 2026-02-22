import { Badge } from "@/components/ui/badge"
import type { CategoryRule } from "@/lib/types"

const labels: Record<string, string> = {
  MAX_PER_TRANSACTION: "Max/txn",
  DAILY_LIMIT: "Daily limit",
  WEEKLY_LIMIT: "Weekly limit",
  MONTHLY_LIMIT: "Monthly limit",
  AUTO_APPROVE_UNDER: "Auto-approve under",
  MERCHANT_WHITELIST: "Whitelist",
  MERCHANT_BLACKLIST: "Blacklist",
  ALWAYS_REQUIRE_APPROVAL: "Require approval",
  BLOCK_CATEGORY: "Blocked",
  CUSTOM_RULE: "Custom Rule",
}

function formatValue(rule: CategoryRule): string {
  const { rule_type, value } = rule
  if (
    ["MAX_PER_TRANSACTION", "DAILY_LIMIT", "WEEKLY_LIMIT", "MONTHLY_LIMIT", "AUTO_APPROVE_UNDER"].includes(
      rule_type
    )
  ) {
    return `$${parseFloat(value).toFixed(0)}`
  }
  if (rule_type === "MERCHANT_WHITELIST" || rule_type === "MERCHANT_BLACKLIST") {
    try {
      const arr = JSON.parse(value) as string[]
      return `${arr.length} merchant${arr.length !== 1 ? "s" : ""}`
    } catch {
      return value
    }
  }
  if (rule_type === "ALWAYS_REQUIRE_APPROVAL") return value === "true" ? "On" : "Off"
  if (rule_type === "BLOCK_CATEGORY") return value === "true" ? "Blocked" : "Active"
  return value
}

export function RuleTag({ rule }: { rule: CategoryRule }) {
  return (
    <Badge variant="outline" className="text-xs font-normal gap-1">
      <span className="font-medium">{labels[rule.rule_type] ?? rule.rule_type}:</span>
      <span>{formatValue(rule)}</span>
    </Badge>
  )
}
