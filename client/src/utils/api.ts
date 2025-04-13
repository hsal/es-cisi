const API_BASE_URL = 'https://es-cisi.onrender.com';

export const endpoints = {
  getDocumentById: (id: string) => `${API_BASE_URL}/api/document/${id}`,
  search: (query: string, size = 10) =>
    `${API_BASE_URL}/api/search?q=${encodeURIComponent(query)}&size=${size}`,
  autocomplete: (query: string) =>
    `${API_BASE_URL}/api/search/autocomplete?q=${encodeURIComponent(query)}`,
};
