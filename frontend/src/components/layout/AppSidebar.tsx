import { useLocation, useNavigate } from "react-router-dom"
import {
  LayoutDashboard,
  FolderKanban,
  ShieldCheck,
  KeyRound,
  UserCircle,
  LogOut,
  Eye,
} from "lucide-react"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { useAuth } from "@/hooks/useAuth"
import { AgentSwitcher } from "@/components/agents/AgentSwitcher"

const navItems = [
  { label: "Dashboard", icon: LayoutDashboard, path: "/" },
  { label: "Categories", icon: FolderKanban, path: "/categories" },
  { label: "Approvals", icon: ShieldCheck, path: "/approvals" },
  { label: "Agent Keys", icon: KeyRound, path: "/agent-keys" },
]

export function AppSidebar({ pendingCount = 0 }: { pendingCount?: number }) {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  return (
    <Sidebar>
      <SidebarHeader className="px-4 py-5">
        <div
          className="flex items-center gap-2 cursor-pointer"
          onClick={() => navigate("/")}
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-teal-600 text-white">
            <Eye className="h-4 w-4" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-sidebar-foreground">
              Argus
            </h1>
            <p className="text-[11px] text-sidebar-muted-foreground leading-none">
              AI Payment Authorization
            </p>
          </div>
        </div>
      </SidebarHeader>

      <AgentSwitcher />

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.path}>
                  <SidebarMenuButton
                    isActive={location.pathname === item.path}
                    onClick={() => navigate(item.path)}
                    className="gap-3"
                  >
                    <item.icon className="h-4 w-4" />
                    <span>{item.label}</span>
                    {item.label === "Approvals" && pendingCount > 0 && (
                      <span className="ml-auto flex h-5 min-w-5 items-center justify-center rounded-full bg-amber-500 px-1.5 text-[11px] font-medium text-white">
                        {pendingCount}
                      </span>
                    )}
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="px-4 py-3">
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate("/profile")}
            className="min-w-0 text-left hover:opacity-80 transition-opacity flex items-center gap-2"
          >
            <UserCircle className="h-5 w-5 shrink-0 text-sidebar-muted-foreground" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-sidebar-foreground">
                {user?.name ?? "User"}
              </p>
              <p className="truncate text-xs text-sidebar-muted-foreground">
                {user?.email ?? ""}
              </p>
            </div>
          </button>
          <button
            onClick={() => {
              logout()
              navigate("/login")
            }}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-sidebar-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-foreground transition-colors"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}
