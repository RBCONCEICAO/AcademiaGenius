import { useState } from 'react';
import { Loader2, GraduationCap, BookOpen, Zap, Shield } from 'lucide-react';
import { signInWithGoogle } from '../lib/supabase';

const FEATURES = [
  { icon: BookOpen, title: 'Busca Multi-Fonte', desc: 'OpenAlex, SciELO, PubMed, arXiv e mais de 10 bases acadêmicas em paralelo.' },
  { icon: Zap,      title: 'IA Generativa',    desc: 'Gemini, GPT-4 ou Claude para gerar documentos ABNT prontos para uso.' },
  { icon: Shield,   title: 'Notebook AI',      desc: 'Converse com suas fontes, gere guias de estudo, FAQs e podcasts automáticos.' },
];

export function Login() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleGoogle = async () => {
    setLoading(true);
    setError('');
    try {
      await signInWithGoogle();
    } catch (e: any) {
      setError('Erro ao conectar com o Google. Verifique a configuração do Supabase.');
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 flex">
      {/* Left panel — branding */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between p-14 relative overflow-hidden">
        {/* Background glow */}
        <div className="absolute inset-0 bg-gradient-to-br from-indigo-600/20 to-purple-600/10 pointer-events-none" />
        <div className="absolute top-1/3 -left-24 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-500 rounded-xl flex items-center justify-center">
              <GraduationCap className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold text-white tracking-tight">AcademiaGenius</span>
          </div>
        </div>

        <div className="relative z-10 space-y-8">
          <div>
            <h1 className="text-4xl font-bold text-white leading-tight">
              Pesquisa acadêmica<br />
              <span className="text-indigo-400">com superpoderes.</span>
            </h1>
            <p className="mt-4 text-slate-400 text-lg leading-relaxed max-w-sm">
              Da busca em bases globais ao documento pronto — em minutos.
            </p>
          </div>

          <div className="space-y-4">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div key={title} className="flex gap-4 items-start group">
                <div className="w-9 h-9 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center shrink-0 group-hover:bg-indigo-500/30 transition">
                  <Icon className="w-4 h-4 text-indigo-400" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-white">{title}</p>
                  <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <p className="relative z-10 text-xs text-slate-600">© 2026 AcademiaGenius. Todos os direitos reservados.</p>
      </div>

      {/* Right panel — login */}
      <div className="flex-1 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          {/* Mobile logo */}
          <div className="flex items-center gap-2 mb-10 lg:hidden">
            <div className="w-9 h-9 bg-indigo-500 rounded-xl flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">AcademiaGenius</span>
          </div>

          <div className="bg-white/5 backdrop-blur-xl border border-white/10 rounded-2xl p-8 shadow-2xl">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-white">Bem-vindo</h2>
              <p className="text-slate-400 text-sm mt-1">Entre com sua conta Google para começar</p>
            </div>

            <button
              onClick={handleGoogle}
              disabled={loading}
              className="w-full flex items-center justify-center gap-3 bg-white hover:bg-gray-50 text-gray-800 font-semibold py-3.5 px-6 rounded-xl transition-all shadow-lg hover:shadow-xl active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin text-gray-500" />
              ) : (
                <svg className="w-5 h-5" viewBox="0 0 48 48">
                  <path fill="#4285F4" d="M44.5 20H24v8.5h11.8C34.7 33.9 30.1 37 24 37c-7.2 0-13-5.8-13-13s5.8-13 13-13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2 11.8 2 2 11.8 2 24s9.8 22 22 22c11 0 21-8 21-22 0-1.3-.2-2.7-.5-4z"/>
                  <path fill="#34A853" d="M6.3 14.7l7 5.1C15.1 16.1 19.2 13 24 13c3.1 0 5.9 1.1 8.1 2.9l6.4-6.4C34.6 4.1 29.6 2 24 2c-7.7 0-14.4 4.4-17.7 10.7z"/>
                  <path fill="#FBBC05" d="M24 46c5.9 0 10.9-2 14.5-5.4l-6.7-5.5C29.9 36.8 27.1 38 24 38c-6.1 0-11.3-4.1-13.1-9.7l-7 5.4C7.4 41.4 15.2 46 24 46z"/>
                  <path fill="#EA4335" d="M44.5 20H24v8.5h11.8c-.8 2.5-2.4 4.6-4.5 6.1l6.7 5.5C41.8 37.3 45 31.1 45 24c0-1.3-.2-2.7-.5-4z"/>
                </svg>
              )}
              {loading ? 'Conectando...' : 'Continuar com Google'}
            </button>

            {error && (
              <div className="mt-4 bg-red-500/10 border border-red-500/20 text-red-400 text-sm rounded-lg px-4 py-3">
                {error}
              </div>
            )}

            <div className="mt-6 pt-6 border-t border-white/10">
              <p className="text-xs text-slate-500 text-center leading-relaxed">
                Ao entrar, você concorda com nossos{' '}
                <span className="text-indigo-400 hover:underline cursor-pointer">Termos de Uso</span>
                {' '}e{' '}
                <span className="text-indigo-400 hover:underline cursor-pointer">Política de Privacidade</span>.
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-3 gap-4 text-center">
            {['10+ bases', 'ABNT/APA', 'Open Access'].map(label => (
              <div key={label} className="bg-white/5 border border-white/10 rounded-xl py-3 px-2">
                <p className="text-white text-xs font-semibold">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
