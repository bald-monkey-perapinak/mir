import { useState, useEffect } from 'react'
import { Document, Scenario } from '../types'
import { fetchAvailableDocuments, fetchScenarios } from '../api'
import Spinner from '../components/Spinner'

const TYPE_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  cards:     { label: 'Карточки', icon: '🃏', color: 'bg-blue-100 text-blue-700' },
  tree:      { label: 'Алгоритм', icon: '🔀', color: 'bg-purple-100 text-purple-700' },
  free_text: { label: 'Свободный ответ', icon: '✏️', color: 'bg-orange-100 text-orange-700' },
}

interface Props {
  onStartTraining: (scenarios: Scenario[]) => void
}

export default function CatalogPage({ onStartTraining }: Props) {
  const [docs, setDocs] = useState<Document[]>([])
  const [scenarios, setScenarios] = useState<Record<string, Scenario[]>>({})
  const [expanded, setExpanded] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadingScenarios, setLoadingScenarios] = useState<string | null>(null)

  useEffect(() => {
    fetchAvailableDocuments()
      .then(setDocs)
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  async function toggleDoc(docId: string) {
    if (expanded === docId) { setExpanded(null); return }
    setExpanded(docId)
    if (!scenarios[docId]) {
      setLoadingScenarios(docId)
      try {
        const list = await fetchScenarios(docId)
        setScenarios(s => ({ ...s, [docId]: list }))
      } finally {
        setLoadingScenarios(null)
      }
    }
  }

  function startAll(docId: string) {
    const list = scenarios[docId] || []
    if (list.length > 0) onStartTraining(list)
  }

  function startByType(docId: string, type: string) {
    const list = (scenarios[docId] || []).filter(s => s.type === type)
    if (list.length > 0) onStartTraining(list)
  }

  if (loading) return <div className="flex-1 flex items-center justify-center"><Spinner /></div>

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <div className="px-4 pt-5 pb-3">
        <h1 className="text-2xl font-bold text-gray-900">Тренировки</h1>
        <p className="text-sm text-gray-500 mt-1">Выберите регламент для обучения</p>
      </div>

      {docs.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center px-4 text-center">
          <span className="text-5xl mb-4">📋</span>
          <p className="text-gray-500 text-sm">Тренировки пока не добавлены.<br/>Обратитесь к администратору.</p>
        </div>
      ) : (
        <div className="px-4 pb-6 space-y-3">
          {docs.map(doc => {
            const docScenarios = scenarios[doc.id] || []
            const typeGroups = docScenarios.reduce((acc, s) => {
              acc[s.type] = (acc[s.type] || 0) + 1
              return acc
            }, {} as Record<string, number>)

            return (
              <div key={doc.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <button
                  onClick={() => toggleDoc(doc.id)}
                  className="w-full text-left p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-xl">
                          {doc.file_format === 'pdf' ? '📄' : doc.file_format === 'docx' ? '📝' : '📃'}
                        </span>
                        <p className="font-semibold text-sm text-gray-800 leading-snug">{doc.title}</p>
                      </div>
                      <p className="text-xs text-gray-400 ml-8">
                        {doc.scenario_count} заданий · {doc.file_format?.toUpperCase()}
                      </p>
                    </div>
                    <span className="text-gray-400 mt-1">{expanded === doc.id ? '▲' : '▼'}</span>
                  </div>
                </button>

                {expanded === doc.id && (
                  <div className="px-4 pb-4 border-t border-gray-100">
                    {loadingScenarios === doc.id ? (
                      <Spinner size="sm" />
                    ) : (
                      <>
                        {}
                        <button
                          onClick={() => startAll(doc.id)}
                          className="w-full bg-brand text-white rounded-xl py-3 font-semibold text-sm mt-3 mb-3"
                        >
                          ▶ Начать все задания ({docScenarios.length})
                        </button>

                        {}
                        <div className="space-y-2">
                          {Object.entries(typeGroups).map(([type, count]) => {
                            const info = TYPE_LABELS[type] || { label: type, icon: '📌', color: 'bg-gray-100 text-gray-700' }
                            return (
                              <button
                                key={type}
                                onClick={() => startByType(doc.id, type)}
                                className="w-full flex items-center justify-between bg-gray-50 hover:bg-gray-100 rounded-xl px-4 py-3 transition"
                              >
                                <div className="flex items-center gap-2">
                                  <span>{info.icon}</span>
                                  <span className="text-sm text-gray-700">{info.label}</span>
                                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${info.color}`}>
                                    {count}
                                  </span>
                                </div>
                                <span className="text-brand text-sm">→</span>
                              </button>
                            )
                          })}
                        </div>
                      </>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
