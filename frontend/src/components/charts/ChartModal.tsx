import { ReactNode, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

interface ChartModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  dataPoints?: number; // Number of data points to calculate width
}

export default function ChartModal({ isOpen, onClose, title, children, dataPoints = 12 }: ChartModalProps) {
  const [scrollPosition, setScrollPosition] = useState(0);
  const [maxScroll, setMaxScroll] = useState(0);

  // Handle ESC key to close
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    
    if (isOpen) {
      document.addEventListener('keydown', handleEsc);
      document.body.style.overflow = 'hidden';
    }
    
    return () => {
      document.removeEventListener('keydown', handleEsc);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // Track scroll position for navigation indicator
  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const target = e.target as HTMLDivElement;
    setScrollPosition(target.scrollLeft);
    setMaxScroll(target.scrollWidth - target.clientWidth);
  };

  // Scroll navigation
  const scrollTo = (direction: 'left' | 'right') => {
    const container = document.getElementById('chart-scroll-container');
    if (container) {
      const scrollAmount = 300;
      container.scrollBy({
        left: direction === 'left' ? -scrollAmount : scrollAmount,
        behavior: 'smooth'
      });
    }
  };

  if (!isOpen) return null;

  // Calculate minimum width based on data points (min 55px per data point)
  const minChartWidth = Math.max(dataPoints * 55, 800);

  return createPortal(
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6 md:p-8"
      onClick={onClose}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" />
      
      {/* Modal content */}
      <div 
        className="relative w-full max-w-[95vw] h-[85vh] bg-white rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-scale-in"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 bg-gray-50 shrink-0">
          <h2 className="text-xl font-semibold text-gray-800">{title}</h2>
          <div className="flex items-center gap-4">
            {/* Scroll indicator */}
            <div className="flex items-center gap-2 text-sm text-gray-500">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4m0 6l-4 4-4-4" />
              </svg>
              <span>Usa scroll horizontal para navegar</span>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-gray-200 transition-colors group"
              aria-label="Cerrar"
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-6 w-6 text-gray-500 group-hover:text-gray-700" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Navigation buttons */}
        <div className="flex items-center justify-between px-6 py-2 border-b border-gray-100 bg-white shrink-0">
          <button
            onClick={() => scrollTo('left')}
            disabled={scrollPosition <= 0}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              scrollPosition <= 0 
                ? 'text-gray-300 cursor-not-allowed' 
                : 'text-gray-600 hover:bg-gray-100 hover:text-green-600'
            }`}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            <span className="font-medium">Anterior</span>
          </button>

          {/* Scroll progress indicator */}
          <div className="flex-1 mx-8">
            <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-green-500 rounded-full transition-all duration-150"
                style={{ 
                  width: maxScroll > 0 ? `${(scrollPosition / maxScroll) * 100}%` : '100%',
                  minWidth: '20%'
                }}
              />
            </div>
          </div>

          <button
            onClick={() => scrollTo('right')}
            disabled={scrollPosition >= maxScroll}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
              scrollPosition >= maxScroll 
                ? 'text-gray-300 cursor-not-allowed' 
                : 'text-gray-600 hover:bg-gray-100 hover:text-green-600'
            }`}
          >
            <span className="font-medium">Siguiente</span>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
        
        {/* Chart container with horizontal scroll */}
        <div 
          id="chart-scroll-container"
          className="flex-1 overflow-x-auto overflow-y-auto"
          onScroll={handleScroll}
        >
          <div 
            className="p-6"
            style={{ minWidth: minChartWidth, minHeight: '100%' }}
          >
            {children}
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}

