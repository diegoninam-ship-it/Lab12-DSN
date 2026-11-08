import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { api, ApiError } from "../api/client";
import type { SalaDetalle } from "../types";
import { useAuth } from "../context/AuthContext";

export function SalaUnirsePorEnlace() {
  const { codigo } = useParams();
  const navegar = useNavigate();
  const { usuario, cargando } = useAuth();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cargando) return;
    if (!usuario) {
      navegar("/login", { state: { desde: `/salas/unirse/${codigo}` } });
      return;
    }
    api
      .post<SalaDetalle>("/salas/unirse", { codigo })
      .then((sala) => navegar(`/salas/${sala.id}`, { replace: true }))
      .catch((err) =>
        setError(
          err instanceof ApiError && typeof err.detail === "string" ? err.detail : "Código inválido"
        )
      );
  }, [cargando, usuario, codigo, navegar]);

  if (error) return <p className="error">{error}</p>;
  return <p>Uniéndote a la sala...</p>;
}
