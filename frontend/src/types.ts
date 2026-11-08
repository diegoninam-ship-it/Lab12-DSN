export type Rol = "USER" | "ADMIN";
export type EstadoPartido = "PROGRAMADO" | "EN_JUEGO" | "FINALIZADO";
export type Fase = "GRUPOS" | "OCTAVOS" | "CUARTOS" | "SEMIFINAL" | "TERCER_PUESTO" | "FINAL";

export interface Usuario {
  id: number;
  email: string;
  apodo: string;
  rol: Rol;
}

export interface Equipo {
  id: number;
  nombre: string;
  codigo: string;
}

export interface PrediccionPropia {
  goles_local: number;
  goles_visitante: number;
  registrado_en: string;
  puntos_base: number | null;
  bonus_anticipacion: number | null;
}

export interface Partido {
  id: number;
  equipo_local: Equipo;
  equipo_visitante: Equipo;
  inicio: string;
  fase: Fase;
  estado: EstadoPartido;
  goles_local: number | null;
  goles_visitante: number | null;
  mi_prediccion: PrediccionPropia | null;
}

export interface PrediccionConPartido {
  partido: Partido;
  goles_local: number;
  goles_visitante: number;
  registrado_en: string;
  puntos_base: number | null;
  bonus_anticipacion: number | null;
}

export interface ItemRanking {
  posicion: number;
  apodo: string;
  total: number;
  exactos: number;
  aciertos: number;
  racha_actual: number;
  mejor_racha: number;
}

export interface RankingSalida {
  pagina: number;
  tamano: number;
  total_usuarios: number;
  items: ItemRanking[];
}

export interface SalaItem {
  id: number;
  nombre: string;
  dueno_id: number;
  es_dueno: boolean;
  creada_en: string;
}

export interface MiembroSala {
  usuario_id: number;
  apodo: string;
  unido_en: string;
  es_dueno: boolean;
}

export interface SalaDetalle extends SalaItem {
  codigo_invitacion: string;
  miembros: MiembroSala[];
}

export interface SalaRanking {
  sala_id: number;
  items: ItemRanking[];
}

export interface EstadisticasMias {
  predicciones_con_resultado: number;
  porcentaje_aciertos: number;
  puntos_totales: number;
  puntos_base: number;
  bonus_anticipacion: number;
  bonus_racha: number;
  exactos: number;
  aciertos: number;
  racha_actual: number;
  mejor_racha: number;
  promedio_global_total: number;
  diferencia_con_promedio: number;
}

export interface EstadisticasSala {
  sala_id: number;
  miembros: number;
  promedio_total: number;
  maximo_total: number;
  minimo_total: number;
  mejor_racha_sala: number;
}

export interface AnalisisIA {
  texto: string;
  generado_en: string;
  version_datos: string;
}

export interface Config {
  ia_disponible: boolean;
}
