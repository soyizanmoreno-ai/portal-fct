const API_ROOT = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

export async function api(path, options = {}) {
  const token = localStorage.getItem('fct_token');
  const headers = new Headers(options.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  let response;
  try {
    response = await fetch(`${API_ROOT}${path}`, { ...options, headers });
  } catch {
    throw new Error('No se pudo conectar con la API. Comprueba que el backend está iniciado.');
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail;
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join('. ') : detail || `Error ${response.status}`);
  }
  if (response.status === 204) return null;
  return response;
}

export async function requestJson(path, options = {}) {
  const response = await api(path, options);
  return response.json();
}

export async function download(path, filename) {
  const response = await api(path);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}