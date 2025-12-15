interface LudaLogoFullProps {
  className?: string;
  height?: number;
}

export default function LudaLogoFull({ className = '', height = 60 }: LudaLogoFullProps) {
  // Aspect ratio aproximado del logo completo (ancho/alto)
  const aspectRatio = 3.2;
  const width = height * aspectRatio;
  
  return (
    <svg 
      xmlns="http://www.w3.org/2000/svg" 
      viewBox="0 0 320 100" 
      width={width} 
      height={height}
      className={className}
    >
      {/* Bocadillo de chat verde */}
      <path 
        d="M50 6 C74 6 94 26 94 50 C94 74 74 94 50 94 C42 94 34 91 28 87 L10 96 L16 76 C10 68 6 59 6 50 C6 26 26 6 50 6 Z" 
        fill="#3CB371"
      />
      
      {/* Estructura molecular */}
      {/* Triángulo inferior */}
      <line x1="30" y1="70" x2="50" y2="50" stroke="white" strokeWidth="4" strokeLinecap="round"/>
      <line x1="50" y1="50" x2="30" y2="45" stroke="white" strokeWidth="4" strokeLinecap="round"/>
      <line x1="30" y1="45" x2="30" y2="70" stroke="white" strokeWidth="4" strokeLinecap="round"/>
      
      {/* Rama superior izquierda */}
      <line x1="30" y1="45" x2="22" y2="30" stroke="white" strokeWidth="4" strokeLinecap="round"/>
      <circle cx="22" cy="30" r="4.5" fill="white"/>
      
      {/* Y superior derecha */}
      <line x1="50" y1="50" x2="65" y2="35" stroke="white" strokeWidth="4" strokeLinecap="round"/>
      <line x1="65" y1="35" x2="58" y2="22" stroke="white" strokeWidth="4" strokeLinecap="round"/>
      <line x1="65" y1="35" x2="80" y2="30" stroke="white" strokeWidth="4" strokeLinecap="round"/>
      <circle cx="58" cy="22" r="4.5" fill="white"/>
      <circle cx="80" cy="30" r="4.5" fill="white"/>
      <circle cx="65" cy="35" r="4.5" fill="white"/>
      
      {/* Rama derecha desde Y */}
      <line x1="80" y1="30" x2="88" y2="45" stroke="white" strokeWidth="4" strokeLinecap="round"/>
      <circle cx="88" cy="45" r="4.5" fill="white"/>
      
      {/* Nodos del triángulo */}
      <circle cx="30" cy="70" r="4.5" fill="white"/>
      <circle cx="50" cy="50" r="4.5" fill="white"/>
      <circle cx="30" cy="45" r="4.5" fill="white"/>
      
      {/* Texto LUDA */}
      <text x="110" y="50" fontFamily="'Outfit', 'Inter', Arial, sans-serif" fontSize="38" fontWeight="300" fill="white" letterSpacing="2">
        LUDA
      </text>
      
      {/* Texto Partners */}
      <text x="110" y="82" fontFamily="'Outfit', 'Inter', Arial, sans-serif" fontSize="28" fontWeight="400" fill="rgba(255,255,255,0.8)" letterSpacing="1">
        Partners
      </text>
    </svg>
  );
}

