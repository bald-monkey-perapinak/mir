export interface User {
  id: string
  telegram_id: number
  role: 'admin' | 'doctor'
  full_name: string | null
}

export interface Document {
  id: string
  title: string
  original_name: string
  file_format: string
  status: 'pending' | 'processing' | 'indexed' | 'generating' | 'scenarios_ready' | 'error'
  chunk_count: number
  scenario_count: number
  created_at: string
  error_message?: string
}

export interface Scenario {
  id: string
  document_id: string
  type: 'cards' | 'tree' | 'free_text'
  title: string
  description?: string
  difficulty: number
  scenario_json: CardsScenario | TreeScenario | FreeTextScenario
  status: string
}

export interface CardsScenario {
  type: 'cards'
  title: string
  description: string
  options: string[]
  correct_option_index: number
  explanations: Record<string, string>
  consequences: Record<string, string>
  visual_hint: Record<string, string>
  difficulty: number
}

export interface TreeBlock {
  id: string
  text: string
}

export interface TreeScenario {
  type: 'tree'
  title: string
  description: string
  blocks: TreeBlock[]
  correct_order: string[]
  step_explanations: Record<string, string>
  difficulty: number
}

export interface FreeTextScenario {
  type: 'free_text'
  title: string
  question: string
  ideal_answer: string
  criteria: Record<string, string>
  difficulty: number
}

export interface CheckResponse {
  correct: boolean
  score_delta: number
  explanation?: string
  consequence?: string
  visual_hint?: string
  detail?: any
}

export interface TrainingSession {
  scenarios: Scenario[]
  currentIndex: number
  totalScore: number
  correctCount: number
}
