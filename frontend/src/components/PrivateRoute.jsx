// src/components/PrivateRoute.jsx
import { Navigate } from "react-router-dom"
import { useAuth } from "../context/AuthContext"

const PrivateRoute = ({ children }) => {
  const { user, loading } = useAuth()

  if (loading) {
    // While checking auth status, show nothing or a loader
    return <div>Loading...</div>
  }

  // If user is not logged in, redirect to login
  if (!user) {
    return <Navigate to="/login" replace />
  }

  // User is logged in, render the protected component
  return children
}

export default PrivateRoute
