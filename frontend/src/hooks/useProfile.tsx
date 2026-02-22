import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react"
import { api } from "@/lib/api"
import { mockProfiles } from "@/lib/mock-data"
import type { Profile } from "@/lib/types"

const USE_MOCK = !import.meta.env.VITE_API_URL
const STORAGE_KEY = "argus_current_profile"

interface ProfileContextValue {
  profiles: Profile[]
  currentProfile: Profile | null
  loading: boolean
  switchProfile: (profileId: string) => void
  createProfile: (name: string, description?: string) => void
}

const ProfileContext = createContext<ProfileContextValue | null>(null)

export function ProfileProvider({ children }: { children: ReactNode }) {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [currentProfile, setCurrentProfile] = useState<Profile | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        let loaded: Profile[]
        if (USE_MOCK) {
          loaded = mockProfiles
        } else {
          const { data } = await api.get("/profiles")
          loaded = data.profiles ?? data
        }
        setProfiles(loaded)

        const savedId = localStorage.getItem(STORAGE_KEY)
        const saved = loaded.find((p) => p.id === savedId)
        setCurrentProfile(saved ?? loaded[0] ?? null)
      } catch {
        setProfiles(mockProfiles)
        setCurrentProfile(mockProfiles[0] ?? null)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const switchProfile = useCallback(
    (profileId: string) => {
      const profile = profiles.find((p) => p.id === profileId)
      if (profile) {
        setCurrentProfile(profile)
        localStorage.setItem(STORAGE_KEY, profileId)
      }
    },
    [profiles]
  )

  const createProfile = useCallback(
    (name: string, description?: string) => {
      if (USE_MOCK) {
        const newProfile: Profile = {
          id: `profile-${Date.now()}`,
          name,
          description: description ?? undefined,
          is_active: true,
          created_at: new Date().toISOString(),
        }
        setProfiles((prev) => [...prev, newProfile])
        setCurrentProfile(newProfile)
        localStorage.setItem(STORAGE_KEY, newProfile.id)
      } else {
        api
          .post("/profiles", { name, description })
          .then(({ data }) => {
            setProfiles((prev) => [...prev, data])
            setCurrentProfile(data)
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
    <ProfileContext.Provider
      value={{ profiles, currentProfile, loading, switchProfile, createProfile }}
    >
      {children}
    </ProfileContext.Provider>
  )
}

export function useProfile() {
  const ctx = useContext(ProfileContext)
  if (!ctx) throw new Error("useProfile must be used within ProfileProvider")
  return ctx
}
