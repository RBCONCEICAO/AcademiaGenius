/**
 * Configuração centralizada da URL da API.
 * Em dev: http://localhost:8000
 * Em prod: definir VITE_API_URL no .env de produção
 */
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
