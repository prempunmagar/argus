import { CreditCard, Pencil } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { RuleTag } from "./RuleTag"
import { formatCurrency } from "@/lib/utils"
import type { SpendingCategory } from "@/lib/types"

function LimitBar({
  label,
  spent,
  limit,
}: {
  label: string
  spent: number
  limit: number
}) {
  const pct = limit > 0 ? Math.min((spent / limit) * 100, 100) : 0
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">
          {formatCurrency(spent)} / {formatCurrency(limit)}
        </span>
      </div>
      <Progress value={pct} className="h-1.5" />
    </div>
  )
}

export function CategoryCard({
  category: c,
  onEdit,
}: {
  category: SpendingCategory
  onEdit?: (category: SpendingCategory) => void
}) {
  const dailyLimit = c.rules.find((r) => r.rule_type === "DAILY_LIMIT")
  const monthlyLimit = c.rules.find((r) => r.rule_type === "MONTHLY_LIMIT")

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            {c.name}
            {c.is_default && (
              <Badge variant="secondary" className="text-[10px]">
                Default
              </Badge>
            )}
          </CardTitle>
          <div className="flex items-center gap-1.5 shrink-0">
            {c.payment_method && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <CreditCard className="h-3.5 w-3.5" />
                <span>{c.payment_method.label}</span>
              </div>
            )}
            {onEdit && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-foreground"
                onClick={() => onEdit(c)}
              >
                <Pencil className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>
        {c.description && (
          <p className="text-xs text-muted-foreground mt-1">{c.description}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {c.keywords.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {c.keywords.map((kw) => (
              <Badge key={kw} variant="secondary" className="text-[11px] font-normal">
                {kw}
              </Badge>
            ))}
          </div>
        )}

        <div className="flex flex-wrap gap-1.5">
          {c.rules.map((rule) => (
            <RuleTag key={rule.id} rule={rule} />
          ))}
        </div>

        <div className="space-y-2">
          {dailyLimit && (
            <LimitBar
              label="Today"
              spent={c.spending_today}
              limit={parseFloat(dailyLimit.value)}
            />
          )}
          {monthlyLimit && (
            <LimitBar
              label="This month"
              spent={c.spending_this_month}
              limit={parseFloat(monthlyLimit.value)}
            />
          )}
        </div>
      </CardContent>
    </Card>
  )
}
