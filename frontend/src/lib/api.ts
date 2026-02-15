/**
 * Pensieve API Client
 * 
 * Centralized API client with authentication handling.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiError {
  detail: string;
  status: number;
}

class ApiClient {
  private baseUrl: string;
  
  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }
  
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }
  
  private setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', token);
    }
  }
  
  private removeToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('access_token');
    }
  }
  
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const token = this.getToken();
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (token) {
      (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers,
    });
    
    if (!response.ok) {
      const error: ApiError = {
        detail: 'An error occurred',
        status: response.status,
      };
      
      try {
        const data = await response.json();
        error.detail = data.detail || error.detail;
      } catch {
        // Use default error message
      }
      
      if (response.status === 401) {
        this.removeToken();
      }
      
      throw error;
    }
    
    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }
    
    return response.json();
  }
  
  // Auth endpoints
  async register(email: string, password: string) {
    const data = await this.request<{ id: string; email: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    return data;
  }
  
  async login(email: string, password: string) {
    const data = await this.request<{
      access_token: string;
      token_type: string;
      expires_at: string;
    }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(data.access_token);
    return data;
  }
  
  logout() {
    this.removeToken();
  }
  
  isAuthenticated(): boolean {
    return !!this.getToken();
  }
  
  // Entry endpoints
  async getEntries(page = 1, pageSize = 20) {
    return this.request<{
      entries: Array<{
        id: string;
        content: string;
        entry_date: string;
        word_count: number;
        created_at: string;
      }>;
      total: number;
      page: number;
      page_size: number;
    }>(`/api/entries?page=${page}&page_size=${pageSize}`);
  }
  
  async createEntry(content: string, entryDate?: string) {
    return this.request<{
      id: string;
      content: string;
      entry_date: string;
      word_count: number;
    }>('/api/entries', {
      method: 'POST',
      body: JSON.stringify({ 
        content, 
        entry_date: entryDate || new Date().toISOString().split('T')[0] 
      }),
    });
  }
  
  async autosave(content: string, entryId?: string) {
    return this.request<{
      entry_id: string;
      saved_at: string;
      word_count: number;
    }>('/api/entries/autosave', {
      method: 'POST',
      body: JSON.stringify({ content, entry_id: entryId }),
    });
  }
  
  async deleteEntry(entryId: string) {
    return this.request<void>(`/api/entries/${entryId}`, {
      method: 'DELETE',
    });
  }
  
  // Reflection endpoints
  async suggestReflections() {
    return this.request<{
      reflections: Array<{
        id: string;
        content: string;
        metadata: {
          entries_analyzed: number;
          date_range: string;
          concepts: Array<{
            id: string;
            name: string;
            description: string;
            source: string;
            relevance_score: number;
          }>;
          confidence: string;
          confidence_score: number;
        };
        disclaimer: string;
        created_at: string;
      }>;
      total: number;
    }>('/api/reflections/suggest');
  }
  
  async getReflections(page = 1, pageSize = 10) {
    return this.request<{
      reflections: Array<{
        id: string;
        content: string;
        metadata: {
          entries_analyzed: number;
          date_range: string;
          concepts: Array<{
            id: string;
            name: string;
            description: string;
            source: string;
            relevance_score: number;
          }>;
          confidence: string;
          confidence_score: number;
        };
        disclaimer: string;
        created_at: string;
      }>;
      total: number;
    }>(`/api/reflections?page=${page}&page_size=${pageSize}`);
  }
  
  async dismissReflection(reflectionId: string) {
    return this.request<void>(`/api/reflections/${reflectionId}/dismiss`, {
      method: 'POST',
    });
  }
  
  // Concepts
  async getConcepts(category?: string) {
    const query = category ? `?category=${category}` : '';
    return this.request<{
      concepts: Array<{
        id: string;
        name: string;
        category: string;
        description: string;
        source_citation: string;
        tags: string[];
      }>;
      total: number;
    }>(`/api/concepts${query}`);
  }
}

// Export singleton instance
export const api = new ApiClient();
export default api;
