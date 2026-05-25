import { Component, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props { children: ReactNode }
interface State { error: Error | null }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 p-8">
          <div className="max-w-md w-full bg-white border border-red-200 rounded-2xl p-8 shadow-sm text-center">
            <div className="w-12 h-12 bg-red-50 rounded-full flex items-center justify-center mx-auto mb-4">
              <AlertTriangle className="w-6 h-6 text-red-500" />
            </div>
            <h2 className="text-lg font-bold text-slate-900 mb-2">Algo deu errado</h2>
            <p className="text-sm text-slate-500 mb-6">
              Ocorreu um erro inesperado na aplicação. Recarregue a página para continuar.
            </p>
            <p className="text-xs font-mono text-red-600 bg-red-50 rounded-lg p-3 mb-6 text-left break-words">
              {this.state.error.message}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="bg-slate-900 text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-slate-800 transition">
              Recarregar página
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
