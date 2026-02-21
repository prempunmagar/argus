import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react"
import { api } from "@/lib/api"
import { mockAgents } from "@/lib/mock-data"
import type { Agent } from "@/lib/types"

const USE_MOCK = !import.meta.env.VITE_API_URL
const STORAGE_KEY = "argus_current_agent"

interface AgentContextValue {
  agents: Agent[]
  currentAgent: Agent | null
  loading: boolean
  switchAgent: (agentId: string) => void
  createAgent: (name: string, description?: string) => void
}

const AgentContext = createContext<AgentContextValue | null>(null)

export function AgentProvider({ children }: { children: ReactNode }) {
  const [agents, setAgents] = useState<Agent[]>([])
  const [currentAgent, setCurrentAgent] = useState<Agent | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        let loaded: Agent[]
        if (USE_MOCK) {
          loaded = mockAgents
        } else {
          const { data } = await api.get("/agents")
          loaded = data.agents ?? data
        }
        setAgents(loaded)

        // Restore last-selected agent from localStorage, or pick first
        const savedId = localStorage.getItem(STORAGE_KEY)
        const saved = loaded.find((a) => a.id === savedId)
        setCurrentAgent(saved ?? loaded[0] ?? null)
      } catch {
        setAgents(mockAgents)
        setCurrentAgent(mockAgents[0] ?? null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const switchAgent = useCallback(
    (agentId: string) => {
      const agent = agents.find((a) => a.id === agentId)
      if (agent) {
        setCurrentAgent(agent)
        localStorage.setItem(STORAGE_KEY, agentId)
      }
    },
    [agents]
  )

  const createAgent = useCallback(
    (name: string, description?: string) => {
      if (USE_MOCK) {
        const newAgent: Agent = {
          id: `agent-${Date.now()}`,
          name,
          description: description ?? null,
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        setAgents((prev) => [...prev, newAgent])
        setCurrentAgent(newAgent)
        localStorage.setItem(STORAGE_KEY, newAgent.id)
      } else {
        api
          .post("/agents", { name, description })
          .then(({ data }) => {
            setAgents((prev) => [...prev, data])
            setCurrentAgent(data)
            localStorage.setItem(STORAGE_KEY, data.id)
          })
          .catch(() => {
            // fallback
          })
      }
    },
    []
  )

  return (
    <AgentContext.Provider
      value={{ agents, currentAgent, loading, switchAgent, createAgent }}
    >
      {children}
    </AgentContext.Provider>
  )
}

export function useAgent() {
  const ctx = useContext(AgentContext)
  if (!ctx) throw new Error("useAgent must be used within AgentProvider")
  return ctx
}
