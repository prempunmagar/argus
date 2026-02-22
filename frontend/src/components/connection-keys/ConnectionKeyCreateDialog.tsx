import { useState, useEffect, type ChangeEvent } from "react"
import { Copy, Check } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

interface Props {
  open: boolean
  onOpenChange: (open: boolean) => void
  onGenerate: (label: string) => string // returns the full key_value
}

export function ConnectionKeyCreateDialog({ open, onOpenChange, onGenerate }: Props) {
  const [label, setLabel] = useState("")
  const [generatedKey, setGeneratedKey] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (open) {
      setLabel("")
      setGeneratedKey(null)
      setCopied(false)
    }
  }, [open])

  function handleGenerate() {
    if (!label.trim()) return
    const key = onGenerate(label.trim())
    setGeneratedKey(key)
  }

  async function handleCopy() {
    if (!generatedKey) return
    await navigator.clipboard.writeText(generatedKey)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Generate Connection Key</DialogTitle>
          <DialogDescription>
            Create a new connection key for an AI shopping agent.
          </DialogDescription>
        </DialogHeader>

        {!generatedKey ? (
          <>
            <div className="space-y-2 py-1">
              <Label htmlFor="ck-label">Label</Label>
              <Input
                id="ck-label"
                placeholder="e.g., My Shopping Agent"
                value={label}
                onChange={(e: ChangeEvent<HTMLInputElement>) => setLabel(e.target.value)}
              />
            </div>

            <DialogFooter className="pt-2">
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleGenerate}
                disabled={!label.trim()}
                className="bg-teal-600 hover:bg-teal-700 text-white"
              >
                Generate Key
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <div className="space-y-3 py-1">
              <div className="rounded-lg border bg-slate-50 p-3">
                <code className="text-sm font-mono break-all select-all">
                  {generatedKey}
                </code>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="gap-1.5"
                onClick={handleCopy}
              >
                {copied ? (
                  <>
                    <Check className="h-3.5 w-3.5" />
                    Copied
                  </>
                ) : (
                  <>
                    <Copy className="h-3.5 w-3.5" />
                    Copy to clipboard
                  </>
                )}
              </Button>
              <p className="text-xs text-amber-600 font-medium">
                Save this key now. It will not be shown again.
              </p>
            </div>

            <DialogFooter className="pt-2">
              <Button
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Close
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
