import { Navigate, Outlet, useLocation } from "react-router";
import { useAuth } from "../context/AuthContext";

export function RutaProtegida() {
  const { usuario, cargando } = useAuth();
  const location = useLocation();

  if (cargando) return <p className="cargando">Cargando...</p>;
  if (!usuario) {
    return <Navigate to="/login" state={{ desde: location.pathname }} replace />;
  }
  return <Outlet />;
}

export function RutaAdmin() {
  const { usuario, cargando } = useAuth();

  if (cargando) return <p className="cargando">Cargando...</p>;
  if (!usuario) return <Navigate to="/login" replace />;
  if (usuario.rol !== "ADMIN") return <Navigate to="/partidos" replace />;
  return <Outlet />;
}
