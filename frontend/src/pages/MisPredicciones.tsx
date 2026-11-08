import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { PrediccionConPartido } from "../types";

export function MisPredicciones() {
  const [predicciones, setPredicciones] = useState<PrediccionConPartido[]>([]);
  const [cargando, setCargando] = useState(true);

  useEffect(() => {
    api
      .get<PrediccionConPartido[]>("/predicciones/mias")
      .then(setPredicciones)
      .finally(() => setCargando(false));
  }, []);

  if (cargando) return <p>Cargando...</p>;

  return (
    <div>
      <h1>Mis predicciones</h1>
      <table>
        <thead>
          <tr>
            <th>Partido</th>
            <th>Mi predicción</th>
            <th>Resultado</th>
            <th>Puntos</th>
          </tr>
        </thead>
        <tbody>
          {predicciones.map((p) => {
            const puntos =
              p.puntos_base !== null ? p.puntos_base + (p.bonus_anticipacion ?? 0) : null;
            return (
              <tr key={p.partido.id}>
                <td>
                  {p.partido.equipo_local.nombre} vs {p.partido.equipo_visitante.nombre}
                </td>
                <td>
                  {p.goles_local} - {p.goles_visitante}
                </td>
                <td>
                  {p.partido.goles_local !== null
                    ? `${p.partido.goles_local} - ${p.partido.goles_visitante}`
                    : "—"}
                </td>
                <td>{puntos !== null ? puntos : "Pendiente"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
