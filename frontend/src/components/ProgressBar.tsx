interface Props {
  current: number
  total: number
}

export default function ProgressBar({ current, total }: Props) {
  const pct = total > 0 ? Math.round((current / total) * 100) : 0
  return (
    <div className="px-4 pt-3 pb-2">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Вопрос {current} из {total}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full bg-brand rounded-full progress-fill transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}
