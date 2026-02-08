import { createContext, useContext, useState, useEffect } from "react";
import userAPI from "../api/users"; // centralized auth API

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch current user on app load
  useEffect(() => {
    async function fetchUser() {
      try {
        const currentUser = await userAPI.getCurrentUser();
        setUser(currentUser);
        setError(null);
      } catch (err) {
        console.debug("User not authenticated:", err.message);
        setUser(null);
        setError(null);
      } finally {
        setLoading(false);
      }
    }

    fetchUser();
  }, []);

  // Login function
  const login = async (username, password) => {
    setLoading(true);
    try {
      await userAPI.login(username, password);
      const currentUser = await userAPI.getCurrentUser(); // fetch user after login
      setUser(currentUser);
      setError(null);
    } catch (err) {
      setUser(null);
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Register function - minimal flow: register then log the user in
  const register = async (username, password) => {
    setLoading(true);
    try {
      // create user
      await userAPI.register(username, password);

      // login to set HTTP-only cookie and load user
      await userAPI.login(username, password);
      const currentUser = await userAPI.getCurrentUser();
      setUser(currentUser);
      setError(null);
    } catch (err) {
      setUser(null);
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = async () => {
    setLoading(true);
    try {
      await userAPI.logout();
      setUser(null);
      setError(null);
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, error, login, logout, register }}>
      {children}
    </AuthContext.Provider>
  );
}

// Hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
