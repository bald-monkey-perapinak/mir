import { useState } from 'react'
import { Scenario, FreeTextScenario, CheckResponse } from '../types'
import { checkAnswer } from '../api'
import ProgressBar from '../components/ProgressBar'
import { hapticSuccess, hapticError } from '../telegram'

interface Props {
  scenarios: Scenario[]
  onFinish: (score: number, correct: number) => void
}

export default function TrainingFreeTextPage({ scenarios, onFinish }: Props) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [text, setText] = useState('')
  const [feedback, setFeedback] = useState<CheckResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [totalScore, setTotalScore] = useState(0)
  const [correctCount, setCorrectCount] = useState(0)

  const scenario = scenarios[currentIdx]
  const data = scenario.scenario_json as FreeTextScenario
  const isLast = currentIdx === scenarios.length - 1

  async function handleSubmit() {
    if (!text.trim() || loading) return
    setLoading(true)
    try {
      const result = await checkAnswer(scenario.id, {
        action_type: 'free_text',
        free_text: text,
      })
      setFeedback(result)
      if (result.correct) {
        hapticSuccess()
        setCorrectCount(c => c + 1)
      } else {
        hapticError()
      }
      setTotalScore(s => s + result.score_delta)
    } finally {
      setLoading(false)
    }
  }

  function handleNext() {
    if (isLast) {
      onFinish(totalScore, correctCount)
    } else {
      setText('')
      setFeedback(null)
      setCurrentIdx(i => i + 1)
    }
  }

  const detail = feedback?.detail
  const totalPossible = Object.keys(data.criteria || {}).length

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <ProgressBar current={currentIdx + 1} total={scenarios.length} />

      <div className="flex-1 px-4 pb-6 overflow-y-auto">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-medium uppercase tracking-wider text-gray-500">Свободный ответ</span>
          <span className="text-yellow-500">{'★'.repeat(data.difficulty || 1)}</span>
        </div>

        <div className="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100">
          <h2 className="font-semibold text-base text-gray-800 mb-2">{data.title}</h2>
          <p className="text-sm text-gray-700 leading-relaxed">{data.question}</p>
        </div>

        {!feedback && (
          <>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              placeholder="Введите ваш развёрнутый ответ…"
              rows={5}
              className="w-full bg-white border-2 border-gray-200 focus:border-brand rounded-xl p-4 text-sm text-gray-800 outline-none resize-none transition mb-3"
            />
            <button
              onClick={handleSubmit}
              disabled={loading || !text.trim()}
              className="w-full bg-brand text-white rounded-xl py-3.5 font-semibold text-sm disabled:opacity-50 transition flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
                  </svg>
                  AI проверяет ответ…
                </>
              ) : 'Отправить на проверку'}
            </button>
          </>
        )}

        {feedback && detail && (
          <div className="space-y-4">
            {}
            <div className="bg-brand text-white rounded-2xl p-5">
              <p className="text-sm opacity-75 mb-1">Результат</p>
              <div className="flex items-end gap-2">
                <span className="text-4xl font-bold">{detail.total_score}</span>
                <span className="text-xl opacity-75">/ {totalPossible}</span>
              </div>
              <div className="mt-3 h-2 bg-white/20 rounded-full">
                <div
                  className="h-full bg-white rounded-full transition-all"
                  style={{ width: `${(detail.total_score / totalPossible) * 100}%` }}
                />
              </div>
            </div>

            {}
            <div className="bg-white rounded-2xl p-4 shadow-sm border border-gray-100">
              <p className="font-semibold text-sm text-gray-700 mb-3">Критерии оценки</p>
              <div className="space-y-2">
                {Object.entries(detail.criteria_results || {}).map(([key, val]: [string, any]) => (
                  <div key={key} className={`flex gap-3 p-3 rounded-lg ${val.passed ? 'bg-green-50' : 'bg-red-50'}`}>
                    <span className={`text-lg ${val.passed ? 'text-success' : 'text-error'}`}>
                      {val.passed ? '✓' : '✗'}
                    </span>
                    <p className="text-xs text-gray-700 leading-relaxed">{val.comment}</p>
                  </div>
                ))}
              </div>
            </div>

            {}
            {detail.overall_feedback && (
              <div className="bg-blue-50 border border-brand/20 rounded-xl p-4">
                <p className="text-xs font-semibold text-brand mb-1">Комментарий</p>
                <p className="text-sm text-gray-700 leading-relaxed">{detail.overall_feedback}</p>
              </div>
            )}

            {detail.missing_points && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <p className="text-xs font-semibold text-warning mb-1">Что стоило упомянуть</p>
                <p className="text-sm text-gray-700 leading-relaxed">{detail.missing_points}</p>
              </div>
            )}

            <button
              onClick={handleNext}
              className="w-full bg-brand text-white rounded-xl py-3.5 font-semibold text-sm transition"
            >
              {isLast ? 'Завершить' : 'Далее →'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
