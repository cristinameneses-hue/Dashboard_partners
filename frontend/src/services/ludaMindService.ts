/**
 * Servicio para comunicación con el backend Flask de Luda Mind
 */

import type {
  LudaMindResponse,
  LudaMindMode,
  LudaMindHealthResponse
} from '../types/ludaMind';

const LUDA_MIND_BASE_URL = '/luda-api';

export const ludaMindService = {
  /**
   * Envía una query al sistema Luda Mind
   */
  async sendQuery(
    query: string,
    mode: LudaMindMode,
    sessionId: string
  ): Promise<LudaMindResponse> {
    const response = await fetch(`${LUDA_MIND_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query,
        mode,
        session_id: sessionId,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Error desconocido' }));
      throw new Error(error.message || `Error ${response.status}`);
    }

    return response.json();
  },

  /**
   * Cambia el modo de la sesión actual
   */
  async setMode(sessionId: string, mode: LudaMindMode): Promise<void> {
    const response = await fetch(`${LUDA_MIND_BASE_URL}/session/mode`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        mode,
      }),
    });

    if (!response.ok) {
      console.warn('Error al cambiar modo en backend:', response.status);
    }
  },

  /**
   * Verifica el estado del backend Luda Mind
   */
  async healthCheck(): Promise<LudaMindHealthResponse> {
    const response = await fetch('/luda-health', {
      method: 'GET',
    });

    if (!response.ok) {
      throw new Error('Luda Mind no disponible');
    }

    return response.json();
  },
};
