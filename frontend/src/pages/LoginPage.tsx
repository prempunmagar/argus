import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader } from "@/components/ui/card"
import { LoginForm } from "@/components/auth/LoginForm"

export function LoginPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">
      <Card className="w-full max-w-sm">
        <CardHeader className="items-center justify-items-center pb-2">
          <img src="/logo.png" alt="Argus" className="h-11 w-11 rounded-xl object-contain" />
          <div className="text-center">
            <h1 className="text-xl font-semibold tracking-tight">Argus</h1>
            <p className="text-xs text-muted-foreground mt-0.5">
              AI Payment Authorization
            </p>
          </div>
        </CardHeader>
        <CardContent>
          <LoginForm onSuccess={() => navigate("/")} />
          <div className="mt-4 rounded-md bg-muted/60 px-3 py-2 text-center">
            <p className="text-[11px] text-muted-foreground">
              Demo account:{" "}
              <span className="font-mono font-medium text-foreground">demo@argus.dev</span>
              {" / "}
              <span className="font-mono font-medium text-foreground">argus2026</span>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
