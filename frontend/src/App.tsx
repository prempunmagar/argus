import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { Toaster } from "@/components/ui/sonner"
import { AgentProvider } from "@/hooks/useAgent"
import { AppLayout } from "@/components/layout/AppLayout"
import { LoginPage } from "@/pages/LoginPage"
import { DashboardPage } from "@/pages/DashboardPage"
import { CategoriesPage } from "@/pages/CategoriesPage"
import { ApprovalsPage } from "@/pages/ApprovalsPage"
import { AgentKeysPage } from "@/pages/AgentKeysPage"
import { ProfilePage } from "@/pages/ProfilePage"
import { TransactionDetailPage } from "@/pages/TransactionDetailPage"

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("argus_token")
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          element={
            <ProtectedRoute>
              <AgentProvider>
                <AppLayout />
              </AgentProvider>
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<DashboardPage />} />
          <Route path="/categories" element={<CategoriesPage />} />
          <Route path="/approvals" element={<ApprovalsPage />} />
          <Route path="/agent-keys" element={<AgentKeysPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/transactions/:id" element={<TransactionDetailPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
    </BrowserRouter>
  )
}

export default App
