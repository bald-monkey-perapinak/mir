import { useState } from 'react'
import {
  DndContext,
  closestCenter,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  SortableContext,
  verticalListSortingStrategy,
  useSortable,
  arrayMove,
} from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { Scenario, TreeScenario, CheckResponse } from '../types'
import { checkAnswer } from '../api'
import ProgressBar from '../components/ProgressBar'
import FeedbackPopup from '../components/FeedbackPopup'
import VisualHint from '../components/VisualHint'
import { hapticSuccess, hapticError, hapticLight } from '../telegram'

interface Props {
  scenarios: Scenario[]
  onFinish: (score: number, correct: number) => void
}

interface BlockError {
  position: number
  user_block: string
  correct_block: string
  explanation?: string
  llm_explanation?: string
  hint?: string
}

function SortableBlock({ id, text, state }: { id: string; text: string; state: 'neutral' | 'correct' | 'error' }) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({ id })
  const style = { transform: CSS.Transform.toString(transform), transition }

  const stateStyles = {
    neutral: 'border-gray-200 bg-white',
    correct: 'border-success bg-green-50',
    error:   'border-error bg-red-50',
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={`flex items-center gap-3 rounded-xl p-3.5 border-2 ${stateStyles[state]} ${isDragging ? 'opacity-50 shadow-lg' : ''} drag-handle`}
    >
      <span className="text-gray-400 flex-shrink-0">⠿</span>
      <span className="text-sm text-gray-800 leading-snug">{text}</span>
      {state === 'correct' && <span className="ml-auto text-success text-lg">✓</span>}
      {state === 'error'   && <span className="ml-auto text-error text-lg">✗</span>}
    </div>
  )
}

export default function TrainingTreePage({ scenarios, onFinish }: Props) {
  const [currentIdx, setCurrentIdx] = useState(0)
  const [checked, setChecked] = useState(false)
  const [feedback, setFeedback] = useState<CheckResponse | null>(null)
  const [errors, setErrors] = useState<BlockError[]>([])
  const [loading, setLoading] = useState(false)
  const [totalScore, setTotalScore] = useState(0)
  const [correctCount, setCorrectCount] = useState(0)
  const [expandedError, setExpandedError] = useState<string | null>(null)

  const scenario = scenarios[currentIdx]
  const data = scenario.scenario_json as TreeScenario
  const isLast = currentIdx === scenarios.length - 1

  const [order, setOrder] = useState<string[]>(() =>
    [...data.blocks.map(b => b.id)]
  )

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(TouchSensor, { activationConstraint: { delay: 100, tolerance: 5 } })
  )

  function handleDragEnd(event: DragEndEvent) {
    const { active, over } = event
    if (over && active.id !== over.id) {
      hapticLight()
      setOrder(prev => {
        const from = prev.indexOf(String(active.id))
        const to   = prev.indexOf(String(over.id))
        return arrayMove(prev, from, to)
      })
    }
  }

  async function handleCheck() {
    if (loading) return
    setLoading(true)
    try {
      const result = await checkAnswer(scenario.id, {
        action_type: 'submit_order',
        blocks_order: order,
      })
      setFeedback(result)
      setChecked(true)
      if (result.correct) {
        hapticSuccess()
        setCorrectCount(c => c + 1)
      } else {
        hapticError()
        setErrors(result.detail || [])
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
      const next = scenarios[currentIdx + 1]
      const nextData = next.scenario_json as TreeScenario
      setOrder(nextData.blocks.map(b => b.id))
      setChecked(false)
      setFeedback(null)
      setErrors([])
      setExpandedError(null)
      setCurrentIdx(i => i + 1)
    }
  }

  const blocksMap = Object.fromEntries(data.blocks.map(b => [b.id, b.text]))
  const errorIds = new Set(errors.map(e => e.user_block))

  function getBlockState(id: string): 'neutral' | 'correct' | 'error' {
    if (!checked) return 'neutral'
    return errorIds.has(id) ? 'error' : 'correct'
  }

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <ProgressBar current={currentIdx + 1} total={scenarios.length} />

      <div className="flex-1 px-4 pb-36 overflow-y-auto">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-medium uppercase tracking-wider text-gray-500">Алгоритм</span>
          <span className="text-yellow-500">{'★'.repeat(data.difficulty || 1)}</span>
        </div>

        {feedback && <div className="mb-3"><VisualHint visualId={feedback.visual_hint} /></div>}

        <div className="bg-white rounded-2xl p-4 shadow-sm mb-4 border border-gray-100">
          <h2 className="font-semibold text-base text-gray-800 mb-1">{data.title}</h2>
          <p className="text-sm text-gray-500">{data.description}</p>
        </div>

        <p className="text-xs text-gray-400 mb-3 text-center">Перетащите шаги в правильном порядке</p>

        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={order} strategy={verticalListSortingStrategy}>
            <div className="space-y-2">
              {order.map((id, pos) => (
                <div key={id}>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400 w-5 text-right flex-shrink-0">{pos + 1}.</span>
                    <div className="flex-1">
                      <SortableBlock id={id} text={blocksMap[id] || id} state={getBlockState(id)} />
                    </div>
                  </div>
                  {}
                  {checked && errorIds.has(id) && (
                    <div className="ml-7 mt-1">
                      <button
                        onClick={() => setExpandedError(expandedError === id ? null : id)}
                        className="text-xs text-error underline"
                      >
                        {expandedError === id ? 'Скрыть' : 'Почему ошибка?'}
                      </button>
                      {expandedError === id && (
                        <div className="mt-1 bg-red-50 border border-red-200 rounded-lg p-3 text-xs text-red-800">
                          {errors.find(e => e.user_block === id)?.llm_explanation ||
                           errors.find(e => e.user_block === id)?.explanation ||
                           'Неверная позиция в алгоритме.'}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </SortableContext>
        </DndContext>

        {!checked && (
          <button
            onClick={handleCheck}
            disabled={loading}
            className="w-full mt-5 bg-brand text-white rounded-xl py-3.5 font-semibold text-sm disabled:opacity-50 transition"
          >
            {loading ? 'Проверяем…' : 'Проверить порядок'}
          </button>
        )}
      </div>

      {feedback && checked && (
        <FeedbackPopup
          correct={feedback.correct}
          explanation={feedback.explanation}
          onNext={handleNext}
          isLast={isLast}
        />
      )}
    </div>
  )
}
