import { useEffect, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { mensajeDeError } from "../api/errores.js";
import { useAuth } from "../auth/AuthContext.jsx";
import Mensaje from "../components/Mensaje.jsx";

export default function Login() {
  const { usuario, cargando, login } = useAuth();
  const navegar = useNavigate();
  const ubicacion = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [lento, setLento] = useState(false);
  const [error, setError] = useState("");

  // El servidor gratuito puede estar "dormido": si tarda, se avisa para que no parezca trabado.
  useEffect(() => {
    if (!enviando) {
      setLento(false);
      return undefined;
    }
    const temporizador = setTimeout(() => setLento(true), 4000);
    return () => clearTimeout(temporizador);
  }, [enviando]);

  if (cargando) return <p className="cargando">Verificando sesión…</p>;
  if (usuario) return <Navigate to={ubicacion.state?.desde || "/"} replace />;

  async function enviar(evento) {
    evento.preventDefault();
    setError("");
    setEnviando(true);
    try {
      await login(email.trim(), password);
      navegar(ubicacion.state?.desde || "/", { replace: true });
    } catch (e) {
      setError(
        e.status === 400 ? "Email o contraseña incorrectos." : mensajeDeError(e)
      );
      setEnviando(false);
    }
  }

  return (
    <div className="login-pagina">
      <form className="login-caja" onSubmit={enviar}>
        <h1>Iniciar sesión</h1>
        <p className="detalle">Sistema de gestión de caja y proveedores · Comedores Universitarios</p>

        <Mensaje tipo="error">{error}</Mensaje>

        <label className="campo">
          <span>Email</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required autoFocus />
        </label>
        <label className="campo">
          <span>Contraseña</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
        </label>

        <button type="submit" className="btn btn-primario btn-ancho" disabled={enviando}>
          {enviando ? "Ingresando…" : "Ingresar"}
        </button>
        {lento && (
          <Mensaje tipo="info">
            Conectando con el servidor. La primera vez del día puede tardar hasta un minuto: no cierres la página.
          </Mensaje>
        )}
      </form>
    </div>
  );
}
