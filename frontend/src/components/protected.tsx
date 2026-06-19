import { Navigate } from "react-router-dom"

interface ProtectedRouteProps {
  children: React.ReactNode
  isLoggedIn: boolean
}

export function ProtectedRoute({ children, isLoggedIn }: ProtectedRouteProps) {
  if (!isLoggedIn) {
    console.warn("tried to access protected route without authentication")
    return <Navigate to="/login" replace />;
  }

  return children;
}
