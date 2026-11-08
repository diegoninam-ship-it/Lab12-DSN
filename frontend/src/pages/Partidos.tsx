import { useEffect, useState } from "react";
import { api, ApiError } from "../api/client";
import type { EstadoPartido, Partido } from "../types";

const ESTADOS: { valor: EstadoPartido | ""; etiqueta: string }[] = [
  { valor: "", etiqueta: "Todos" },
  { valor: "PROGRAMADO", etiqueta: "Programados" },
  { valor: "EN_JUEGO", etiqueta: "En juego" },
  { valor: "FINALIZADO", etiqueta: "Finalizados" },
];

export function Partidos() {
  const [partidos, setPartidos] = useState<Partido[]>([]);
  const [filtro, setFiltro] = useState<EstadoPartido | "">("");
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    setCargando(true);
    setError(null);
    try {
      const ruta = filtro ? `/partidos?estado=${filtro}` : "/partidos";
      setPartidos(await api.get<Partido[]>(ruta));
    } catch {
      setError("No se pudieron cargar los partidos");
    } finally {
      setCargando(false);
    }
  }

  useEffect(() => {
    cargar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filtro]);

  return (
    <div>
      <h1>Partidos</h1>
      <div className="filtros">
        {ESTADOS.map((e) => (
          <button
            key={e.valor}
            className={filtro === e.valor ? "activo" : ""}
            onClick={() => setFiltro(e.valor)}
          >
            {e.etiqueta}
          </button>
        ))}
      </div>
      {error && <p className="error">{error}</p>}
      {cargando ? (
        <p>Cargando...</p>
      ) : (
        <ul className="lista-partidos">
          {partidos.map((p) => (
            <FilaPartido key={p.id} partido={p} onGuardado={cargar} />
          ))}
        </ul>
      )}
    </div>
  );
}

function formatearCuenta(ms: number): string {
  if (ms <= 0) return "¡ya empezó!";
  const segundos = Math.floor(ms / 1000);
  const dias = Math.floor(segundos / 86400);
  const horas = Math.floor((segundos % 86400) / 3600);
  const minutos = Math.floor((segundos % 3600) / 60);
  const seg = segundos % 60;
  if (dias > 0) return `${dias}d ${horas}h`;
  if (horas > 0) return `${horas}h ${minutos}m`;
  return `${minutos}m ${seg}s`;
}

function FilaPartido({ partido, onGuardado }: { partido: Partido; onGuardado: () => void }) {
  const [gl, setGl] = useState(partido.mi_prediccion?.goles_local ?? 0);
  const [gv, setGv] = useState(partido.mi_prediccion?.goles_visitante ?? 0);
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ahora, setAhora] = useState(Date.now());

  useEffect(() => {
    const id = setInterval(() => setAhora(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  const inicio = new Date(partido.inicio).getTime();
  const puedePredecir = partido.estado === "PROGRAMADO";
  const faltan = inicio - ahora;

  async function guardar() {
    setGuardando(true);
    setError(null);
    try {
      await api.put(`/partidos/${partido.id}/prediccion`, { goles_local: gl, goles_visitante: gv });
      onGuardado();
    } catch (err) {
      setError(
        err instanceof ApiError && typeof err.detail === "string"
          ? err.detail
          : "No se pudo guardar la predicción"
      );
    } finally {
      setGuardando(false);
    }
  }

  const puntosTotales =
    partido.mi_prediccion?.puntos_base !== null && partido.mi_prediccion?.puntos_base !== undefined
      ? partido.mi_prediccion.puntos_base + (partido.mi_prediccion.bonus_anticipacion ?? 0)
      : null;

  return (
    <li className="partido">
      <div className="equipos">
        <span>{partido.equipo_local.nombre}</span>
        <span className="vs">vs</span>
        <span>{partido.equipo_visitante.nombre}</span>
      </div>
      <div className="meta">
        <span>{partido.fase}</span>
        <span className={`estado estado-${partido.estado}`}>{partido.estado}</span>
        {partido.estado === "PROGRAMADO" && <span>Inicia en {formatearCuenta(faltan)}</span>}
      </div>
      {partido.estado === "FINALIZADO" && (
        <div className="resultado">
          Resultado: {partido.goles_local} - {partido.goles_visitante}
        </div>
      )}
      <div className="prediccion">
        <input
          type="number"
          min={0}
          max={20}
          value={gl}
          disabled={!puedePredecir}
          onChange={(e) => setGl(Number(e.target.value))}
        />
        <span>-</span>
        <input
          type="number"
          min={0}
          max={20}
          value={gv}
          disabled={!puedePredecir}
          onChange={(e) => setGv(Number(e.target.value))}
        />
        {puedePredecir && (
          <button onClick={guardar} disabled={guardando}>
            {partido.mi_prediccion ? "Editar" : "Predecir"}
          </button>
        )}
        {partido.mi_prediccion && (
          <span className="puntos">
            {puntosTotales !== null ? `Puntos: ${puntosTotales}` : "Pendiente de resultado"}
          </span>
        )}
      </div>
      {error && <p className="error">{error}</p>}
    </li>
  );
}
