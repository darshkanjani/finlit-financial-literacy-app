import { Link } from "react-router-dom"
import { Button } from "@/components/ui/button"

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-6">

        {/* Brand */}
        <Link to="/" className="font-bold text-lg tracking-tight shrink-0">
          FinLit
        </Link>

        {/* Nav links */}
        <nav className="hidden sm:flex items-center gap-1">
          <Link
            to="/"
            className="px-3 py-1.5 text-sm text-muted-foreground rounded-md hover:text-foreground hover:bg-muted transition-colors"
          >
            Home
          </Link>
          <Link
            to="/faq"
            className="px-3 py-1.5 text-sm text-muted-foreground rounded-md hover:text-foreground hover:bg-muted transition-colors"
          >
            FAQ
          </Link>
          <Link
            to="/legal"
            className="px-3 py-1.5 text-sm text-muted-foreground rounded-md hover:text-foreground hover:bg-muted transition-colors"
          >
            Legal
          </Link>
        </nav>

        {/* Auth buttons */}
        <div className="flex items-center gap-2 shrink-0">
          <Link to="/login">
            <Button variant="ghost" size="sm">Log in</Button>
          </Link>
          <Link to="/signup">
            <Button size="sm">Sign up</Button>
          </Link>
        </div>

      </div>
    </header>
  )
}

export default Navbar
