export type ApiResponse<T> = {
  data: T;
  meta?: {
    total?: number;
    limit?: number;
    offset?: number;
  };
  error?: {
    code: string;
    message: string;
    details?: unknown[];
  };
};

const getToken = () => localStorage.getItem('token');

const getHeaders = (hasBody = false) => {
  const headers: Record<string, string> = {};
  const token = getToken();

  if (hasBody) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
};

export async function apiRequest<T>(path: string, options: RequestInit = {}) {
  const hasBody = options.body !== undefined;
  const response = await fetch(path, {
    ...options,
    headers: {
      ...getHeaders(hasBody),
      ...options.headers,
    },
  });
  const payload = (await response.json().catch(() => ({}))) as ApiResponse<T>;

  if (!response.ok) {
    throw new Error(payload.error?.message || 'Erro ao comunicar com a API.');
  }

  return payload;
}

