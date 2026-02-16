// src/components/Navbar.jsx
import { Link } from "react-router-dom"
import { useAuth } from "../context/AuthContext"
import logo from "../assets/FBReflectLogo.png"  // <-- import image

export default function Navbar() {
  const { user, logout } = useAuth()

  const handleLogout = async () => {
    try {
      await logout()
    } catch (err) {
      console.error(err)
    }
  }

  return (
    <nav className="bg-gray-800 text-white px-6 py-4 flex justify-between items-center">
      <Link to="/" className="font-bold text-xl flex items-center">
        <img src={logo} alt="FBReflect Logo" className="h-8 inline-block mr-2" />
        FBReflect
      </Link>
      <div className="space-x-4">
        {user ? (
          <>
            <span>Welcome, {user.username}</span>
            <button
              onClick={handleLogout}
              className="bg-red-600 px-3 py-1 rounded hover:bg-red-700"
            >
              Logout
            </button>
          </>
        ) : (
          <>
            <Link to="/login" className="hover:underline">
              Login
            </Link>
            <Link to="/register" className="hover:underline">
              Register
            </Link>
          </>
        )}
      </div>
    </nav>
  )
}
