import { useMemo, useState, type ReactNode } from "react"
import { useNavigate } from "react-router-dom"
import {
  Bot,
  LayoutDashboard,
  UserCircle,
  LogOut,
  Target,
  ShieldAlert,
} from "lucide-react"

import { api } from "@/components/api"
import { Button } from "@/components/ui/button"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
} from "@/components/ui/sidebar"
import { Assistant } from "@/pages/dashboard/assistant"
import { Goals } from "@/pages/dashboard/goals"
import { StressTest, SCENARIOS } from "@/pages/dashboard/stress"
import { Summary } from "@/pages/dashboard/summary"
import { Onboarding } from "@/pages/onboarding/onboarding"

type Tab = "summary" | "assistant" | "goals" | "stress" | "profile"

interface DashboardProps {
  setLoggedInState: (value: boolean) => void
}

const NAV_ITEMS: { id: Tab; label: string; icon: ReactNode; description: string }[] = [
  {
    id: "summary",
    label: "Summary",
    icon: <LayoutDashboard className="h-4 w-4" />,
    description: "Your financial snapshot",
  },
  {
    id: "goals",
    label: "Goals",
    icon: <Target className="h-4 w-4" />,
    description: "Track milestones",
  },
  {
    id: "assistant",
    label: "Assistant",
    icon: <Bot className="h-4 w-4" />,
    description: "Chat and structured advice",
  },
  {
    id: "stress",
    label: "Stress Tests",
    icon: <ShieldAlert className="h-4 w-4" />,
    description: "Run scenarios",
  },
  {
    id: "profile",
    label: "Profile",
    icon: <UserCircle className="h-4 w-4" />,
    description: "Income and expenses",
  },
]

export function Dashboard({ setLoggedInState }: DashboardProps) {
  const [activeTab, setActiveTab] = useState<Tab>("summary")
  const navigate = useNavigate()

  const todayLabel = useMemo(
    () =>
      new Date().toLocaleDateString(undefined, {
        weekday: "long",
        month: "long",
        day: "numeric",
      }),
    []
  )

  const activeNav = NAV_ITEMS.find((item) => item.id === activeTab)

  const handleLogout = () => {
    api
      .post({}, "/api/v1/auth/logout")
      .json(() => {
        setLoggedInState(false)
        navigate("/login", { replace: true })
      })
      .catch((error) => console.error(error))
  }

  const updateProfile = () => {
    SCENARIOS.map((scenario) => {
    api
      .post({ scenario_type: scenario.id }, "/api/v1/stress-test/run")
      .error(400, () => console.log("Complete your financial profile before running stress tests."))
      .json((result) => {
        console.log(result)
      })
      .catch(() => console.log("Failed to run scenario. Please try again."))

      return null;
    })
  }

  return (
    <div className="flex h-screen overflow-hidden bg-transparent">
      <SidebarProvider>
        <Sidebar className="border-r border-sidebar-border/80">
          <SidebarHeader className="border-b border-sidebar-border/80 p-4">
            <div className="rounded-xl bg-gradient-to-br from-emerald-700 via-emerald-600 to-lime-500 px-3 py-3 text-emerald-50 shadow">
              <p className="text-[11px] uppercase tracking-[0.16em] text-emerald-100/90">FinLit</p>
              <p className="mt-1 text-sm font-semibold">Money clarity hub</p>
            </div>
          </SidebarHeader>

          <SidebarContent className="px-2 py-3">
            <SidebarGroup>
              <SidebarMenu>
                {NAV_ITEMS.map((item) => (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      onClick={() => setActiveTab(item.id)}
                      isActive={activeTab === item.id}
                      className="h-auto rounded-xl px-3 py-2.5 data-[active=true]:bg-gradient-to-r data-[active=true]:from-emerald-600 data-[active=true]:to-emerald-500 data-[active=true]:text-white data-[active=true]:shadow-md"
                    >
                      {item.icon}
                      <span className="flex flex-col text-left leading-tight">
                        <span className="text-sm">{item.label}</span>
                        <span className="text-[11px] opacity-70">{item.description}</span>
                      </span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter className="border-t border-sidebar-border/80 p-3">
            <Button
              variant="ghost"
              type="button"
              onClick={handleLogout}
              className="w-full justify-start gap-2 rounded-lg text-muted-foreground hover:text-foreground"
            >
              <LogOut className="h-4 w-4" />
              Log out
            </Button>
          </SidebarFooter>
        </Sidebar>

        <main className="flex-1 overflow-auto">
          <header className="sticky top-0 z-20 border-b bg-background/80 px-6 py-4 backdrop-blur">
            <p className="text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">Dashboard</p>
            <div className="mt-1 flex items-center justify-between gap-4">
              <div>
                <h1 className="text-xl font-semibold">{activeNav?.label ?? "Overview"}</h1>
                <p className="text-sm text-muted-foreground">{activeNav?.description}</p>
              </div>
              <p className="rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground">{todayLabel}</p>
            </div>
          </header>

          {activeTab === "summary" && (
            <Summary
              onGoToProfile={() => setActiveTab("profile")}
              onGoToAdvice={() => setActiveTab("assistant")}
              onGoToStress={() => setActiveTab("stress")}
            />
          )}
          {activeTab === "assistant" && <Assistant />}
          {activeTab === "goals" && <Goals />}
          {activeTab === "stress" && <StressTest />}
          {activeTab === "profile" && (
            <div className="mx-auto w-full max-w-4xl px-6 py-6">
              <div className="mb-6 rounded-2xl border bg-card px-5 py-4 shadow-sm">
                <h2 className="text-lg font-semibold">Your Financial Profile</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Keep this updated to improve spending insights, stress testing, and AI recommendations.
                </p>
              </div>
              <Onboarding setLoggedInState={setLoggedInState} onSaved={updateProfile} />
            </div>
          )}
        </main>
      </SidebarProvider>
    </div>
  )
}

export default Dashboard
