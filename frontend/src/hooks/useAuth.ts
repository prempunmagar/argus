import { useState, useCallback } from "react"
import { api } from "@/lib/api"
import type { User, AuthResponse } from "@/lib/types"

function getStoredUser(): User | null {
  const raw = localStorage.getItem("argus_user")
  if (!raw) return null
  try {
    return JSON.parse(raw) as User
  } catch {
    return null
  }
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(getStoredUser)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const token = localStorage.getItem("argus_token")
  const isAuthenticated = !!token && !!user

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post<AuthResponse>("/auth/login", { email, password })
      localStorage.setItem("argus_token", data.token)
      localStorage.setItem("argus_user", JSON.stringify(data.user))
      setUser(data.user)
      return true
    } catch {
      // Mock auth fallback when backend isn't running
      if (email === "demo@argus.dev" && password === "argus2026") {
        const mockUser: User = {
          id: "usr_demo_001",
          email: "demo@argus.dev",
          name: "Demo User",
          created_at: "2026-02-20T10:00:00Z",
        }
        localStorage.setItem("argus_token", "mock_jwt_token")
        localStorage.setItem("argus_user", JSON.stringify(mockUser))
        setUser(mockUser)
        return true
      }
      setError("Invalid email or password")
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const register = useCallback(async (name: string, email: string, password: string) => {
    setLoading(true)
    setError(null)
    try {
      const { data } = await api.post<AuthResponse>("/auth/register", { name, email, password })
      localStorage.setItem("argus_token", data.token)
      localStorage.setItem("argus_user", JSON.stringify(data.user))
      setUser(data.user)
      return true
    } catch (err: any) {
      // Mock register fallback when backend isn't running
      if (!import.meta.env.VITE_API_URL) {
        const mockUser: User = {
          id: `usr_${Date.now()}`,
          email,
          name,
          created_at: new Date().toISOString(),
        }
        localStorage.setItem("argus_token", "mock_jwt_token")
        localStorage.setItem("argus_user", JSON.stringify(mockUser))
        setUser(mockUser)
        return true
      }
      const msg = err?.response?.data?.message
      setError(msg || "Failed to create account")
      return false
    } finally {
      setLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem("argus_token")
    localStorage.removeItem("argus_user")
    setUser(null)
  }, [])

  return { user, isAuthenticated, loading, error, login, register, logout }
}
