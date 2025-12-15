/**
 * Hook personalizado para gestionar el estado de Luda Mind
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { ludaMindService } from '../services/ludaMindService';
import type {
  LudaMindMode,
  LudaMindMessage,
  HistoryEntry,
} from '../types/ludaMind';
import { STORAGE_KEY, MAX_HISTORY_ITEMS } from '../types/ludaMind';

// Genera un ID de sesión único
const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

// Genera un ID único para mensajes
const generateMessageId = (): string => {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};

export function useLudaMind() {
  // Estado principal
  const [messages, setMessages] = useState<LudaMindMessage[]>([]);
  const [mode, setMode] = useState<LudaMindMode>('conversational');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [isConnected, setIsConnected] = useState<boolean | null>(null);

  // Ref para el sessionId (persiste entre renders)
  const sessionIdRef = useRef<string>(generateSessionId());

  // Cargar historial del localStorage al montar
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as HistoryEntry[];
        setHistory(parsed);
      }
    } catch (e) {
      console.warn('Error cargando historial:', e);
    }
  }, []);

  // Verificar conexión al montar
  useEffect(() => {
    const checkConnection = async () => {
      try {
        await ludaMindService.healthCheck();
        setIsConnected(true);
      } catch {
        setIsConnected(false);
      }
    };
    checkConnection();
  }, []);

  // Agregar mensaje de bienvenida al montar
  useEffect(() => {
    const welcomeMessage: LudaMindMessage = {
      id: generateMessageId(),
      type: 'system',
      content: `¡Hola! Soy **Luda Mind**, tu asistente inteligente de datos farmacéuticos.

Puedo ayudarte con:
- **Farmacias**: Información y análisis de farmacias
- **Productos**: Catálogo, precios y disponibilidad
- **Partners**: Métricas de GMV, pedidos y KPIs
- **Conversacional**: Consultas abiertas y análisis complejos

Selecciona un modo en el panel izquierdo y escribe tu consulta.`,
      timestamp: new Date().toISOString(),
    };
    setMessages([welcomeMessage]);
  }, []);

  // Guardar en historial
  const saveToHistory = useCallback((query: string, queryMode: LudaMindMode) => {
    const entry: HistoryEntry = {
      query,
      mode: queryMode,
      timestamp: new Date().toISOString(),
    };

    setHistory(prev => {
      const updated = [entry, ...prev].slice(0, MAX_HISTORY_ITEMS);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {
        console.warn('Error guardando historial:', e);
      }
      return updated;
    });
  }, []);

  // Enviar query
  const sendQuery = useCallback(async (query: string) => {
    if (!query.trim() || loading) return;

    setError(null);
    setLoading(true);

    // Agregar mensaje del usuario
    const userMessage: LudaMindMessage = {
      id: generateMessageId(),
      type: 'user',
      content: query,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Guardar en historial
    saveToHistory(query, mode);

    try {
      const response = await ludaMindService.sendQuery(
        query,
        mode,
        sessionIdRef.current
      );

      // Agregar respuesta del asistente
      const assistantMessage: LudaMindMessage = {
        id: generateMessageId(),
        type: 'assistant',
        content: response.answer,
        timestamp: response.timestamp,
        metadata: {
          database: response.database,
          confidence: response.confidence,
          mode: response.mode,
          method: response.method,
        },
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsConnected(true);
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : 'Error desconocido';
      setError(errorMessage);
      setIsConnected(false);

      // Agregar mensaje de error
      const errorMsg: LudaMindMessage = {
        id: generateMessageId(),
        type: 'assistant',
        content: `Lo siento, ocurrió un error: ${errorMessage}. Por favor, verifica que el servidor Luda Mind esté activo.`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }, [mode, loading, saveToHistory]);

  // Cambiar modo
  const changeMode = useCallback(async (newMode: LudaMindMode) => {
    setMode(newMode);

    // Notificar al backend (no esperar respuesta)
    ludaMindService.setMode(sessionIdRef.current, newMode).catch(() => {
      // Ignorar errores silenciosamente
    });
  }, []);

  // Limpiar chat
  const clearChat = useCallback(() => {
    const welcomeMessage: LudaMindMessage = {
      id: generateMessageId(),
      type: 'system',
      content: 'Chat limpiado. ¿En qué puedo ayudarte?',
      timestamp: new Date().toISOString(),
    };
    setMessages([welcomeMessage]);
    setError(null);
  }, []);

  // Limpiar historial
  const clearHistory = useCallback(() => {
    setHistory([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.warn('Error limpiando historial:', e);
    }
  }, []);

  // Cargar query del historial
  const loadFromHistory = useCallback((entry: HistoryEntry) => {
    setMode(entry.mode);
    return entry.query;
  }, []);

  return {
    // Estado
    messages,
    mode,
    loading,
    error,
    history,
    isConnected,
    sessionId: sessionIdRef.current,

    // Acciones
    sendQuery,
    changeMode,
    clearChat,
    clearHistory,
    loadFromHistory,
  };
}
