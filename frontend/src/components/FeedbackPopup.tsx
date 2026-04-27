interface Props {
  correct: boolean
  explanation?: string
  consequence?: string
  onNext: () => void
  isLast?: boolean
  loading?: boolean
}

export default function FeedbackPopup({ correct, explanation, consequence, onNext, isLast, loading }: Props) {
  const bg = correct ? 'bg-success' : 'bg-error'
  const icon = correct ? '✓' : '✗'
  const title = correct ? 'Правильно!' : 'Неверно!'

  return (
    <div className={`fixed bottom-0 left-0 right-0 ${bg} text-white rounded-t-2xl p-5 slide-up z-50 shadow-2xl`}>
      <div className="flex items-center gap-3 mb-3">
        <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-xl font-bold">
          {icon}
        </div>
        <span className="text-lg font-semibold">{title}</span>
      </div>

      {explanation && (
        <p className="text-sm text-white/90 mb-2 leading-relaxed">{explanation}</p>
      )}
      {consequence && !correct && (
        <p className="text-xs text-white/70 italic mb-3">⚠ {consequence}</p>
      )}

      <button
        onClick={onNext}
        disabled={loading}
        className="w-full mt-2 bg-white/20 hover:bg-white/30 disabled:opacity-50 rounded-xl py-3 font-semibold text-sm transition"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"/>
            </svg>
            Загрузка…
          </span>
        ) : isLast ? 'Завершить' : 'Далее →'}
      </button>
    </div>
  )
}
