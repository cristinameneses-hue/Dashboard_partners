/**
 * Luda Mind - Sistema Inteligente de Consultas
 * Pagina principal del chat con IA
 * Diseño fiel al original HTML con tema claro y acentos verdes
 */

import { useState, useRef, useEffect, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useLudaMind } from '../hooks/useLudaMind';
import {
  LUDA_MIND_MODES,
  QUERY_EXAMPLES,
  QUERY_TEMPLATES,
  PERIOD_LABELS,
  PARTNER_LABELS,
  PROVINCES,
  buildQueryFromTemplate,
  type LudaMindMode,
  type LudaMindMessage,
  type HistoryEntry,
  type PeriodOption,
  type PartnerOption,
  type QueryTemplate,
  type QueryParams,
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
  // Query Builder styles
  queryBuilder: {
    background: 'white',
    borderRadius: '12px',
    padding: '1.5rem',
    marginBottom: '1rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    border: '1px solid #e1e8ed',
  },
  queryBuilderHeader: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: '1rem',
  },
  queryBuilderTitle: {
    fontSize: '1rem',
    fontWeight: 600,
    color: '#2c3e50',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  queryBuilderToggle: {
    padding: '0.4rem 0.8rem',
    background: '#f8f9fa',
    border: '1px solid #e1e8ed',
    borderRadius: '6px',
    fontSize: '0.8rem',
    color: '#6c757d',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  },
  dropdownsRow: {
    display: 'flex',
    gap: '1rem',
    flexWrap: 'wrap' as const,
    marginBottom: '1rem',
  },
  dropdownGroup: {
    flex: '1 1 200px',
    minWidth: '150px',
  },
  dropdownLabel: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#6c757d',
    marginBottom: '0.4rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  dropdown: {
    width: '100%',
    padding: '0.6rem 0.8rem',
    border: '2px solid #e1e8ed',
    borderRadius: '8px',
    fontSize: '0.9rem',
    color: '#2c3e50',
    background: 'white',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    appearance: 'none' as const,
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%236c757d' viewBox='0 0 16 16'%3E%3Cpath d='M8 11L3 6h10l-5 5z'/%3E%3C/svg%3E")`,
    backgroundRepeat: 'no-repeat',
    backgroundPosition: 'right 0.8rem center',
    paddingRight: '2.5rem',
  },
  searchableDropdown: {
    position: 'relative' as const,
  },
  searchInput: {
    width: '100%',
    padding: '0.6rem 0.8rem',
    border: '2px solid #e1e8ed',
    borderRadius: '8px',
    fontSize: '0.9rem',
    color: '#2c3e50',
    background: 'white',
    transition: 'all 0.2s ease',
  },
  dropdownOptions: {
    position: 'absolute' as const,
    top: '100%',
    left: 0,
    right: 0,
    maxHeight: '200px',
    overflowY: 'auto' as const,
    background: 'white',
    border: '2px solid #41A837',
    borderRadius: '8px',
    marginTop: '4px',
    zIndex: 1000,
    boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
  },
  dropdownOption: {
    padding: '0.6rem 0.8rem',
    cursor: 'pointer',
    fontSize: '0.9rem',
    color: '#2c3e50',
    transition: 'all 0.15s ease',
    border: 'none',
    background: 'none',
    width: '100%',
    textAlign: 'left' as const,
  },
  templatesList: {
    marginTop: '1rem',
    borderTop: '1px solid #e1e8ed',
    paddingTop: '1rem',
  },
  templatesTitle: {
    fontSize: '0.8rem',
    fontWeight: 600,
    color: '#6c757d',
    marginBottom: '0.8rem',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.5px',
  },
  templateButton: {
    width: '100%',
    padding: '0.8rem 1rem',
    marginBottom: '0.5rem',
    background: '#f8f9fa',
    border: '2px solid transparent',
    borderRadius: '8px',
    fontSize: '0.9rem',
    color: '#495057',
    cursor: 'pointer',
    textAlign: 'left' as const,
    transition: 'all 0.2s ease',
    display: 'flex',
    alignItems: 'center',
    gap: '0.8rem',
  },
  templateIcon: {
    width: '32px',
    height: '32px',
    background: 'linear-gradient(135deg, #41A837 0%, #2e7a28 100%)',
    borderRadius: '6px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    color: 'white',
    fontSize: '0.9rem',
    flexShrink: 0,
  },
  templateInfo: {
    flex: 1,
  },
  templateLabel: {
    fontWeight: 600,
    marginBottom: '0.2rem',
    color: '#2c3e50',
  },
  templateDescription: {
    fontSize: '0.8rem',
    color: '#6c757d',
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
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => (
                  <div style={{
                    overflowX: 'auto',
                    margin: '1rem 0',
                    borderRadius: '12px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
                    border: '1px solid #e1e8ed',
                  }}>
                    <table style={{
                      borderCollapse: 'collapse',
                      width: '100%',
                      fontSize: '0.85rem',
                      background: 'white',
                    }}>
                      {children}
                    </table>
                  </div>
                ),
                thead: ({ children }) => (
                  <thead style={{
                    background: 'linear-gradient(135deg, #41A837 0%, #2e7a28 100%)',
                  }}>
                    {children}
                  </thead>
                ),
                th: ({ children }) => (
                  <th style={{
                    padding: '0.75rem 1rem',
                    textAlign: 'left',
                    fontWeight: 600,
                    color: 'white',
                    fontSize: '0.8rem',
                    textTransform: 'uppercase',
                    letterSpacing: '0.5px',
                    borderBottom: '2px solid #2e7a28',
                  }}>
                    {children}
                  </th>
                ),
                tr: ({ children }) => (
                  <tr style={{
                    borderBottom: '1px solid #f0f0f0',
                    transition: 'background 0.15s ease',
                  }}>
                    {children}
                  </tr>
                ),
                td: ({ children }) => (
                  <td style={{
                    padding: '0.75rem 1rem',
                    textAlign: 'left',
                    color: '#2c3e50',
                    verticalAlign: 'middle',
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

          {/* Grafica de comparativa - solo para mensajes del bot que contengan tablas comparativas */}
          {!isUser && message.content.includes('|') && (message.content.toLowerCase().includes('metrica') || message.content.toLowerCase().includes('métrica')) && (() => {
            const parsed = parseComparisonDataFromText(message.content);
            if (parsed && parsed.data.length > 0) {
              return (
                <ComparisonChart
                  data={parsed.data}
                  title={`Comparativa ${parsed.provinces[0]} vs ${parsed.provinces[1]}`}
                />
              );
            }
            return null;
          })()}
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

// Interface para datos de grafica de comparativas
interface ComparisonChartData {
  metric: string;
  value1: number;
  value2: number;
  label1: string;
  label2: string;
}

// Componente de grafica de barras para comparativas
function ComparisonChart({ data, title }: { data: ComparisonChartData[], title: string }) {
  if (!data || data.length === 0) return null;

  const label1 = data[0]?.label1 || 'Provincia 1';
  const label2 = data[0]?.label2 || 'Provincia 2';

  return (
    <div style={{
      background: 'white',
      borderRadius: '12px',
      padding: '1.5rem',
      boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      border: '1px solid #e1e8ed',
      marginTop: '1rem',
    }}>
      <div style={{
        fontSize: '1rem',
        fontWeight: 600,
        color: '#2c3e50',
        marginBottom: '1rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
      }}>
        <span>📊</span>
        <span>{title}</span>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e1e8ed" />
          <XAxis
            dataKey="metric"
            tick={{ fontSize: 11, fill: '#6c757d' }}
            angle={-35}
            textAnchor="end"
            height={80}
          />
          <YAxis tick={{ fontSize: 11, fill: '#6c757d' }} />
          <Tooltip
            contentStyle={{
              background: 'white',
              border: '1px solid #e1e8ed',
              borderRadius: '8px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            }}
            formatter={(value: number) => value.toLocaleString('es-ES')}
          />
          <Legend wrapperStyle={{ paddingTop: '10px' }} />
          <Bar dataKey="value1" fill="#41A837" name={label1} radius={[4, 4, 0, 0]} />
          <Bar dataKey="value2" fill="#2e7a28" name={label2} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// Funcion para parsear datos de comparativa desde el texto markdown
function parseComparisonDataFromText(text: string): { data: ComparisonChartData[], provinces: [string, string] } | null {
  const lines = text.split('\n');
  const data: ComparisonChartData[] = [];
  let provinces: [string, string] = ['Provincia 1', 'Provincia 2'];

  // Buscar la fila de encabezado para extraer nombres de provincias
  for (const line of lines) {
    if (line.includes('|') && (line.toLowerCase().includes('metrica') || line.toLowerCase().includes('métrica'))) {
      const parts = line.split('|').map(p => p.trim()).filter(p => p && !p.includes('-'));
      if (parts.length >= 3) {
        provinces = [parts[1], parts[2]];
      }
      break;
    }
  }

  // Parsear filas de datos
  for (const line of lines) {
    if (!line.includes('|') || line.includes('---') || line.toLowerCase().includes('metrica') || line.toLowerCase().includes('métrica')) {
      continue;
    }

    const parts = line.split('|').map(p => p.trim()).filter(p => p);
    if (parts.length >= 3) {
      const metric = parts[0];
      const val1Str = parts[1];
      const val2Str = parts[2];

      // Extraer numeros de las celdas (quitar EUR, %, etc)
      const extractNumber = (str: string): number => {
        const cleaned = str.replace(/[^\d.,]/g, '').replace(/\./g, '').replace(',', '.');
        return parseFloat(cleaned) || 0;
      };

      const val1 = extractNumber(val1Str);
      const val2 = extractNumber(val2Str);

      // Solo incluir si ambos valores son numeros validos
      if (!isNaN(val1) && !isNaN(val2) && (val1 > 0 || val2 > 0)) {
        data.push({
          metric,
          value1: val1,
          value2: val2,
          label1: provinces[0],
          label2: provinces[1],
        });
      }
    }
  }

  if (data.length === 0) return null;
  return { data, provinces };
}

// Componente SearchableDropdown para provincias
interface SearchableDropdownProps {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
  placeholder?: string;
}

function SearchableDropdown({ label, value, options, onChange, placeholder = 'Buscar...' }: SearchableDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  const filteredOptions = useMemo(() => {
    if (!search) return options;
    return options.filter(opt =>
      opt.toLowerCase().includes(search.toLowerCase())
    );
  }, [options, search]);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div style={styles.dropdownGroup}>
      <div style={styles.dropdownLabel}>{label}</div>
      <div style={styles.searchableDropdown} ref={dropdownRef}>
        <input
          type="text"
          value={isOpen ? search : value}
          onChange={(e) => {
            setSearch(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          onFocus={() => {
            setIsOpen(true);
            setSearch('');
          }}
          placeholder={value || placeholder}
          style={{
            ...styles.searchInput,
            borderColor: isOpen ? '#41A837' : '#e1e8ed',
          }}
        />
        {isOpen && (
          <div style={styles.dropdownOptions}>
            {filteredOptions.length === 0 ? (
              <div style={{ ...styles.dropdownOption, color: '#999' }}>
                No se encontraron resultados
              </div>
            ) : (
              filteredOptions.slice(0, 20).map((opt) => (
                <button
                  key={opt}
                  onClick={() => {
                    onChange(opt);
                    setIsOpen(false);
                    setSearch('');
                  }}
                  style={{
                    ...styles.dropdownOption,
                    background: opt === value ? '#e8f5e6' : 'transparent',
                    fontWeight: opt === value ? 600 : 400,
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#f0f9ef'}
                  onMouseLeave={(e) => e.currentTarget.style.background = opt === value ? '#e8f5e6' : 'transparent'}
                >
                  {opt}
                </button>
              ))
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Componente QueryBuilder
interface QueryBuilderProps {
  mode: LudaMindMode;
  onSubmitQuery: (query: string) => void;
  loading: boolean;
}

function QueryBuilder({ mode, onSubmitQuery, loading }: QueryBuilderProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [params, setParams] = useState<QueryParams>({
    period: 'this_month',
    partner: 'all',
    province1: '',
    province2: '',
  });
  const [hoveredTemplate, setHoveredTemplate] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<QueryTemplate | null>(null);

  // Filtrar templates por modo actual
  const modeTemplates = useMemo(() =>
    QUERY_TEMPLATES.filter(t => t.category === mode),
    [mode]
  );

  // Reset template seleccionado cuando cambia el modo
  useEffect(() => {
    setSelectedTemplate(null);
  }, [mode]);

  // Al hacer clic en template, solo lo selecciona (no envía)
  const handleTemplateClick = (template: QueryTemplate) => {
    setSelectedTemplate(template);
  };

  // Construir la query actual basada en template + params
  const currentQuery = useMemo(() => {
    if (!selectedTemplate) return '';
    return buildQueryFromTemplate(selectedTemplate, params);
  }, [selectedTemplate, params]);

  // Enviar la query
  const handleSubmit = () => {
    if (!selectedTemplate) {
      alert('Por favor selecciona una consulta');
      return;
    }

    // Verificar params necesarios
    const missingParams: string[] = [];
    if (selectedTemplate.params.includes('province1') && !params.province1) {
      missingParams.push('Provincia 1');
    }
    if (selectedTemplate.params.includes('province2') && !params.province2) {
      missingParams.push('Provincia 2');
    }

    if (missingParams.length > 0) {
      alert(`Por favor selecciona: ${missingParams.join(', ')}`);
      return;
    }

    onSubmitQuery(currentQuery);
  };

  if (modeTemplates.length === 0) {
    return null;
  }

  return (
    <div style={styles.queryBuilder}>
      <div style={styles.queryBuilderHeader}>
        <div style={styles.queryBuilderTitle}>
          <span>🔧</span>
          <span>Constructor de Consultas</span>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          style={styles.queryBuilderToggle}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = '#e8f5e6';
            e.currentTarget.style.borderColor = '#41A837';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = '#f8f9fa';
            e.currentTarget.style.borderColor = '#e1e8ed';
          }}
        >
          {isExpanded ? 'Ocultar' : 'Mostrar'}
        </button>
      </div>

      {isExpanded && (
        <>
          {/* Templates de queries - PRIMERO para seleccionar que filtros mostrar */}
          <div style={styles.templatesList}>
            <div style={styles.templatesTitle}>Selecciona una consulta</div>
            {modeTemplates.map((template) => {
              const isSelected = selectedTemplate?.id === template.id;
              const isHovered = hoveredTemplate === template.id;
              return (
                <button
                  key={template.id}
                  onClick={() => handleTemplateClick(template)}
                  onMouseEnter={() => setHoveredTemplate(template.id)}
                  onMouseLeave={() => setHoveredTemplate(null)}
                  disabled={loading}
                  style={{
                    ...styles.templateButton,
                    borderColor: isSelected ? '#41A837' : isHovered ? '#41A837' : 'transparent',
                    background: isSelected ? '#e8f5e6' : 'transparent',
                    transform: isHovered ? 'translateX(5px)' : 'none',
                    opacity: loading ? 0.6 : 1,
                  }}
                >
                  <div style={styles.templateIcon}>
                    {isSelected ? '✓' : template.id.includes('province') ? '🗺️' : '📊'}
                  </div>
                  <div style={styles.templateInfo}>
                    <div style={styles.templateLabel}>{template.label}</div>
                    <div style={styles.templateDescription}>{template.description}</div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Dropdowns de parametros - Solo se muestran los necesarios segun el template */}
          {selectedTemplate && (
            <div style={{
              ...styles.dropdownsRow,
              marginTop: '1rem',
              padding: '1rem',
              background: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #e1e8ed',
            }}>
              <div style={{ width: '100%', marginBottom: '0.75rem', fontSize: '0.85rem', color: '#6c757d', fontWeight: 500 }}>
                Configura los parametros:
              </div>

              {/* Periodo - siempre visible si el template lo requiere */}
              {selectedTemplate.params.includes('period') && (
                <div style={styles.dropdownGroup}>
                  <div style={styles.dropdownLabel}>Periodo</div>
                  <select
                    value={params.period}
                    onChange={(e) => setParams({ ...params, period: e.target.value as PeriodOption })}
                    style={styles.dropdown}
                  >
                    {(Object.keys(PERIOD_LABELS) as PeriodOption[])
                      .filter(k => k !== 'custom')
                      .map((key) => (
                        <option key={key} value={key}>{PERIOD_LABELS[key]}</option>
                      ))
                    }
                  </select>
                </div>
              )}

              {/* Partner - solo si el template lo requiere */}
              {selectedTemplate.params.includes('partner') && (
                <div style={styles.dropdownGroup}>
                  <div style={styles.dropdownLabel}>Partner</div>
                  <select
                    value={params.partner}
                    onChange={(e) => setParams({ ...params, partner: e.target.value as PartnerOption })}
                    style={styles.dropdown}
                  >
                    {(Object.keys(PARTNER_LABELS) as PartnerOption[]).map((key) => (
                      <option key={key} value={key}>{PARTNER_LABELS[key]}</option>
                    ))}
                  </select>
                </div>
              )}

              {/* Provincia 1 - solo si el template lo requiere */}
              {selectedTemplate.params.includes('province1') && (
                <SearchableDropdown
                  label="Provincia 1"
                  value={params.province1 || ''}
                  options={PROVINCES}
                  onChange={(v) => setParams({ ...params, province1: v })}
                  placeholder="Seleccionar provincia..."
                />
              )}

              {/* Provincia 2 - solo si el template lo requiere */}
              {selectedTemplate.params.includes('province2') && (
                <SearchableDropdown
                  label="Provincia 2"
                  value={params.province2 || ''}
                  options={PROVINCES}
                  onChange={(v) => setParams({ ...params, province2: v })}
                  placeholder="Seleccionar provincia..."
                />
              )}
            </div>
          )}

          {/* Preview de la query y boton enviar */}
          {selectedTemplate && (
            <div style={{
              marginTop: '1rem',
              padding: '1rem',
              background: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #e1e8ed',
            }}>
              <div style={{ fontSize: '0.8rem', color: '#6c757d', marginBottom: '0.5rem' }}>
                Vista previa de la consulta:
              </div>
              <div style={{
                padding: '0.75rem',
                background: 'white',
                borderRadius: '6px',
                border: '1px solid #dee2e6',
                fontSize: '0.9rem',
                color: '#2c3e50',
                lineHeight: 1.5,
                marginBottom: '1rem',
              }}>
                {currentQuery || 'Selecciona los parametros necesarios...'}
              </div>
              <button
                onClick={handleSubmit}
                disabled={loading || !currentQuery}
                style={{
                  width: '100%',
                  padding: '0.75rem 1.5rem',
                  background: loading || !currentQuery ? '#ccc' : '#41A837',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  fontWeight: 600,
                  cursor: loading || !currentQuery ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s ease',
                }}
                onMouseEnter={(e) => {
                  if (!loading && currentQuery) {
                    e.currentTarget.style.background = '#369830';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = loading || !currentQuery ? '#ccc' : '#41A837';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <span>📤</span>
                <span>{loading ? 'Enviando...' : 'Enviar Consulta'}</span>
              </button>
            </div>
          )}
        </>
      )}
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
  const [hoveredMode, setHoveredMode] = useState<string | null>(null);
  const [hoveredHistory, setHoveredHistory] = useState<number | null>(null);
  const [inputFocused, setInputFocused] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll al final de los mensajes
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Manejar envio de query
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendQuery(input);
      setInput('');
    }
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
  };

  const currentModeConfig = LUDA_MIND_MODES.find(m => m.id === mode);

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
        /* Estilos profesionales para tablas */
        .luda-message-text table tbody tr:nth-child(even) {
          background-color: #f8faf8;
        }
        .luda-message-text table tbody tr:hover {
          background-color: #e8f5e6;
        }
        .luda-message-text table td:first-child {
          font-weight: 600;
          color: #2c3e50;
        }
        .luda-message-text table td:last-child {
          font-weight: 600;
        }
        /* Estilos para diferencias positivas/negativas */
        .luda-message-text table td:last-child {
          color: #41A837;
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
        {/* Chat Header */}
        <div style={styles.chatHeader}>
          <div style={styles.chatTitle}>
            <span>🔍</span>
            <span>Realiza tu Consulta</span>
          </div>
          <div
            style={{
              ...styles.modeIndicator,
              ...(mode === 'conversational' ? styles.modeIndicatorConversational : {}),
              cursor: 'default',
            }}
          >
            <span>{currentModeConfig?.icon}</span>
            <span>Modo {currentModeConfig?.label}</span>
          </div>
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

        {/* Query Builder - Se muestra en todos los modos que tengan templates */}
        <QueryBuilder mode={mode} onSubmitQuery={sendQuery} loading={loading} />

        {/* Messages Area */}
        <div style={styles.messagesContainer}>
          {messages.length === 0 ? (
            <div style={styles.welcomeMessage}>
              <div style={styles.welcomeIcon}>🚀</div>
              <div style={styles.welcomeTitle}>¡Bienvenido a Luda Mind!</div>
              <div style={styles.welcomeText}>
                Selecciona un modo en el panel izquierdo y usa el constructor de consultas<br />
                para configurar los parametros y ejecutar tu busqueda.
              </div>
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
