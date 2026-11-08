import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { RankingSalida } from "../types";

const TAMANO = 10;

export function Ranking() {
  const [pagina, setPagina] = useState(1);
  const [ranking, setRanking] = useState<RankingSalida | null>(null);

  useEffect(() => {
    api.get<RankingSalida>(`/ranking?pagina=${pagina}&tamano=${TAMANO}`).then(setRanking);
  }, [pagina]);

  if (!ranking) return <p>Cargando...</p>;

  const totalPaginas = Math.max(1, Math.ceil(ranking.total_usuarios / ranking.tamano));

  return (
    <div>
      <h1>Ranking global</h1>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Apodo</th>
            <th>Total</th>
            <th>Exactos</th>
            <th>Aciertos</th>
            <th>Racha</th>
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
              <td>
                {i.racha_actual} (mejor {i.mejor_racha})
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="paginacion">
        <button disabled={pagina <= 1} onClick={() => setPagina((p) => p - 1)}>
          Anterior
        </button>
        <span>
          Página {pagina} de {totalPaginas}
        </span>
        <button disabled={pagina >= totalPaginas} onClick={() => setPagina((p) => p + 1)}>
          Siguiente
        </button>
      </div>
    </div>
  );
}
