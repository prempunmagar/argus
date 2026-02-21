import { useState, useEffect, type ChangeEvent } from "react"
import { Plus } from "lucide-react"
import { toast } from "sonner"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/hooks/useAuth"
import { PaymentMethodCard } from "@/components/payment-methods/PaymentMethodCard"
import {
  PaymentMethodFormDialog,
  type PaymentMethodFormData,
} from "@/components/payment-methods/PaymentMethodFormDialog"
import { api } from "@/lib/api"
import { mockPaymentMethods } from "@/lib/mock-data"
import type { PaymentMethod } from "@/lib/types"

const USE_MOCK = !import.meta.env.VITE_API_URL

export function ProfilePage() {
  const { user } = useAuth()

  const [name, setName] = useState(user?.name ?? "")
  const [email, setEmail] = useState(user?.email ?? "")
  const [currentPassword, setCurrentPassword] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [saving, setSaving] = useState(false)

  // Payment methods state
  const [methods, setMethods] = useState<PaymentMethod[]>([])
  const [methodsLoading, setMethodsLoading] = useState(true)
  const [pmDialogOpen, setPmDialogOpen] = useState(false)
  const [editingMethod, setEditingMethod] = useState<PaymentMethod | undefined>(
    undefined
  )

  useEffect(() => {
    async function loadMethods() {
      try {
        if (USE_MOCK) {
          setMethods(mockPaymentMethods)
        } else {
          const { data } = await api.get("/payment-methods")
          setMethods(data.payment_methods ?? data)
        }
      } catch {
        setMethods(mockPaymentMethods)
      } finally {
        setMethodsLoading(false)
      }
    }
    loadMethods()
  }, [])

  async function handleSaveProfile() {
    if (!name.trim()) return
    setSaving(true)
    try {
      const updatedUser = { ...user!, name: name.trim(), email: email.trim() }
      localStorage.setItem("argus_user", JSON.stringify(updatedUser))
      toast.success("Profile updated")
    } catch {
      toast.error("Failed to update profile")
    } finally {
      setSaving(false)
    }
  }

  function handleChangePassword() {
    if (!currentPassword || !newPassword) return
    if (newPassword !== confirmPassword) {
      toast.error("Passwords do not match")
      return
    }
    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters")
      return
    }
    setCurrentPassword("")
    setNewPassword("")
    setConfirmPassword("")
    toast.success("Password updated")
  }

  function openCreatePm() {
    setEditingMethod(undefined)
    setPmDialogOpen(true)
  }

  function openEditPm(method: PaymentMethod) {
    setEditingMethod(method)
    setPmDialogOpen(true)
  }

  async function handleSavePm(data: PaymentMethodFormData) {
    try {
      if (USE_MOCK) {
        if (editingMethod) {
          setMethods((prev) =>
            prev.map((m) => {
              if (m.id === editingMethod.id) {
                return {
                  ...m,
                  nickname: data.nickname,
                  method_type: data.method_type,
                  detail: data.detail,
                  is_default: data.is_default,
                }
              }
              if (data.is_default && m.is_default) {
                return { ...m, is_default: false }
              }
              return m
            })
          )
          toast.success("Payment method updated")
        } else {
          const newMethod: PaymentMethod = {
            id: `pm-${Date.now()}`,
            nickname: data.nickname,
            method_type: data.method_type,
            detail: data.detail,
            is_default: data.is_default,
            status: "ACTIVE",
          }
          if (data.is_default) {
            setMethods((prev) => [
              ...prev.map((m) => ({ ...m, is_default: false })),
              newMethod,
            ])
          } else {
            setMethods((prev) => [...prev, newMethod])
          }
          toast.success("Payment method added")
        }
      } else {
        if (editingMethod) {
          const { data: updated } = await api.put(
            `/payment-methods/${editingMethod.id}`,
            data
          )
          setMethods((prev) =>
            prev.map((m) => (m.id === editingMethod.id ? updated : m))
          )
          toast.success("Payment method updated")
        } else {
          const { data: created } = await api.post("/payment-methods", data)
          setMethods((prev) => [...prev, created])
          toast.success("Payment method added")
        }
      }
      setPmDialogOpen(false)
    } catch {
      toast.error("Failed to save payment method")
    }
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Profile</h1>
        <p className="text-sm text-muted-foreground">
          Manage your account settings
        </p>
      </div>

      <div className="space-y-6">
        {/* Account Information */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Account Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="profile-name">Name</Label>
              <Input
                id="profile-name"
                value={name}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setName(e.target.value)
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="profile-email">Email</Label>
              <Input
                id="profile-email"
                type="email"
                value={email}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setEmail(e.target.value)
                }
              />
            </div>

            <Button
              onClick={handleSaveProfile}
              disabled={!name.trim() || saving}
              className="bg-teal-600 hover:bg-teal-700 text-white"
            >
              {saving ? "Saving..." : "Save Changes"}
            </Button>
          </CardContent>
        </Card>

        {/* Payment Methods */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Payment Methods</CardTitle>
              <Button
                onClick={openCreatePm}
                size="sm"
                className="bg-teal-600 hover:bg-teal-700 text-white gap-1.5"
              >
                <Plus className="h-3.5 w-3.5" />
                Add Method
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              Cards, bank accounts, and wallets used for AI agent purchases
            </p>
          </CardHeader>
          <CardContent>
            {methodsLoading ? (
              <div className="space-y-3">
                <Skeleton className="h-16 rounded-lg" />
                <Skeleton className="h-16 rounded-lg" />
              </div>
            ) : methods.length === 0 ? (
              <p className="text-sm text-muted-foreground py-2">
                No payment methods yet. Add one to get started.
              </p>
            ) : (
              <div className="space-y-3">
                {methods.map((m) => (
                  <PaymentMethodCard key={m.id} method={m} onEdit={openEditPm} />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Change Password */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Change Password</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">Current Password</Label>
              <Input
                id="current-password"
                type="password"
                value={currentPassword}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setCurrentPassword(e.target.value)
                }
              />
            </div>

            <Separator />

            <div className="space-y-2">
              <Label htmlFor="new-password">New Password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setNewPassword(e.target.value)
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirm-password">Confirm New Password</Label>
              <Input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setConfirmPassword(e.target.value)
                }
              />
            </div>

            <Button
              onClick={handleChangePassword}
              disabled={!currentPassword || !newPassword || !confirmPassword}
              variant="outline"
            >
              Update Password
            </Button>
          </CardContent>
        </Card>
      </div>

      <PaymentMethodFormDialog
        open={pmDialogOpen}
        onOpenChange={setPmDialogOpen}
        method={editingMethod}
        onSave={handleSavePm}
      />
    </div>
  )
}
