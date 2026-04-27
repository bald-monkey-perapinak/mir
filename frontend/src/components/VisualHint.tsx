const VISUAL_MAP: Record<string, { emoji: string; label: string }> = {
  patient_calm:       { emoji: '😊', label: 'Пациент в норме' },
  patient_distressed: { emoji: '😟', label: 'Состояние ухудшилось' },
  patient_critical:   { emoji: '🚨', label: 'Критическое состояние' },
  doctor_approve:     { emoji: '✅', label: 'Действие одобрено' },
  doctor_concern:     { emoji: '⚠️', label: 'Ошибка врача' },
  error_medical:      { emoji: '❌', label: 'Нарушение протокола' },
  emergency_red:      { emoji: '🔴', label: 'Экстренная ситуация' },
  success_green:      { emoji: '🟢', label: 'Успешно' },
  form_ok:            { emoji: '📋', label: 'Документ верен' },
  form_error:         { emoji: '📛', label: 'Ошибка в документе' },
  time_critical:      { emoji: '⏱️', label: 'Мало времени' },
  algorithm_complete: { emoji: '✔️', label: 'Алгоритм выполнен' },
  algorithm_error:    { emoji: '🔄', label: 'Ошибка в алгоритме' },
}

interface Props {
  visualId?: string
}

export default function VisualHint({ visualId }: Props) {
  if (!visualId) return null
  const info = VISUAL_MAP[visualId] || { emoji: '📌', label: visualId }
  return (
    <div className="flex items-center gap-2 text-sm text-gray-600 bg-white rounded-lg px-3 py-2 border border-gray-200 w-fit">
      <span className="text-2xl">{info.emoji}</span>
      <span>{info.label}</span>
    </div>
  )
}
