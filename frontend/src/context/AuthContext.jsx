import { createContext, useContext, useState, useEffect, useCallback } from "react";
import { useNavigate, useLocation } from "react-router-dom";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("gv_token"));
  const [isLoggedIn, setIsLoggedIn] = useState(() => !!localStorage.getItem("gv_token"));

  const login = useCallback((newToken) => {
    localStorage.setItem("gv_token", newToken);
    setToken(newToken);
    setIsLoggedIn(true);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("gv_token");
    setToken(null);
    setIsLoggedIn(false);
  }, []);

  // Keep state in sync if localStorage changes in another tab
  useEffect(() => {
    const handleStorage = () => {
      const t = localStorage.getItem("gv_token");
      setToken(t);
      setIsLoggedIn(!!t);
    };
    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, []);

  return (
    <AuthContext.Provider value={{ token, isLoggedIn, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

/**
 * useRequireAuth — call this inside a component to get a guarded action wrapper.
 * Usage:
 *   const requireAuth = useRequireAuth();
 *   <button onClick={() => requireAuth(() => doSomething())}>Star</button>
 *
 * If not logged in, it redirects to /login with a `redirectTo` query param
 * so the user returns after logging in.
 */
export function useRequireAuth() {
  const { isLoggedIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  return useCallback((action) => {
    if (!isLoggedIn) {
      // Save where they came from so we can redirect back
      navigate(`/login?redirectTo=${encodeURIComponent(location.pathname)}`, {
        state: { message: "Please log in to perform this action." }
      });
      return;
    }
    if (typeof action === "function") action();
  }, [isLoggedIn, navigate, location.pathname]);
}
