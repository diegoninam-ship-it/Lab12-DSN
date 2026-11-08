import { useEffect, useState } from "react";
import { Link, Outlet } from "react-router";
import { useAuth } from "../context/AuthContext";
import { suscribirseServidor, ultimoServidor } from "../api/client";

export function Layout() {
  const { usuario, logout } = useAuth();
  const [servidor, setServidor] = useState(ultimoServidor);

  useEffect(() => suscribirseServidor(setServidor), []);

  return (
    <div className="app-shell">
      <header className="barra">
        <nav>
          <Link to="/partidos">Partidos</Link>
          <Link to="/mis-predicciones">Mis predicciones</Link>
          <Link to="/ranking">Ranking</Link>
          <Link to="/salas">Salas</Link>
          <Link to="/estadisticas">Estadísticas</Link>
          {usuario?.rol === "ADMIN" && <Link to="/admin/partidos">Admin</Link>}
        </nav>
        <div className="usuario-actual">
          {usuario && <span>{usuario.apodo}</span>}
          {usuario && <button onClick={() => logout()}>Salir</button>}
        </div>
      </header>
      <main>
        <Outlet />
      </main>
      <footer>
        <small>Atendido por: {servidor ?? "—"}</small>
      </footer>
    </div>
  );
}
