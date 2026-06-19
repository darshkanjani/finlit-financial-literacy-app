import { useState } from "react"
import { MessageSquareText, Sparkles } from "lucide-react"

import { Chat } from "@/pages/dashboard/chat"
import { Advice } from "@/pages/dashboard/advice"
import { Button } from "@/components/ui/button"

type AssistantMode = "chat" | "advice"

export function Assistant() {
  const [mode, setMode] = useState<AssistantMode>("chat")

  return (
    <div className="mx-auto w-full max-w-6xl space-y-6 px-6 py-6">
      <div className="rounded-2xl border bg-card p-5 shadow-sm">
        <h2 className="text-lg font-semibold">AI Assistant</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          One place for both conversational support and structured recommendations.
        </p>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-xl border bg-muted/20 p-3">
            <p className="flex items-center gap-2 text-sm font-semibold">
              <MessageSquareText className="h-4 w-4 text-emerald-600" />
              Chat Mode
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Best for back-and-forth questions, clarifications, and quick what-if checks.
            </p>
          </div>
          <div className="rounded-xl border bg-muted/20 p-3">
            <p className="flex items-center gap-2 text-sm font-semibold">
              <Sparkles className="h-4 w-4 text-emerald-600" />
              Advice Mode
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Best for a focused recommendation with action items and trackable guidance.
            </p>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <Button
            size="sm"
            variant={mode === "chat" ? "default" : "outline"}
            onClick={() => setMode("chat")}
          >
            Chat
          </Button>
          <Button
            size="sm"
            variant={mode === "advice" ? "default" : "outline"}
            onClick={() => setMode("advice")}
          >
            Advice
          </Button>
        </div>
      </div>

      {mode === "chat" ? <Chat embedded /> : <Advice embedded />}
    </div>
  )
}

export default Assistant
