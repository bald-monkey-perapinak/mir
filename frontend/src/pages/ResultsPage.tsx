interface Props {
  score: number
  correct: number
  total: number
  onRetry: () => void
  onBack: () => void
}

export default function ResultsPage({ score, correct, total, onRetry, onBack }: Props) {
  const pct = total > 0 ? Math.round((correct / total) * 100) : 0

  const config = pct >= 90
    ? { icon: '🏆', color: 'bg-success', msg: 'Отлично! Вы превосходно знаете этот регламент.' }
    : pct >= 70
    ? { icon: '👍', color: 'bg-brand', msg: 'Хорошо! Несколько моментов стоит повторить.' }
    : pct >= 50
    ? { icon: '📖', color: 'bg-warning', msg: 'Требуется повторение. Изучите указанные пункты СОП.' }
    : { icon: '⚠️', color: 'bg-error', msg: 'Критическая ошибка. Необходимо повторно изучить регламент.' }

  return (
    <div className="flex flex-col min-h-screen bg-gray-100 items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {}
        <div className={`w-20 h-20 rounded-full ${config.color} flex items-center justify-center text-4xl mx-auto mb-5 shadow-lg`}>
          {config.icon}
        </div>

        <h1 className="text-2xl font-bold text-center text-gray-900 mb-1">Тренировка завершена</h1>
        <p className="text-sm text-gray-500 text-center mb-6">{config.msg}</p>

        {}
        <div className="bg-brand rounded-2xl p-5 text-white mb-5">
          <p className="text-sm opacity-75 mb-4 text-center">Результаты</p>
          <div className="grid grid-cols-3 gap-3 text-center">
            <div>
              <p className="text-3xl font-bold">{pct}%</p>
              <p className="text-xs opacity-75 mt-1">Результат</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-green-300">{correct}</p>
              <p className="text-xs opacity-75 mt-1">Верных</p>
            </div>
            <div>
              <p className="text-3xl font-bold text-red-300">{total - correct}</p>
              <p className="text-xs opacity-75 mt-1">Ошибок</p>
            </div>
          </div>

          {}
          <div className="mt-4 h-2 bg-white/20 rounded-full">
            <div
              className="h-full bg-white rounded-full transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
          <p className="text-xs text-center opacity-60 mt-2">Баллов набрано: {score}</p>
        </div>

        {}
        <div className="space-y-3">
          <button
            onClick={onRetry}
            className="w-full bg-brand text-white rounded-xl py-3.5 font-semibold text-sm transition hover:bg-brand-hover"
          >
            🔄 Пройти ещё раз
          </button>
          <button
            onClick={onBack}
            className="w-full border-2 border-brand text-brand bg-transparent rounded-xl py-3.5 font-semibold text-sm transition hover:bg-brand-light"
          >
            ← К списку тренировок
          </button>
        </div>
      </div>
    </div>
  )
}
