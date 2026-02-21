import { useState, type FormEvent, type ChangeEvent } from "react"
import { Eye, EyeOff, ArrowLeft, Mail } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { useAuth } from "@/hooks/useAuth"

type Mode = "login" | "signup" | "forgot"

export function LoginForm({ onSuccess }: { onSuccess: () => void }) {
  const { login, register, loading, error } = useAuth()

  const [mode, setMode] = useState<Mode>("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [name, setName] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [localError, setLocalError] = useState<string | null>(null)
  const [resetSent, setResetSent] = useState(false)
  const [resetLoading, setResetLoading] = useState(false)

  const isSignup = mode === "signup"
  const isForgot = mode === "forgot"

  function goTo(m: Mode) {
    setMode(m)
    setLocalError(null)
    setResetSent(false)
    if (m === "login") {
      setName("")
      setConfirmPassword("")
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setLocalError(null)

    if (isSignup) {
      if (password !== confirmPassword) {
        setLocalError("Passwords do not match")
        return
      }
      if (password.length < 8) {
        setLocalError("Password must be at least 8 characters")
        return
      }
      const success = await register(name, email, password)
      if (success) onSuccess()
    } else {
      const success = await login(email, password)
      if (success) onSuccess()
    }
  }

  const handleResetSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return
    setResetLoading(true)
    setLocalError(null)
    // Simulate API call
    await new Promise((r) => setTimeout(r, 800))
    setResetLoading(false)
    setResetSent(true)
  }

  const displayError = localError || error

  // ---- Forgot password view ----
  if (isForgot) {
    if (resetSent) {
      return (
        <div className="space-y-4 text-center py-2">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-teal-50 mx-auto">
            <Mail className="h-6 w-6 text-teal-600" />
          </div>
          <div>
            <p className="text-sm font-medium">Check your email</p>
            <p className="text-xs text-muted-foreground mt-1">
              We sent a password reset link to{" "}
              <span className="font-medium text-foreground">{email}</span>
            </p>
          </div>
          <Button
            variant="outline"
            className="w-full"
            onClick={() => goTo("login")}
          >
            Back to sign in
          </Button>
        </div>
      )
    }

    return (
      <form onSubmit={handleResetSubmit} className="space-y-4">
        <button
          type="button"
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          onClick={() => goTo("login")}
        >
          <ArrowLeft className="h-3 w-3" />
          Back to sign in
        </button>

        <div>
          <p className="text-sm font-medium">Reset your password</p>
          <p className="text-xs text-muted-foreground mt-0.5">
            Enter your email and we'll send you a reset link.
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="reset-email">Email</Label>
          <Input
            id="reset-email"
            type="email"
            placeholder="demo@argus.dev"
            autoComplete="email"
            value={email}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
            required
          />
        </div>

        {localError && (
          <p className="text-sm text-red-600">{localError}</p>
        )}

        <Button
          type="submit"
          className="w-full bg-teal-600 hover:bg-teal-700 text-white"
          disabled={resetLoading || !email.trim()}
        >
          {resetLoading ? "Sending..." : "Send Reset Link"}
        </Button>
      </form>
    )
  }

  // ---- Login / Signup view ----
  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {isSignup && (
        <div className="space-y-2">
          <Label htmlFor="name">Name</Label>
          <Input
            id="name"
            placeholder="John Doe"
            autoComplete="name"
            value={name}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setName(e.target.value)}
            required
          />
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input
          id="email"
          type="email"
          placeholder="demo@argus.dev"
          autoComplete="email"
          value={email}
          onChange={(e: ChangeEvent<HTMLInputElement>) => setEmail(e.target.value)}
          required
        />
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="password">Password</Label>
          {!isSignup && (
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
              onClick={() => goTo("forgot")}
            >
              Forgot password?
            </button>
          )}
        </div>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? "text" : "password"}
            placeholder="••••••••"
            autoComplete={isSignup ? "new-password" : "current-password"}
            className="pr-9"
            value={password}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setPassword(e.target.value)}
            required
          />
          <button
            type="button"
            tabIndex={-1}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {isSignup && (
        <div className="space-y-2">
          <Label htmlFor="confirm-password">Confirm Password</Label>
          <Input
            id="confirm-password"
            type={showPassword ? "text" : "password"}
            placeholder="••••••••"
            autoComplete="new-password"
            value={confirmPassword}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setConfirmPassword(e.target.value)}
            required
          />
        </div>
      )}

      {displayError && (
        <p className="text-sm text-red-600">{displayError}</p>
      )}

      <Button
        type="submit"
        className="w-full bg-teal-600 hover:bg-teal-700 text-white"
        disabled={loading}
      >
        {loading
          ? isSignup ? "Creating account..." : "Signing in..."
          : isSignup ? "Create Account" : "Sign in"}
      </Button>

      <p className="text-center text-xs text-muted-foreground">
        {isSignup ? "Already have an account?" : "Don't have an account?"}{" "}
        <button
          type="button"
          className="text-teal-600 hover:text-teal-700 font-medium"
          onClick={() => goTo(isSignup ? "login" : "signup")}
        >
          {isSignup ? "Sign in" : "Sign up"}
        </button>
      </p>
    </form>
  )
}
