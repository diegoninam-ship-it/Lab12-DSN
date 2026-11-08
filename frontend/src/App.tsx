import { BrowserRouter, Navigate, Route, Routes } from "react-router";
import { AuthProvider } from "./context/AuthContext";
import { Layout } from "./components/Layout";
import { RutaAdmin, RutaProtegida } from "./components/Rutas";
import { Login } from "./pages/Login";
import { Registro } from "./pages/Registro";
import { Partidos } from "./pages/Partidos";
import { MisPredicciones } from "./pages/MisPredicciones";
import { Ranking } from "./pages/Ranking";
import { Salas } from "./pages/Salas";
import { SalaDetallePagina } from "./pages/SalaDetalle";
import { SalaUnirsePorEnlace } from "./pages/SalaUnirse";
import { Estadisticas } from "./pages/Estadisticas";
import { AdminPartidos } from "./pages/AdminPartidos";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/registro" element={<Registro />} />
          <Route path="/salas/unirse/:codigo" element={<SalaUnirsePorEnlace />} />

          <Route element={<RutaProtegida />}>
            <Route element={<Layout />}>
              <Route path="/" element={<Navigate to="/partidos" replace />} />
              <Route path="/partidos" element={<Partidos />} />
              <Route path="/mis-predicciones" element={<MisPredicciones />} />
              <Route path="/ranking" element={<Ranking />} />
              <Route path="/salas" element={<Salas />} />
              <Route path="/salas/:id" element={<SalaDetallePagina />} />
              <Route path="/estadisticas" element={<Estadisticas />} />
              <Route element={<RutaAdmin />}>
                <Route path="/admin/partidos" element={<AdminPartidos />} />
              </Route>
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/partidos" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
