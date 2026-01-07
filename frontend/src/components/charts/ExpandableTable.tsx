import { useState, useRef, ReactNode, cloneElement, isValidElement, ReactElement } from 'react';
import html2canvas from 'html2canvas';
import TableModal from './TableModal';

interface ExpandableTableProps {
  title: string;
  children: ReactNode;
  dataColumns?: number; // Number of data columns for calculating table width
}

export default function ExpandableTable({ 
  title, 
  children,
  dataColumns = 12
}: ExpandableTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const tableRef = useRef<HTMLDivElement>(null);

  // Clone children with modified props for expanded view
  const renderExpandedContent = () => {
    if (isValidElement(children)) {
      // Clone the table component with expanded mode
      return cloneElement(children as ReactElement<any>, {
        isExpanded: true,
        showHeader: false
      });
    }
    return children;
  };

  // Download table as image (captures full table including scrolled content)
  const handleDownload = async () => {
    if (!tableRef.current || isDownloading) return;
    
    setIsDownloading(true);
    try {
      // Get the card and scrollable container
      const cardElement = tableRef.current.querySelector('.card') as HTMLElement;
      const scrollContainer = tableRef.current.querySelector('.overflow-x-auto') as HTMLElement;
      const tableElement = tableRef.current.querySelector('table') as HTMLElement;
      
      if (!cardElement || !tableElement) {
        throw new Error('Table elements not found');
      }
      
      // Store original styles
      const originalCardOverflow = cardElement.style.overflow;
      const originalCardWidth = cardElement.style.width;
      const originalContainerOverflow = scrollContainer?.style.overflow || '';
      const originalContainerWidth = scrollContainer?.style.width || '';
      
      // Temporarily expand to show full content
      cardElement.style.overflow = 'visible';
      cardElement.style.width = 'fit-content';
      if (scrollContainer) {
        scrollContainer.style.overflow = 'visible';
        scrollContainer.style.width = 'fit-content';
      }
      
      // Wait for reflow
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const canvas = await html2canvas(cardElement, {
        backgroundColor: '#ffffff',
        scale: 2, // Higher resolution
        logging: false,
        useCORS: true,
        width: tableElement.scrollWidth + 40, // Add padding
        height: cardElement.scrollHeight,
        windowWidth: tableElement.scrollWidth + 100,
        windowHeight: cardElement.scrollHeight + 100
      });
      
      // Restore original styles
      cardElement.style.overflow = originalCardOverflow;
      cardElement.style.width = originalCardWidth;
      if (scrollContainer) {
        scrollContainer.style.overflow = originalContainerOverflow;
        scrollContainer.style.width = originalContainerWidth;
      }
      
      const link = document.createElement('a');
      link.download = `${title.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().split('T')[0]}.png`;
      link.href = canvas.toDataURL('image/png');
      link.click();
    } catch (error) {
      console.error('Error downloading table:', error);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <>
      {/* Original table with expand and download buttons */}
      <div className="relative group" ref={tableRef}>
        {children}
        
        {/* Button container - top right corner */}
        <div className="absolute top-3 right-3 flex gap-2 opacity-0 group-hover:opacity-100 transition-all duration-200 z-20">
          {/* Download button */}
          <button
            onClick={handleDownload}
            disabled={isDownloading}
            className="p-2 bg-white/90 hover:bg-white rounded-lg shadow-md border border-gray-200 transition-all duration-200 hover:scale-110 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Descargar imagen"
            aria-label="Descargar imagen"
          >
            {isDownloading ? (
              <svg className="animate-spin h-5 w-5 text-gray-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            ) : (
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-5 w-5 text-gray-600 hover:text-blue-600" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" 
                />
              </svg>
            )}
          </button>
          
          {/* Expand button */}
          <button
            onClick={() => setIsExpanded(true)}
            className="p-2 bg-white/90 hover:bg-white rounded-lg shadow-md border border-gray-200 transition-all duration-200 hover:scale-110"
            title="Ampliar tabla"
            aria-label="Ampliar tabla"
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
      </div>

      {/* Expanded modal */}
      <TableModal
        isOpen={isExpanded}
        onClose={() => setIsExpanded(false)}
        title={title}
        dataColumns={dataColumns}
      >
        {renderExpandedContent()}
      </TableModal>
    </>
  );
}

