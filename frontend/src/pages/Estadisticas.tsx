import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { AnalisisIA, Config, EstadisticasMias } from "../types";

export function Estadisticas() {
  const [stats, setStats] = useState<EstadisticasMias | null>(null);
  const [iaDisponible, setIaDisponible] = useState(false);
  const [analisis, setAnalisis] = useState<AnalisisIA | null>(null);
  const [cargandoAnalisis, setCargandoAnalisis] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.get<EstadisticasMias>("/estadisticas/mias").then(setStats);
    api.get<Config>("/config").then((c) => setIaDisponible(c.ia_disponible));
  }, []);

  async function pedirAnalisis() {
    setCargandoAnalisis(true);
    setError(null);
    try {
      setAnalisis(await api.post<AnalisisIA>("/estadisticas/mias/analisis"));
    } catch (err) {
      setError(
        err instanceof ApiError && typeof err.detail === "string"
          ? err.detail
          : "No se pudo generar el análisis"
      );
    } finally {
      setCargandoAnalisis(false);
    }
  }

  if (!stats) return <p>Cargando...</p>;

  return (
    <div>
      <h1>Mis estadísticas</h1>
      <ul className="tarjetas-stats">
        <li>% de aciertos: {stats.porcentaje_aciertos}%</li>
        <li>Puntos totales: {stats.puntos_totales}</li>
        <li>Puntos base: {stats.puntos_base}</li>
        <li>Bonus anticipación: {stats.bonus_anticipacion}</li>
        <li>Bonus racha: {stats.bonus_racha}</li>
        <li>Marcadores exactos: {stats.exactos}</li>
        <li>Aciertos: {stats.aciertos}</li>
        <li>Racha actual: {stats.racha_actual}</li>
        <li>Mejor racha: {stats.mejor_racha}</li>
        <li>Promedio global: {stats.promedio_global_total}</li>
        <li>Diferencia con el promedio: {stats.diferencia_con_promedio}</li>
      </ul>

      {iaDisponible && (
        <div className="analisis-ia">
          <button onClick={pedirAnalisis} disabled={cargandoAnalisis}>
            {cargandoAnalisis ? "Generando..." : "Analizar con IA"}
          </button>
          {error && <p className="error">{error}</p>}
          {analisis && <p className="texto-analisis">{analisis.texto}</p>}
        </div>
      )}
    </div>
  );
}
