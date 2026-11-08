import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router";
import { ApiError } from "../api/client";
import { useAuth } from "../context/AuthContext";

export function Login() {
  const { login } = useAuth();
  const navegar = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await login(email, password);
      const destino = (location.state as { desde?: string } | null)?.desde ?? "/partidos";
      navegar(destino, { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? "Credenciales inválidas" : "No se pudo iniciar sesión");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <div className="tarjeta-centrada">
      <h1>Iniciar sesión</h1>
      <form onSubmit={enviar}>
        <label>
          Correo
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={enviando}>
          Entrar
        </button>
      </form>
      <p>
        ¿No tienes cuenta? <Link to="/registro">Regístrate</Link>
      </p>
    </div>
  );
}
