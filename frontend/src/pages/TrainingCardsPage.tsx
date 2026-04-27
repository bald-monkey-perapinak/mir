import { useState } from 'react'
import { Scenario, CardsScenario, CheckResponse } from '../types'
import { checkAnswer } from '../api'
import ProgressBar from '../components/ProgressBar'
import FeedbackPopup from '../components/FeedbackPopup'
import VisualHint from '../components/VisualHint'
import { hapticSuccess, hapticError } from '../telegram'

interface Props {
  scenarios: Scenario[]
  onFinish: (score: number, correct: number) => void
}

export default function TrainingCardsPage({ scenarios, onFinish }: Props) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [selected, setSelected] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<CheckResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [totalScore, setTotalScore] = useState(0)
  const [correctCount, setCorrectCount] = useState(0)

  const scenario = scenarios[currentIdx]
  const data = scenario.scenario_json as CardsScenario
  const isLast = currentIdx === scenarios.length - 1

  async function handleSelect(optionIdx: number) {
    if (selected !== null || loading) return
    setSelected(optionIdx)
    setLoading(true)
    try {
      const result = await checkAnswer(scenario.id, {
        action_type: 'select_option',
        selected_option_index: optionIdx,
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
      setSelected(null)
      setFeedback(null)
      setCurrentIdx(i => i + 1)
    }
  }

  function getCardStyle(idx: number) {
    if (selected === null) return 'border-gray-200 hover:border-brand cursor-pointer'
    if (idx === data.correct_option_index) return 'border-success bg-green-50'
    if (idx === selected) return 'border-error bg-red-50'
    return 'border-gray-200 opacity-50'
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <ProgressBar current={currentIdx + 1} total={scenarios.length} />

      <div className="flex-1 px-4 pb-32 overflow-y-auto">
        {}
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
            Карточки
          </span>
          <span className="text-yellow-500">{'★'.repeat(data.difficulty || 1)}</span>
        </div>

        {}
        {feedback && (
          <div className="mb-3">
            <VisualHint visualId={feedback.visual_hint} />
          </div>
        )}

        {}
        <div className="bg-white rounded-2xl p-5 shadow-sm mb-4 border border-gray-100">
          <h2 className="font-semibold text-base text-gray-800 mb-2">{data.title}</h2>
          <p className="text-sm text-gray-600 leading-relaxed">{data.description}</p>
        </div>

        {}
        <div className="space-y-3">
          {data.options?.map((option, idx) => (
            <button
              key={idx}
              onClick={() => handleSelect(idx)}
              disabled={selected !== null}
              className={`w-full text-left bg-white rounded-xl p-4 border-2 transition-all duration-200 ${getCardStyle(idx)}`}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-gray-800 leading-relaxed">{option}</span>
                {selected !== null && idx === data.correct_option_index && (
                  <span className="text-success text-xl flex-shrink-0">✓</span>
                )}
                {selected === idx && idx !== data.correct_option_index && (
                  <span className="text-error text-xl flex-shrink-0">✗</span>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      {}
      {feedback && (
        <FeedbackPopup
          correct={feedback.correct}
          explanation={feedback.explanation}
          consequence={feedback.consequence}
          onNext={handleNext}
          isLast={isLast}
        />
      )}
    </div>
  )
}
