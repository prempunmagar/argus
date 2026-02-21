import { useEffect, useState } from "react"
import { Plus } from "lucide-react"
import { toast } from "sonner"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { CategoryCard } from "@/components/categories/CategoryCard"
import {
  CategoryFormDialog,
  type CategoryFormData,
} from "@/components/categories/CategoryFormDialog"
import { api } from "@/lib/api"
import { mockCategories, mockPaymentMethods } from "@/lib/mock-data"
import { useProfile } from "@/hooks/useProfile"
import type { SpendingCategory, PaymentMethod } from "@/lib/types"

const USE_MOCK = !import.meta.env.VITE_API_URL

export function CategoriesPage() {
  const { currentProfile } = useProfile()
  const [categories, setCategories] = useState<SpendingCategory[]>([])
  const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingCategory, setEditingCategory] = useState<
    SpendingCategory | undefined
  >(undefined)

  useEffect(() => {
    async function load() {
      try {
        if (USE_MOCK) {
          setCategories(mockCategories)
          setPaymentMethods(mockPaymentMethods)
        } else {
          const profileParam = currentProfile ? `?profile_id=${currentProfile.id}` : ""
          const [catRes, pmRes] = await Promise.all([
            api.get(`/categories${profileParam}`),
            api.get("/payment-methods").catch(() => ({ data: { payment_methods: [] } })),
          ])
          setCategories(catRes.data.categories)
          setPaymentMethods(pmRes.data.payment_methods ?? pmRes.data ?? [])
        }
      } catch {
        setCategories(mockCategories)
        setPaymentMethods(mockPaymentMethods)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [currentProfile])

  function openCreate() {
    setEditingCategory(undefined)
    setDialogOpen(true)
  }

  function openEdit(category: SpendingCategory) {
    setEditingCategory(category)
    setDialogOpen(true)
  }

  async function handleSave(data: CategoryFormData) {
    try {
      if (USE_MOCK) {
        if (editingCategory) {
          // Update existing in local state
          const selectedPm = paymentMethods.find((pm) => pm.id === data.payment_method_id) ?? null
          setCategories((prev) =>
            prev.map((c) =>
              c.id === editingCategory.id
                ? {
                    ...c,
                    name: data.name,
                    description: data.description,
                    keywords: data.keywords,
                    payment_method: selectedPm ? { id: selectedPm.id, nickname: selectedPm.nickname, method_type: selectedPm.method_type } : undefined,
                    rules: data.rules.map((r, i) => ({
                      id: `rule-${Date.now()}-${i}`,
                      is_active: true,
                      ...r,
                    })),
                  }
                : c
            )
          )
          toast.success("Category updated")
        } else {
          // Create new in local state
          const selectedPmCreate = paymentMethods.find((pm) => pm.id === data.payment_method_id) ?? null
          const newCategory: SpendingCategory = {
            id: `cat-${Date.now()}`,
            name: data.name,
            description: data.description,
            keywords: data.keywords,
            is_default: false,
            payment_method: selectedPmCreate ? { id: selectedPmCreate.id, nickname: selectedPmCreate.nickname, method_type: selectedPmCreate.method_type } : undefined,
            rules: data.rules.map((r, i) => ({
              id: `rule-${Date.now()}-${i}`,
              is_active: true,
              ...r,
            })),
            spending_today: 0,
            spending_this_week: 0,
            spending_this_month: 0,
          }
          setCategories((prev) => [...prev, newCategory])
          toast.success("Category created")
        }
      } else {
        if (editingCategory) {
          const { data: updated } = await api.put(
            `/categories/${editingCategory.id}`,
            data
          )
          setCategories((prev) =>
            prev.map((c) => (c.id === editingCategory.id ? updated : c))
          )
          toast.success("Category updated")
        } else {
          const { data: created } = await api.post("/categories", data)
          setCategories((prev) => [...prev, created])
          toast.success("Category created")
        }
      }
      setDialogOpen(false)
    } catch {
      toast.error("Failed to save category")
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Spending Categories</h1>
          <p className="text-sm text-muted-foreground">
            Manage your spending categories and rules for AI agent purchases
          </p>
        </div>
        <Button
          onClick={openCreate}
          className="bg-teal-600 hover:bg-teal-700 text-white gap-1.5"
        >
          <Plus className="h-4 w-4" />
          Add Category
        </Button>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-64 rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {categories.map((c) => (
            <CategoryCard key={c.id} category={c} onEdit={openEdit} />
          ))}
        </div>
      )}

      <CategoryFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        category={editingCategory}
        onSave={handleSave}
        paymentMethods={paymentMethods}
      />
    </div>
  )
}
