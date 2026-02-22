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
    } catch (err: any) {
      const msg = err?.response?.data?.detail?.message || err?.response?.data?.message || "Invalid email or password"
      setError(msg)
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
