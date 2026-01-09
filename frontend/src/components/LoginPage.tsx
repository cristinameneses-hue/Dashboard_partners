import { GoogleLogin, CredentialResponse, googleLogout } from '@react-oauth/google';
import { useAuth } from '../contexts/AuthContext';
import { useState } from 'react';
import LudaLogoFull from './LudaLogoFull';

export default function LoginPage() {
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showSwitchAccount, setShowSwitchAccount] = useState(false);
  const [loginKey, setLoginKey] = useState(0);

  const handleSuccess = async (credentialResponse: CredentialResponse) => {
    if (!credentialResponse.credential) {
      setError('No credential received from Google');
      return;
    }

    setIsLoading(true);
    setError(null);
    setShowSwitchAccount(false);

    try {
      await login(credentialResponse.credential);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setError(errorMessage);
      // Si el error es de dominio no autorizado, mostrar opcion de cambiar cuenta
      if (errorMessage.toLowerCase().includes('domain') ||
          errorMessage.toLowerCase().includes('dominio') ||
          errorMessage.toLowerCase().includes('autorizado') ||
          errorMessage.toLowerCase().includes('allowed')) {
        setShowSwitchAccount(true);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleError = () => {
    setError('Google login failed. Please try again.');
  };

  const handleSwitchAccount = () => {
    // Limpiar estado de Google OAuth
    googleLogout();
    // Limpiar cookies de sesion de Google abriendo la pagina de signout
    // Esto fuerza a Google a pedir seleccion de cuenta la proxima vez
    window.open('https://accounts.google.com/Logout', '_blank', 'width=500,height=600');
    setError('Cierra la ventana de Google y vuelve a hacer click en "Iniciar sesion con Google"');
    setShowSwitchAccount(false);
    // Forzar re-render del componente GoogleLogin
    setLoginKey(prev => prev + 1);
  };

  return (
    <div className="min-h-screen flex items-center justify-center" style={{
      background: 'linear-gradient(135deg, #00A651 0%, #008C45 50%, #006633 100%)'
    }}>
      <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-2xl max-w-md w-full mx-4">
        <div className="text-center mb-8">
          <div className="flex justify-center mb-6">
            <LudaLogoFull height={60} />
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            Dashboard Partners
          </h1>
          <p className="text-white/70">
            Accede con tu cuenta de LudaPartners
          </p>
        </div>

        {error && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 mb-6">
            <p className="text-red-200 text-sm text-center">{error}</p>
            {showSwitchAccount && (
              <div className="mt-4 text-center">
                <p className="text-white/70 text-xs mb-3">
                  Parece que iniciaste sesion con una cuenta personal.
                </p>
                <button
                  onClick={handleSwitchAccount}
                  className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  Cambiar de cuenta Google
                </button>
              </div>
            )}
          </div>
        )}

        <div className="flex flex-col items-center gap-4">
          {isLoading ? (
            <div className="flex items-center gap-3 text-white">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span>Iniciando sesion...</span>
            </div>
          ) : (
            <>
              <GoogleLogin
                key={loginKey}
                onSuccess={handleSuccess}
                onError={handleError}
                useOneTap={false}
                theme="filled_black"
                shape="pill"
                size="large"
                text="signin_with"
              />
              <button
                onClick={handleSwitchAccount}
                className="text-white/60 hover:text-white text-sm underline transition-colors"
              >
                Usar otra cuenta de Google
              </button>
            </>
          )}
        </div>

        <div className="mt-8 pt-6 border-t border-white/20">
          <p className="text-white/50 text-xs text-center">
            Solo usuarios con email @ludapartners.com pueden acceder
          </p>
        </div>
      </div>
    </div>
  );
}
