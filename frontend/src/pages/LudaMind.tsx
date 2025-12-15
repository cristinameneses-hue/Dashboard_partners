/**
 * Luda Mind - Sistema Inteligente de Consultas
 * Pagina principal del chat con IA
 * Diseño fiel al original HTML con tema claro y acentos verdes
 */

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { useLudaMind } from '../hooks/useLudaMind';
import {
  LUDA_MIND_MODES,
  QUERY_EXAMPLES,
  type LudaMindMode,
  type LudaMindMessage,
  type HistoryEntry,
} from '../types/ludaMind';

// Estilos inline para mantener fidelidad con el diseño original
const styles = {
  container: {
    display: 'flex',
    height: 'calc(100vh - 4rem)',
    backgroundColor: '#f5f7fa',
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
  },
  // Sidebar
  sidebar: {
    width: '320px',
    backgroundColor: 'white',
    borderRight: '1px solid #e1e8ed',
    display: 'flex',
    flexDirection: 'column' as const,
    boxShadow: '2px 0 4px rgba(0,0,0,0.05)',
  },
  sidebarHeader: {
    padding: '1.5rem 1.5rem 1rem',
    borderBottom: '1px solid #e1e8ed',
  },
  sidebarTitle: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#2c3e50',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  // Mode buttons
  modesContainer: {
    padding: '1rem',
  },
  modeButton: {
    width: '100%',
    padding: '1rem',
    marginBottom: '0.5rem',
    background: 'white',
    border: '2px solid #e1e8ed',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    textAlign: 'left' as const,
    display: 'flex',
    alignItems: 'center',
    gap: '0.8rem',
  },
  modeButtonActive: {
    background: 'linear-gradient(135deg, #41A837 0%, #2e7a28 100%)',
    borderColor: 'transparent',
    color: 'white',
  },
  modeIcon: {
    fontSize: '1.5rem',
  },
  modeInfo: {
    flex: 1,
  },
  modeName: {
    fontWeight: 600,
    fontSize: '0.95rem',
    marginBottom: '0.2rem',
  },
  modeDescription: {
    fontSize: '0.75rem',
    opacity: 0.8,
  },
  // History
  historyContainer: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '1rem',
  },
  historyHeader: {
    fontSize: '0.85rem',
    fontWeight: 600,
    color: '#666',
    marginBottom: '1rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  clearHistory: {
    fontSize: '0.75rem',
    color: '#999',
    cursor: 'pointer',
    textTransform: 'none' as const,
    letterSpacing: 'normal',
    background: 'none',
    border: 'none',
  },
  historyItem: {
    padding: '0.8rem',
    marginBottom: '0.5rem',
    background: '#f8f9fa',
    borderRadius: '6px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontSize: '0.85rem',
    color: '#495057',
    border: '1px solid transparent',
    display: 'flex',
    alignItems: 'flex-start',
    gap: '0.5rem',
  },
  historyEmpty: {
    textAlign: 'center' as const,
    color: '#adb5bd',
    fontSize: '0.85rem',
    padding: '2rem 1rem',
  },
  // Chat area
  chatArea: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column' as const,
    background: '#fafbfc',
    position: 'relative' as const,
  },
  // Chat header
  chatHeader: {
    background: 'white',
    padding: '1rem 2rem',
    borderBottom: '1px solid #e1e8ed',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  chatTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.8rem',
    fontSize: '1.1rem',
    fontWeight: 600,
    color: '#2c3e50',
  },
  modeIndicator: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    padding: '0.4rem 0.8rem',
    background: '#f8f9fa',
    borderRadius: '20px',
    fontSize: '0.85rem',
    color: '#41A837',
    fontWeight: 500,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    border: 'none',
  },
  modeIndicatorConversational: {
    background: '#41A837',
    color: 'white',
  },
  clearButton: {
    padding: '0.5rem 1rem',
    background: 'transparent',
    border: '1px solid #dee2e6',
    borderRadius: '6px',
    color: '#6c757d',
    cursor: 'pointer',
    fontSize: '0.85rem',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'all 0.2s ease',
  },
  // Messages
  messagesContainer: {
    flex: 1,
    overflowY: 'auto' as const,
    padding: '2rem',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1.5rem',
  },
  // Input area
  inputArea: {
    background: 'white',
    borderTop: '1px solid #e1e8ed',
    padding: '1.5rem 2rem',
  },
  inputContainer: {
    display: 'flex',
    gap: '1rem',
    alignItems: 'center',
    maxWidth: '1000px',
    margin: '0 auto',
  },
  inputWrapper: {
    flex: 1,
    position: 'relative' as const,
  },
  queryInput: {
    width: '100%',
    padding: '0.8rem 1rem',
    border: '2px solid #e1e8ed',
    borderRadius: '8px',
    fontSize: '1rem',
    transition: 'all 0.2s ease',
    background: '#fafbfc',
    outline: 'none',
  },
  sendButton: {
    padding: '0.8rem 1.5rem',
    background: 'linear-gradient(135deg, #41A837 0%, #2e7a28 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '1rem',
    fontWeight: 600,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'all 0.2s ease',
  },
  // Examples dropdown
  examplesDropdown: {
    position: 'absolute' as const,
    top: '60px',
    left: '50%',
    transform: 'translateX(-50%)',
    width: '90%',
    maxWidth: '600px',
    background: 'white',
    borderRadius: '12px',
    boxShadow: '0 10px 30px rgba(0,0,0,0.15)',
    zIndex: 100,
    border: '2px solid #41A837',
    animation: 'slideDown 0.3s ease',
  },
  examplesHeader: {
    padding: '1rem',
    background: 'linear-gradient(135deg, #41A837 0%, #2e7a28 100%)',
    color: 'white',
    borderRadius: '10px 10px 0 0',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  examplesTitle: {
    fontWeight: 600,
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  closeExamples: {
    cursor: 'pointer',
    fontSize: '1.2rem',
    opacity: 0.8,
    transition: 'opacity 0.2s',
    background: 'none',
    border: 'none',
    color: 'white',
  },
  examplesGrid: {
    padding: '1rem',
    display: 'grid',
    gridTemplateColumns: '1fr',
    gap: '0.5rem',
    maxHeight: '400px',
    overflowY: 'auto' as const,
  },
  exampleItem: {
    padding: '0.8rem 1rem',
    background: '#f8f9fa',
    borderRadius: '8px',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    fontSize: '0.9rem',
    color: '#495057',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    border: 'none',
    width: '100%',
    textAlign: 'left' as const,
  },
  exampleNumber: {
    width: '24px',
    height: '24px',
    background: '#41A837',
    color: 'white',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '0.75rem',
    fontWeight: 600,
    flexShrink: 0,
  },
  // Welcome message
  welcomeMessage: {
    textAlign: 'center' as const,
    padding: '3rem',
    color: '#6c757d',
  },
  welcomeIcon: {
    fontSize: '3rem',
    marginBottom: '1rem',
    color: '#41A837',
  },
  welcomeTitle: {
    fontSize: '1.5rem',
    fontWeight: 600,
    color: '#495057',
    marginBottom: '0.5rem',
  },
  welcomeText: {
    fontSize: '1rem',
    lineHeight: 1.5,
  },
  welcomeCta: {
    marginTop: '1.5rem',
    padding: '0.8rem 1.5rem',
    background: 'linear-gradient(135deg, #41A837 0%, #2e7a28 100%)',
    color: 'white',
    border: 'none',
    borderRadius: '8px',
    fontSize: '0.95rem',
    fontWeight: 600,
    cursor: 'pointer',
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
    transition: 'all 0.2s ease',
  },
};

// Componente para mensaje individual
function MessageBubble({ message }: { message: LudaMindMessage }) {
  const isUser = message.type === 'user';

  const messageStyle: React.CSSProperties = {
    display: 'flex',
    gap: '1rem',
    alignItems: 'flex-start',
    animation: 'slideIn 0.3s ease',
  };

  const avatarStyle: React.CSSProperties = {
    width: '36px',
    height: '36px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '1.2rem',
    flexShrink: 0,
    background: isUser ? 'linear-gradient(135deg, #41A837, #2e7a28)' : '#f1f3f5',
    color: isUser ? 'white' : 'inherit',
  };

  const contentStyle: React.CSSProperties = {
    flex: 1,
    maxWidth: '70%',
    marginLeft: isUser ? 'auto' : 0,
    marginRight: isUser ? 0 : 'auto',
  };

  const bubbleStyle: React.CSSProperties = {
    padding: '0.8rem 1.2rem',
    borderRadius: '12px',
    background: isUser ? 'linear-gradient(135deg, #41A837, #2e7a28)' : 'white',
    color: isUser ? 'white' : '#2c3e50',
    boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
  };

  return (
    <div style={messageStyle}>
      {!isUser && <div style={avatarStyle}>🤖</div>}
      <div style={contentStyle}>
        <div style={bubbleStyle}>
          <div className={`luda-message-text ${isUser ? 'user' : ''}`}>
            <ReactMarkdown
              components={{
                table: ({ children }) => (
                  <div style={{ overflowX: 'auto', margin: '0.5rem 0' }}>
                    <table style={{
                      borderCollapse: 'collapse',
                      width: '100%',
                      fontSize: '0.9rem'
                    }}>
                      {children}
                    </table>
                  </div>
                ),
                th: ({ children }) => (
                  <th style={{
                    border: '1px solid #e1e8ed',
                    padding: '0.5rem',
                    textAlign: 'left',
                    background: '#f8f9fa',
                    fontWeight: 600,
                    color: isUser ? 'white' : '#41A837'
                  }}>
                    {children}
                  </th>
                ),
                td: ({ children }) => (
                  <td style={{
                    border: '1px solid #e1e8ed',
                    padding: '0.5rem',
                    textAlign: 'left'
                  }}>
                    {children}
                  </td>
                ),
                code: ({ children, className }) => {
                  const isInline = !className;
                  return isInline ? (
                    <code style={{
                      background: isUser ? 'rgba(255,255,255,0.2)' : '#f1f3f5',
                      padding: '0.15rem 0.4rem',
                      borderRadius: '4px',
                      fontFamily: "'Monaco', 'Courier New', monospace",
                      fontSize: '0.9em',
                      color: isUser ? 'white' : '#c7254e'
                    }}>
                      {children}
                    </code>
                  ) : (
                    <pre style={{
                      background: '#f8f9fa',
                      padding: '0.8rem',
                      borderRadius: '6px',
                      overflow: 'auto',
                      borderLeft: '3px solid #41A837',
                      margin: '0.5rem 0'
                    }}>
                      <code style={{ color: '#2c3e50' }}>{children}</code>
                    </pre>
                  );
                },
                ul: ({ children }) => (
                  <ul style={{ margin: '0.5rem 0', paddingLeft: '1.5rem' }}>{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol style={{ margin: '0.5rem 0', paddingLeft: '1.5rem' }}>{children}</ol>
                ),
                li: ({ children }) => (
                  <li style={{ margin: '0.3rem 0' }}>{children}</li>
                ),
                p: ({ children }) => <p style={{ margin: '0.5rem 0' }}>{children}</p>,
                strong: ({ children }) => (
                  <strong style={{
                    fontWeight: 600,
                    color: isUser ? '#d4f4d4' : '#41A837'
                  }}>
                    {children}
                  </strong>
                ),
                h1: ({ children }) => (
                  <h1 style={{
                    fontSize: '1.4rem',
                    fontWeight: 600,
                    marginTop: '0.5rem',
                    marginBottom: '0.5rem',
                    color: isUser ? 'white' : '#2c3e50',
                    borderBottom: `2px solid ${isUser ? 'rgba(255,255,255,0.3)' : '#41A837'}`,
                    paddingBottom: '0.3rem'
                  }}>
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 style={{
                    fontSize: '1.2rem',
                    fontWeight: 600,
                    marginTop: '0.5rem',
                    marginBottom: '0.5rem',
                    color: isUser ? 'white' : '#34495e'
                  }}>
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 style={{
                    fontSize: '1.05rem',
                    fontWeight: 600,
                    marginTop: '0.5rem',
                    marginBottom: '0.5rem',
                    color: isUser ? 'white' : '#41A837'
                  }}>
                    {children}
                  </h3>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>

          {/* Metadata */}
          {message.metadata && (message.metadata.database || message.metadata.confidence !== undefined) && (
            <div style={{
              fontSize: '0.75rem',
              color: isUser ? 'rgba(255,255,255,0.8)' : '#8e95a3',
              marginTop: '0.5rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              {message.metadata.database && (
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  📊 {message.metadata.database}
                </span>
              )}
              {message.metadata.confidence !== undefined && (
                <span>• Confianza: {Math.round(message.metadata.confidence * 100)}%</span>
              )}
            </div>
          )}
        </div>
      </div>
      {isUser && <div style={avatarStyle}>👤</div>}
    </div>
  );
}

// Indicador de escritura
function TypingIndicator() {
  return (
    <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
      <div style={{
        width: '36px',
        height: '36px',
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '1.2rem',
        flexShrink: 0,
        background: '#f1f3f5',
      }}>
        🤖
      </div>
      <div style={{
        display: 'flex',
        gap: '0.3rem',
        padding: '1rem',
        background: 'white',
        borderRadius: '12px',
        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
      }}>
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            style={{
              width: '8px',
              height: '8px',
              background: '#41A837',
              borderRadius: '50%',
              animation: 'typing 1.4s infinite',
              animationDelay: `${i * 0.2}s`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

// Componente principal
export default function LudaMind() {
  const {
    messages,
    mode,
    loading,
    history,
    isConnected,
    sendQuery,
    changeMode,
    clearChat,
    clearHistory,
    loadFromHistory,
  } = useLudaMind();

  const [input, setInput] = useState('');
  const [showExamples, setShowExamples] = useState(false);
  const [hoveredMode, setHoveredMode] = useState<string | null>(null);
  const [hoveredHistory, setHoveredHistory] = useState<number | null>(null);
  const [hoveredExample, setHoveredExample] = useState<number | null>(null);
  const [inputFocused, setInputFocused] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const examplesRef = useRef<HTMLDivElement>(null);

  // Auto-scroll al final de los mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Cerrar ejemplos al hacer click fuera
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (examplesRef.current && !examplesRef.current.contains(event.target as Node)) {
        setShowExamples(false);
      }
    };

    if (showExamples) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showExamples]);

  // Manejar envio de query
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendQuery(input);
      setInput('');
      setShowExamples(false);
    }
  };

  // Seleccionar ejemplo
  const handleSelectExample = (example: string) => {
    setInput(example);
    setShowExamples(false);
    inputRef.current?.focus();
  };

  // Cargar del historial
  const handleHistoryClick = (entry: HistoryEntry) => {
    const query = loadFromHistory(entry);
    setInput(query);
    inputRef.current?.focus();
  };

  // Cambiar modo
  const handleModeChange = (newMode: LudaMindMode) => {
    changeMode(newMode);
    setShowExamples(true);
  };

  const currentModeConfig = LUDA_MIND_MODES.find(m => m.id === mode);
  const examples = QUERY_EXAMPLES[mode] || [];

  return (
    <div style={styles.container}>
      {/* Estilos de animacion */}
      <style>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateX(-50%) translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(-50%) translateY(0);
          }
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        @keyframes typing {
          0%, 60%, 100% {
            opacity: 0.3;
            transform: translateY(0);
          }
          30% {
            opacity: 1;
            transform: translateY(-10px);
          }
        }
        .luda-message-text {
          line-height: 1.5;
        }
        .luda-message-text a {
          color: #41A837;
          text-decoration: none;
          border-bottom: 1px solid transparent;
        }
        .luda-message-text a:hover {
          border-bottom-color: #41A837;
        }
        .luda-message-text.user a {
          color: white;
        }
        .luda-message-text.user a:hover {
          border-bottom-color: white;
        }
      `}</style>

      {/* Sidebar */}
      <div style={styles.sidebar}>
        {/* Estado de conexion */}
        <div style={{
          padding: '0.8rem 1rem',
          margin: '1rem',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          background: isConnected === null ? '#f8f9fa' : isConnected ? '#e8f5e6' : '#fef2f2',
          border: `1px solid ${isConnected === null ? '#e1e8ed' : isConnected ? '#41A837' : '#ef4444'}`,
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: isConnected === null ? '#999' : isConnected ? '#41A837' : '#ef4444',
          }} />
          <span style={{ fontSize: '0.85rem', color: '#495057' }}>
            {isConnected === null ? 'Verificando...' :
             isConnected ? 'Conectado a Luda Mind' : 'Sin conexion'}
          </span>
        </div>

        {/* Header del sidebar */}
        <div style={styles.sidebarHeader}>
          <div style={styles.sidebarTitle}>
            <span>📋</span>
            <span>Modos de Consulta</span>
          </div>
        </div>

        {/* Selector de Modos */}
        <div style={styles.modesContainer}>
          {LUDA_MIND_MODES.map(modeConfig => {
            const isActive = mode === modeConfig.id;
            const isHovered = hoveredMode === modeConfig.id;

            return (
              <button
                key={modeConfig.id}
                onClick={() => handleModeChange(modeConfig.id)}
                onMouseEnter={() => setHoveredMode(modeConfig.id)}
                onMouseLeave={() => setHoveredMode(null)}
                style={{
                  ...styles.modeButton,
                  ...(isActive ? styles.modeButtonActive : {}),
                  ...(isHovered && !isActive ? {
                    background: '#f0f9ef',
                    borderColor: '#41A837',
                    transform: 'translateX(3px)'
                  } : {}),
                }}
              >
                <div style={styles.modeIcon}>{modeConfig.icon}</div>
                <div style={styles.modeInfo}>
                  <div style={{
                    ...styles.modeName,
                    color: isActive ? 'white' : '#2c3e50'
                  }}>
                    {modeConfig.label}
                  </div>
                  <div style={{
                    ...styles.modeDescription,
                    color: isActive ? 'rgba(255,255,255,0.9)' : '#6c757d'
                  }}>
                    {modeConfig.description}
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* Historial */}
        <div style={styles.historyContainer}>
          <div style={styles.historyHeader}>
            <span>Historial de Consultas</span>
            {history.length > 0 && (
              <button
                onClick={clearHistory}
                onMouseEnter={(e) => e.currentTarget.style.color = '#41A837'}
                onMouseLeave={(e) => e.currentTarget.style.color = '#999'}
                style={styles.clearHistory}
              >
                Limpiar
              </button>
            )}
          </div>
          <div>
            {history.length === 0 ? (
              <div style={styles.historyEmpty}>
                No hay consultas en el historial.<br />
                Tus consultas recientes apareceran aqui.
              </div>
            ) : (
              history.map((entry, idx) => {
                const entryMode = LUDA_MIND_MODES.find(m => m.id === entry.mode);
                const isHovered = hoveredHistory === idx;

                return (
                  <button
                    key={idx}
                    onClick={() => handleHistoryClick(entry)}
                    onMouseEnter={() => setHoveredHistory(idx)}
                    onMouseLeave={() => setHoveredHistory(null)}
                    style={{
                      ...styles.historyItem,
                      ...(isHovered ? {
                        background: '#e8f5e6',
                        borderColor: '#41A837',
                        transform: 'translateX(3px)'
                      } : {}),
                    }}
                  >
                    <span style={{ fontSize: '0.9rem', opacity: 0.7 }}>{entryMode?.icon}</span>
                    <span style={{
                      flex: 1,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {entry.query}
                    </span>
                  </button>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div style={styles.chatArea}>
        {/* Examples Dropdown */}
        {showExamples && (
          <div ref={examplesRef} style={styles.examplesDropdown}>
            <div style={styles.examplesHeader}>
              <div style={styles.examplesTitle}>
                <span>{currentModeConfig?.icon}</span>
                <span>Ejemplos: {currentModeConfig?.label}</span>
              </div>
              <button
                onClick={() => setShowExamples(false)}
                onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
                onMouseLeave={(e) => e.currentTarget.style.opacity = '0.8'}
                style={styles.closeExamples}
              >
                ✕
              </button>
            </div>
            <div style={styles.examplesGrid}>
              {examples.map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelectExample(example)}
                  onMouseEnter={() => setHoveredExample(idx)}
                  onMouseLeave={() => setHoveredExample(null)}
                  style={{
                    ...styles.exampleItem,
                    ...(hoveredExample === idx ? {
                      background: '#e8f5e6',
                      transform: 'translateX(5px)'
                    } : {}),
                  }}
                >
                  <span style={styles.exampleNumber}>{idx + 1}</span>
                  <span>{example}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat Header */}
        <div style={styles.chatHeader}>
          <div style={styles.chatTitle}>
            <span>🔍</span>
            <span>Realiza tu Consulta</span>
          </div>
          <button
            onClick={() => setShowExamples(!showExamples)}
            style={{
              ...styles.modeIndicator,
              ...(mode === 'conversational' ? styles.modeIndicatorConversational : {}),
            }}
          >
            <span>{currentModeConfig?.icon}</span>
            <span>Modo {currentModeConfig?.label}</span>
            <span style={{ fontSize: '0.7rem', opacity: 0.8, marginLeft: '0.3rem' }}>
              ▼ Ver ejemplos
            </span>
          </button>
          <button
            onClick={clearChat}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#f8f9fa';
              e.currentTarget.style.borderColor = '#adb5bd';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
              e.currentTarget.style.borderColor = '#dee2e6';
            }}
            style={styles.clearButton}
          >
            <span>🗑️</span>
            <span>Limpiar</span>
          </button>
        </div>

        {/* Messages Area */}
        <div style={styles.messagesContainer}>
          {messages.length === 0 ? (
            <div style={styles.welcomeMessage}>
              <div style={styles.welcomeIcon}>🚀</div>
              <div style={styles.welcomeTitle}>¡Bienvenido a Luda Mind!</div>
              <div style={styles.welcomeText}>
                Selecciona un modo de consulta para comenzar.<br />
                Haz clic en el modo activo para ver ejemplos de consultas.
              </div>
              <button
                onClick={() => setShowExamples(true)}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(65, 168, 55, 0.3)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
                style={styles.welcomeCta}
              >
                <span>💡</span>
                <span>Ver ejemplos de consultas</span>
              </button>
            </div>
          ) : (
            messages.map(message => (
              <MessageBubble key={message.id} message={message} />
            ))
          )}
          {loading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div style={styles.inputArea}>
          <form onSubmit={handleSubmit} style={styles.inputContainer}>
            <div style={styles.inputWrapper}>
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onFocus={() => setInputFocused(true)}
                onBlur={() => setInputFocused(false)}
                placeholder="Escribe tu pregunta en lenguaje natural"
                disabled={loading}
                style={{
                  ...styles.queryInput,
                  ...(inputFocused ? {
                    borderColor: '#41A837',
                    background: 'white',
                    boxShadow: '0 0 0 3px rgba(65, 168, 55, 0.1)'
                  } : {}),
                }}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !input.trim()}
              onMouseEnter={(e) => {
                if (!loading && input.trim()) {
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 4px 12px rgba(65, 168, 55, 0.3)';
                }
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
              style={{
                ...styles.sendButton,
                opacity: loading || !input.trim() ? 0.6 : 1,
                cursor: loading || !input.trim() ? 'not-allowed' : 'pointer',
              }}
            >
              <span>📤</span>
              <span>{loading ? 'Enviando...' : 'Enviar'}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
