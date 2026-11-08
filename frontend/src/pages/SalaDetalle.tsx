import { useCallback, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router";
import { api, ApiError } from "../api/client";
import type { SalaDetalle as SalaDetalleType, SalaRanking } from "../types";

export function SalaDetallePagina() {
  const { id } = useParams();
  const navegar = useNavigate();
  const [sala, setSala] = useState<SalaDetalleType | null>(null);
  const [ranking, setRanking] = useState<SalaRanking | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async () => {
    try {
      const [s, r] = await Promise.all([
        api.get<SalaDetalleType>(`/salas/${id}`),
        api.get<SalaRanking>(`/salas/${id}/ranking`),
      ]);
      setSala(s);
      setRanking(r);
    } catch (err) {
      setError(
        err instanceof ApiError && typeof err.detail === "string"
          ? err.detail
          : "No se pudo cargar la sala"
      );
    }
  }, [id]);

  useEffect(() => {
    cargar();
  }, [cargar]);

  async function regenerarCodigo() {
    await api.post(`/salas/${id}/codigo`);
    cargar();
  }

  async function expulsar(usuarioId: number) {
    await api.delete(`/salas/${id}/miembros/${usuarioId}`);
    cargar();
  }

  async function salir() {
    await api.post(`/salas/${id}/salir`);
    navegar("/salas");
  }

  async function eliminar() {
    await api.delete(`/salas/${id}`);
    navegar("/salas");
  }

  if (error) return <p className="error">{error}</p>;
  if (!sala || !ranking) return <p>Cargando...</p>;

  return (
    <div>
      <h1>{sala.nombre}</h1>
      <p>
        Código de invitación: <strong>{sala.codigo_invitacion}</strong>
      </p>
      {sala.es_dueno && <button onClick={regenerarCodigo}>Regenerar código</button>}

      <h2>Miembros</h2>
      <ul>
        {sala.miembros.map((m) => (
          <li key={m.usuario_id}>
            {m.apodo} {m.es_dueno && "(dueño)"}
            {sala.es_dueno && !m.es_dueno && (
              <button onClick={() => expulsar(m.usuario_id)}>Expulsar</button>
            )}
          </li>
        ))}
      </ul>

      <h2>Ranking de la sala</h2>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Apodo</th>
            <th>Total</th>
            <th>Exactos</th>
            <th>Aciertos</th>
          </tr>
        </thead>
        <tbody>
          {ranking.items.map((i) => (
            <tr key={i.apodo}>
              <td>{i.posicion}</td>
              <td>{i.apodo}</td>
              <td>{i.total}</td>
              <td>{i.exactos}</td>
              <td>{i.aciertos}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="acciones-sala">
        {!sala.es_dueno && <button onClick={salir}>Salir de la sala</button>}
        {sala.es_dueno && (
          <button className="peligro" onClick={eliminar}>
            Eliminar sala
          </button>
        )}
      </div>
    </div>
  );
}
