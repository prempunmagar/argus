import { useNavigate } from "react-router-dom"
import { Eye } from "lucide-react"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { LoginForm } from "@/components/auth/LoginForm"

export function LoginPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center justify-items-center pb-2">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-600 text-white">
            <Eye className="h-5 w-5" />
          </div>
          <div className="text-center">
            <h1 className="text-xl font-semibold tracking-tight">Argus</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              AI Payment Authorization
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <LoginForm onSuccess={() => navigate("/")} />
          <p className="mt-4 text-center text-[11px] text-muted-foreground">
            Demo: demo@argus.dev / argus2026
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
