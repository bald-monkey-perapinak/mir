import { useState, useEffect } from 'react'
import { Scenario } from './types'
import { authWithTelegram, getRole, isAdmin } from './api'
import { getTelegramInitData, setupTelegram } from './telegram'
import CatalogPage from './pages/CatalogPage'
import AdminPage from './pages/AdminPage'
import TrainingCardsPage from './pages/TrainingCardsPage'
import TrainingTreePage from './pages/TrainingTreePage'
import TrainingFreeTextPage from './pages/TrainingFreeTextPage'
import ResultsPage from './pages/ResultsPage'
import Spinner from './components/Spinner'

type Screen =
  | 'loading'
  | 'auth_error'
  | 'catalog'
  | 'admin'
  | 'training'
  | 'results'

interface TrainingState {
  scenarios: Scenario[]
  score: number
  correct: number
}

export default function App() {
  const [screen, setScreen] = useState<Screen>('loading')
  const [authError, setAuthError] = useState('')
  const [training, setTraining] = useState<TrainingState | null>(null)
  const [results, setResults] = useState<{ score: number; correct: number; total: number } | null>(null)
  const [activeTab, setActiveTab] = useState<'trainings' | 'admin'>('trainings')

  useEffect(() => {
    setupTelegram()
    bootstrap()
  }, [])

  async function bootstrap() {
    try {
      const initData = getTelegramInitData()

      if (!initData) {
        
        if (import.meta.env.DEV) {
          console.warn('Running outside Telegram — using dev mode (no auth)')
          setScreen('catalog')
          return
        }
        throw new Error('Приложение доступно только в Telegram')
      }

      await authWithTelegram(initData)
      setScreen(isAdmin() ? 'admin' : 'catalog')
    } catch (e: any) {
      setAuthError(e.message || 'Ошибка авторизации')
      setScreen('auth_error')
    }
  }

  function startTraining(scenarios: Scenario[]) {
    setTraining({ scenarios, score: 0, correct: 0 })
    setScreen('training')
  }

  function finishTraining(score: number, correct: number) {
    const total = training?.scenarios.length || 0
    setResults({ score, correct, total })
    setScreen('results')
  }

  function retryTraining() {
    if (training) {
      setScreen('training')
      setResults(null)
    }
  }

  function backToCatalog() {
    setTraining(null)
    setResults(null)
    setScreen(isAdmin() ? 'admin' : 'catalog')
  }

  

  if (screen === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <Spinner size="lg" />
        <p className="text-sm text-gray-500 mt-4">Загрузка…</p>
      </div>
    )
  }

  if (screen === 'auth_error') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 px-6 text-center">
        <span className="text-5xl mb-4">🔒</span>
        <h2 className="font-bold text-gray-900 mb-2">Ошибка авторизации</h2>
        <p className="text-sm text-gray-500 mb-6">{authError}</p>
        <button onClick={bootstrap} className="bg-brand text-white rounded-xl px-6 py-3 text-sm font-semibold">
          Повторить
        </button>
      </div>
    )
  }

  if (screen === 'training' && training) {
    const type = training.scenarios[0]?.type
    if (type === 'cards') {
      return <TrainingCardsPage scenarios={training.scenarios} onFinish={finishTraining} />
    }
    if (type === 'tree') {
      return <TrainingTreePage scenarios={training.scenarios} onFinish={finishTraining} />
    }
    if (type === 'free_text') {
      return <TrainingFreeTextPage scenarios={training.scenarios} onFinish={finishTraining} />
    }
    
    return <TrainingCardsPage scenarios={training.scenarios.filter(s => s.type === 'cards')} onFinish={finishTraining} />
  }

  if (screen === 'results' && results) {
    return (
      <ResultsPage
        score={results.score}
        correct={results.correct}
        total={results.total}
        onRetry={retryTraining}
        onBack={backToCatalog}
      />
    )
  }

  
  const role = getRole()

  return (
    <div className="flex flex-col min-h-screen">
      <div className="flex-1 overflow-y-auto pb-16">
        {role === 'admin' ? (
          activeTab === 'trainings'
            ? <CatalogPage onStartTraining={startTraining} />
            : <AdminPage />
        ) : (
          <CatalogPage onStartTraining={startTraining} />
        )}
      </div>

      {}
      {role === 'admin' && (
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 flex z-40">
          <button
            onClick={() => setActiveTab('trainings')}
            className={`flex-1 flex flex-col items-center py-3 text-xs gap-1 transition
              ${activeTab === 'trainings' ? 'text-brand font-semibold' : 'text-gray-400'}`}
          >
            <span className="text-xl">🎯</span>
            Тренировки
          </button>
          <button
            onClick={() => setActiveTab('admin')}
            className={`flex-1 flex flex-col items-center py-3 text-xs gap-1 transition
              ${activeTab === 'admin' ? 'text-brand font-semibold' : 'text-gray-400'}`}
          >
            <span className="text-xl">⚙️</span>
            Документы
          </button>
        </nav>
      )}
    </div>
  )
}
