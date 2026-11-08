import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "../api/client";
import type { Usuario } from "../types";

interface AuthContextValor {
  usuario: Usuario | null;
  cargando: boolean;
  login: (email: string, password: string) => Promise<void>;
  registro: (email: string, password: string, apodo: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValor | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    api
      .get<Usuario>("/auth/yo")
      .then(setUsuario)
      .catch(() => setUsuario(null))
      .finally(() => setCargando(false));
  }, []);

  async function login(email: string, password: string) {
    const nuevo = await api.post<Usuario>("/auth/login", { email, password });
    setUsuario(nuevo);
  }

  async function registro(email: string, password: string, apodo: string) {
    const nuevo = await api.post<Usuario>("/auth/registro", { email, password, apodo });
    setUsuario(nuevo);
  }

  async function logout() {
    await api.post("/auth/logout");
    setUsuario(null);
  }

  return (
    <AuthContext.Provider value={{ usuario, cargando, login, registro, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValor {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
