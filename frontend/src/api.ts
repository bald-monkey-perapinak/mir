import { Document, Scenario, CheckResponse } from './types'

const API_BASE = import.meta.env.VITE_API_BASE ?? '';

let authToken: string | null = localStorage.getItem('auth_token')
let userRole: string | null = localStorage.getItem('user_role')

export function getRole(): string | null { return userRole }
export function isAdmin(): boolean { return userRole === 'admin' }

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  }
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }

  return res.json()
}

export async function authWithTelegram(initData: string) {
  const data = await request<{
    access_token: string
    role: string
    user_id: string
    full_name: string | null
  }>('/api/auth/telegram', {
    method: 'POST',
    body: JSON.stringify({ init_data: initData }),
  })
  authToken = data.access_token
  userRole = data.role
  localStorage.setItem('auth_token', data.access_token)
  localStorage.setItem('user_role', data.role)
  return data
}

export function logout() {
  authToken = null
  userRole = null
  localStorage.removeItem('auth_token')
  localStorage.removeItem('user_role')
}

export async function fetchDocuments(): Promise<Document[]> {
  return request('/api/documents')
}

export async function fetchAvailableDocuments(): Promise<Document[]> {
  return request('/api/documents/available')
}

export async function uploadDocument(file: File, title: string): Promise<Document> {
  const form = new FormData()
  form.append('file', file)
  form.append('title', title)

  const res = await fetch(`${API_BASE}/api/documents`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${authToken}` },
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }))
    throw new Error(err.detail)
  }
  return res.json()
}

export async function getDocument(id: string): Promise<Document> {
  return request(`/api/documents/${id}`)
}

export async function generateScenarios(docId: string) {
  return request(`/api/documents/${docId}/generate`, { method: 'POST' })
}

export async function deleteDocument(docId: string) {
  return request(`/api/documents/${docId}`, { method: 'DELETE' })
}

export async function fetchScenarios(docId?: string, type?: string): Promise<Scenario[]> {
  const params = new URLSearchParams()
  if (docId) params.set('doc_id', docId)
  if (type) params.set('type', type)
  return request(`/api/scenarios?${params}`)
}

export async function getScenario(id: string): Promise<Scenario> {
  return request(`/api/scenarios/${id}`)
}

export async function checkAnswer(
  scenarioId: string,
  payload: {
    action_type: string
    selected_option_index?: number
    blocks_order?: string[]
    free_text?: string
  }
): Promise<CheckResponse> {
  return request(`/api/scenarios/${scenarioId}/check`, {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}
