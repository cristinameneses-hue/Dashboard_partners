import { useState, ReactNode, cloneElement, isValidElement, ReactElement } from 'react';
import ChartModal from './ChartModal';

interface ExpandableChartProps {
  title: string;
  children: ReactNode;
  dataPoints?: number; // Number of data points for calculating chart width
}

export default function ExpandableChart({ 
  title, 
  children,
  dataPoints = 12
}: ExpandableChartProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Clone children with modified props for expanded view
  const renderExpandedContent = () => {
    if (isValidElement(children)) {
      // Clone the chart component with expanded height and hidden header
      return cloneElement(children as ReactElement<any>, {
        height: 500,
        showHeader: false
      });
    }
    return children;
  };

  return (
    <>
      {/* Original chart with expand button */}
      <div className="relative group">
        {children}
        
        {/* Expand button - top right corner */}
        <button
          onClick={() => setIsExpanded(true)}
          className="absolute top-3 right-3 p-2 bg-white/90 hover:bg-white rounded-lg shadow-md border border-gray-200 opacity-0 group-hover:opacity-100 transition-all duration-200 hover:scale-110 z-10"
          title="Ampliar gráfico"
          aria-label="Ampliar gráfico"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-5 w-5 text-gray-600 hover:text-green-600" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" 
            />
          </svg>
        </button>
      </div>

      {/* Expanded modal */}
      <ChartModal
        isOpen={isExpanded}
        onClose={() => setIsExpanded(false)}
        title={title}
        dataPoints={dataPoints}
      >
        {renderExpandedContent()}
      </ChartModal>
    </>
  );
}

