import { useEffect, useState } from "react"
import { Plus, Layers } from "lucide-react"
import { toast } from "sonner"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { CategoryCard } from "@/components/categories/CategoryCard"
import {
  CategoryFormDialog,
  type CategoryFormData,
} from "@/components/categories/CategoryFormDialog"
import { api } from "@/lib/api"
import { useProfile } from "@/hooks/useProfile"
import type { SpendingCategory, PaymentMethod } from "@/lib/types"

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
        const profileParam = currentProfile ? `?profile_id=${currentProfile.id}` : ""
        const [catRes, pmRes] = await Promise.all([
          api.get(`/categories${profileParam}`),
          api.get("/payment-methods").catch(() => ({ data: { payment_methods: [] } })),
        ])
        setCategories(catRes.data.categories)
        setPaymentMethods(pmRes.data.payment_methods ?? pmRes.data ?? [])
      } catch {
        setCategories([])
        setPaymentMethods([])
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
      ) : categories.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted mb-3">
            <Layers className="h-6 w-6 text-muted-foreground" />
          </div>
          <p className="text-sm font-medium">No categories yet</p>
          <p className="text-xs text-muted-foreground mt-1 max-w-xs">
            Create spending categories to control how your AI agent handles purchases.
          </p>
          <Button
            onClick={openCreate}
            className="mt-4 bg-teal-600 hover:bg-teal-700 text-white gap-1.5"
            size="sm"
          >
            <Plus className="h-4 w-4" />
            Add Category
          </Button>
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
