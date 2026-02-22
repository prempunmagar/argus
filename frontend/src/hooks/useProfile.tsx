import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react"
import { api } from "@/lib/api"
import type { Profile } from "@/lib/types"

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
        const { data } = await api.get("/profiles")
        const loaded: Profile[] = data.profiles ?? data
        setProfiles(loaded)

        const savedId = localStorage.getItem(STORAGE_KEY)
        const saved = loaded.find((p) => p.id === savedId)
        setCurrentProfile(saved ?? loaded[0] ?? null)
      } catch {
        setProfiles([])
        setCurrentProfile(null)
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
      api
        .post("/profiles", { name, description })
        .then(({ data }) => {
          setProfiles((prev) => [...prev, data])
          setCurrentProfile(data)
          localStorage.setItem(STORAGE_KEY, data.id)
        })
        .catch(() => {
          // handle error
        })
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
