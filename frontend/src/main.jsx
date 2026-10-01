import React from 'react';
import { createRoot } from 'react-dom/client';
import '@fontsource/dm-sans/400.css';
import '@fontsource/dm-sans/500.css';
import '@fontsource/dm-sans/600.css';
import '@fontsource/space-grotesk/500.css';
import '@fontsource/space-grotesk/600.css';
import App from './App.jsx';
import './styles.css';

class AppErrorBoundary extends React.Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('Error al renderizar Portal FCT:', error, info.componentStack);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="render-error-screen">
          <div className="render-error-panel">
            <span className="eyebrow">ERROR DE INTERFAZ</span>
            <h1>No se pudo mostrar el panel</h1>
            <p>La sesión sigue activa. Recarga el portal y, si vuelve a ocurrir, comparte este detalle:</p>
            <code>{this.state.error.message}</code>
            <button className="button button-primary" onClick={() => window.location.reload()}>
              Recargar portal
            </button>
          </div>
        </main>
      );
    }
    return this.props.children;
  }
}

createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </React.StrictMode>,
);