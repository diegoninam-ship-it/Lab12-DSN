import { useEffect, useState, type FormEvent } from "react";
import { api, ApiError } from "../api/client";
import type { Equipo, Fase, Partido } from "../types";

const FASES: Fase[] = ["GRUPOS", "OCTAVOS", "CUARTOS", "SEMIFINAL", "TERCER_PUESTO", "FINAL"];

export function AdminPartidos() {
  const [equipos, setEquipos] = useState<Equipo[]>([]);
  const [partidos, setPartidos] = useState<Partido[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [local, setLocal] = useState<number | "">("");
  const [visitante, setVisitante] = useState<number | "">("");
  const [inicio, setInicio] = useState("");
  const [fase, setFase] = useState<Fase>("GRUPOS");

  async function cargar() {
    const [e, p] = await Promise.all([api.get<Equipo[]>("/equipos"), api.get<Partido[]>("/partidos")]);
    setEquipos(e);
    setPartidos(p);
  }

  useEffect(() => {
    cargar();
  }, []);

  function detalleError(err: unknown, fallback: string): string {
    return err instanceof ApiError && typeof err.detail === "string" ? err.detail : fallback;
  }

  async function crear(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/admin/partidos", {
        equipo_local_id: Number(local),
        equipo_visitante_id: Number(visitante),
        inicio: new Date(inicio).toISOString(),
        fase,
      });
      setLocal("");
      setVisitante("");
      setInicio("");
      cargar();
    } catch (err) {
      setError(detalleError(err, "No se pudo crear el partido"));
    }
  }

  async function eliminar(id: number) {
    try {
      await api.delete(`/admin/partidos/${id}`);
      cargar();
    } catch (err) {
      setError(detalleError(err, "No se pudo eliminar el partido"));
    }
  }

  async function registrarResultado(id: number, gl: number, gv: number) {
    try {
      await api.put(`/admin/partidos/${id}/resultado`, { goles_local: gl, goles_visitante: gv });
      cargar();
    } catch (err) {
      setError(detalleError(err, "No se pudo registrar el resultado"));
    }
  }

  async function anularResultado(id: number) {
    try {
      await api.delete(`/admin/partidos/${id}/resultado`);
      cargar();
    } catch (err) {
      setError(detalleError(err, "No se pudo anular el resultado"));
    }
  }

  return (
    <div>
      <h1>Administración de partidos</h1>
      {error && <p className="error">{error}</p>}

      <form onSubmit={crear} className="form-admin-partido">
        <h2>Crear partido</h2>
        <select
          aria-label="Local"
          value={local}
          onChange={(e) => setLocal(Number(e.target.value))}
          required
        >
          <option value="">Local</option>
          {equipos.map((eq) => (
            <option key={eq.id} value={eq.id}>
              {eq.nombre}
            </option>
          ))}
        </select>
        <select
          aria-label="Visitante"
          value={visitante}
          onChange={(e) => setVisitante(Number(e.target.value))}
          required
        >
          <option value="">Visitante</option>
          {equipos.map((eq) => (
            <option key={eq.id} value={eq.id}>
              {eq.nombre}
            </option>
          ))}
        </select>
        <input
          aria-label="Inicio"
          type="datetime-local"
          value={inicio}
          onChange={(e) => setInicio(e.target.value)}
          required
        />
        <select
          aria-label="Fase"
          value={fase}
          onChange={(e) => setFase(e.target.value as Fase)}
        >
          {FASES.map((f) => (
            <option key={f} value={f}>
              {f}
            </option>
          ))}
        </select>
        <button type="submit">Crear</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>Partido</th>
            <th>Inicio</th>
            <th>Estado</th>
            <th>Resultado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {partidos.map((p) => (
            <FilaAdmin
              key={p.id}
              partido={p}
              onEliminar={eliminar}
              onResultado={registrarResultado}
              onAnular={anularResultado}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function FilaAdmin({
  partido,
  onEliminar,
  onResultado,
  onAnular,
}: {
  partido: Partido;
  onEliminar: (id: number) => void;
  onResultado: (id: number, gl: number, gv: number) => void;
  onAnular: (id: number) => void;
}) {
  const [gl, setGl] = useState(partido.goles_local ?? 0);
  const [gv, setGv] = useState(partido.goles_visitante ?? 0);

  return (
    <tr>
      <td>
        {partido.equipo_local.nombre} vs {partido.equipo_visitante.nombre}
      </td>
      <td>{new Date(partido.inicio).toLocaleString()}</td>
      <td>{partido.estado}</td>
      <td>
        {partido.estado !== "PROGRAMADO" ? (
          <>
            <input
              type="number"
              min={0}
              value={gl}
              onChange={(e) => setGl(Number(e.target.value))}
              style={{ width: 50 }}
            />
            -
            <input
              type="number"
              min={0}
              value={gv}
              onChange={(e) => setGv(Number(e.target.value))}
              style={{ width: 50 }}
            />
            <button onClick={() => onResultado(partido.id, gl, gv)}>Guardar</button>
            {partido.estado === "FINALIZADO" && (
              <button onClick={() => onAnular(partido.id)}>Anular</button>
            )}
          </>
        ) : (
          <span>—</span>
        )}
      </td>
      <td>{partido.estado === "PROGRAMADO" && <button onClick={() => onEliminar(partido.id)}>Eliminar</button>}</td>
    </tr>
  );
}
