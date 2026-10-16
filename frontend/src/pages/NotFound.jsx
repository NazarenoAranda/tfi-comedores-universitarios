import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <section>
      <h1>Página no encontrada</h1>
      <p>
        La dirección que buscás no existe. <Link to="/">Volver al inicio</Link>
      </p>
    </section>
  );
}
