interface LudaLogoFullProps {
  className?: string;
  height?: number;
}

export default function LudaLogoFull({ className = '', height = 55 }: LudaLogoFullProps) {
  // El logo blanco horizontal se usa en el sidebar con fondo verde
  return (
    <img
      src="/LUDA-LOGO-HOR-WHITE.svg"
      alt="LUDA Partners"
      height={height}
      className={className}
      style={{ height: `${height}px`, width: 'auto' }}
    />
  );
}
