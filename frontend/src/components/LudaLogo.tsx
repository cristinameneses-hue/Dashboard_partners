interface LudaLogoProps {
  className?: string;
  size?: number;
}

export default function LudaLogo({ className = '', size = 48 }: LudaLogoProps) {
  // Logo verde horizontal para header con fondo blanco
  return (
    <img
      src="/LUDA-LOGO-HOR-GREEN.svg"
      alt="LUDA Partners"
      height={size}
      className={className}
      style={{ height: `${size}px`, width: 'auto' }}
    />
  );
}
