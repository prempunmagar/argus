import { Outlet } from "react-router-dom"
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "./AppSidebar"

export function AppLayout({ pendingCount = 0 }: { pendingCount?: number }) {
  return (
    <SidebarProvider>
      <AppSidebar pendingCount={pendingCount} />
      <SidebarInset>
        <main className="flex-1 overflow-auto">
          <Outlet />
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
