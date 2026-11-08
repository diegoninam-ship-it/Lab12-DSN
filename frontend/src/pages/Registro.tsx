import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";

export function Registro() {
  const { registro } = useAuth();
  const navegar = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [apodo, setApodo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await registro(email, password, apodo);
      navegar("/partidos", { replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError(typeof err.detail === "string" ? err.detail : "El correo o apodo ya está en uso");
      } else if (err instanceof ApiError && err.status === 422) {
        setError("Revisa los datos: contraseña ≥ 8 caracteres, apodo 3-20 [A-Za-z0-9_]");
      } else {
        setError("No se pudo completar el registro");
      }
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="tarjeta-centrada">
      <h1>Crear cuenta</h1>
      <form onSubmit={enviar}>
        <label>
          Correo
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Apodo
          <input
            value={apodo}
            onChange={(e) => setApodo(e.target.value)}
            minLength={3}
            maxLength={20}
            pattern="[A-Za-z0-9_]+"
            title="3-20 caracteres: letras, números o guión bajo"
            required
          />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={enviando}>
          Registrarme
        </button>
      </form>
      <p>
        ¿Ya tienes cuenta? <Link to="/login">Inicia sesión</Link>
      </p>
    </div>
  );
}
