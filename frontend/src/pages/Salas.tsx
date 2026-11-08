import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router";
import { api, ApiError } from "../api/client";
import type { SalaItem } from "../types";

export function Salas() {
  const [salas, setSalas] = useState<SalaItem[]>([]);
  const [nombre, setNombre] = useState("");
  const [codigo, setCodigo] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function cargar() {
    setSalas(await api.get<SalaItem[]>("/salas"));
  }

  useEffect(() => {
    cargar();
  }, []);

  async function crear(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/salas", { nombre });
      setNombre("");
      cargar();
    } catch (err) {
      setError(
        err instanceof ApiError && typeof err.detail === "string"
          ? err.detail
          : "No se pudo crear la sala"
      );
    }
  }

  async function unirse(e: FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/salas/unirse", { codigo });
      setCodigo("");
      cargar();
    } catch (err) {
      setError(
        err instanceof ApiError && typeof err.detail === "string" ? err.detail : "Código inválido"
      );
    }
  }

  return (
    <div>
      <h1>Mis salas</h1>
      {error && <p className="error">{error}</p>}
      <ul className="lista-salas">
        {salas.map((s) => (
          <li key={s.id}>
            <Link to={`/salas/${s.id}`}>{s.nombre}</Link> {s.es_dueno && <span className="etiqueta">dueño</span>}
          </li>
        ))}
        {salas.length === 0 && <li>Todavía no perteneces a ninguna sala.</li>}
      </ul>
      <div className="formularios-sala">
        <form onSubmit={crear}>
          <h2>Crear sala</h2>
          <input
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
            placeholder="Nombre (3-50 caracteres)"
            minLength={3}
            maxLength={50}
            required
          />
          <button type="submit">Crear</button>
        </form>
        <form onSubmit={unirse}>
          <h2>Unirse con código</h2>
          <input
            value={codigo}
            onChange={(e) => setCodigo(e.target.value.toUpperCase())}
            placeholder="Código de invitación"
            required
          />
          <button type="submit">Unirse</button>
        </form>
      </div>
    </div>
  );
}
