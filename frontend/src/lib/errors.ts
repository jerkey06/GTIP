import { ApiError } from '../api/client'

/** Mensaje comprensible para el usuario según el código HTTP (UI §4.2). */
export function errorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) return 'Ha ocurrido un error inesperado.'
  switch (error.status) {
    case 0:
      return 'No se pudo conectar con el servidor.'
    case 400:
    case 422:
      return error.detail ?? 'La solicitud no es válida.'
    case 401:
      return 'Tu sesión ha caducado. Vuelve a iniciar sesión.'
    case 403:
      return 'No tienes permiso para realizar esta acción.'
    case 404:
      return error.detail ?? 'No encontrado.'
    case 409:
      return error.detail ?? 'Ya hay una ingesta pendiente o en ejecución para esta fuente.'
    case 429:
      return 'Demasiadas solicitudes. Espera un momento e inténtalo de nuevo.'
    default:
      return 'El servidor no pudo completar la solicitud. Los datos ya almacenados siguen disponibles.'
  }
}

export function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404
}
