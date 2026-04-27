import { useState, useEffect, useRef } from 'react'
import { Document } from '../types'
import { fetchDocuments, uploadDocument, generateScenarios, deleteDocument, getDocument } from '../api'
import Spinner from '../components/Spinner'

const STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending:         { label: 'Ожидает',      color: 'bg-gray-100 text-gray-600' },
  processing:      { label: 'Обработка…',   color: 'bg-yellow-100 text-yellow-700' },
  indexed:         { label: 'Проиндексирован', color: 'bg-blue-100 text-blue-700' },
  generating:      { label: 'Генерация…',   color: 'bg-purple-100 text-purple-700' },
  scenarios_ready: { label: 'Готов',         color: 'bg-green-100 text-green-700' },
  error:           { label: 'Ошибка',        color: 'bg-red-100 text-red-700' },
}

export default function AdminPage() {
  const [docs, setDocs] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const [title, setTitle] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    loadDocs()
    pollingRef.current = setInterval(pollDocs, 5000)
    return () => { if (pollingRef.current) clearInterval(pollingRef.current) }
  }, [])

  async function loadDocs() {
    try {
      setDocs(await fetchDocuments())
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function pollDocs() {
    const list = await fetchDocuments().catch(() => null)
    if (list) setDocs(list)
  }

  async function handleUpload() {
    if (!file || !title.trim()) return
    setUploading(true)
    try {
      const doc = await uploadDocument(file, title)
      setDocs(d => [doc, ...d])
      setShowUpload(false)
      setTitle('')
      setFile(null)
    } catch (e: any) {
      alert('Ошибка загрузки: ' + e.message)
    } finally {
      setUploading(false)
    }
  }

  async function handleGenerate(docId: string) {
    try {
      await generateScenarios(docId)
      await pollDocs()
    } catch (e: any) {
      alert('Ошибка: ' + e.message)
    }
  }

  async function handleDelete(docId: string) {
    if (!confirm('Удалить документ и все сценарии?')) return
    await deleteDocument(docId)
    setDocs(d => d.filter(x => x.id !== docId))
  }

  if (loading) return <div className="flex-1 flex items-center justify-center"><Spinner /></div>

  return (
    <div className="flex flex-col min-h-screen bg-gray-100">
      <div className="px-4 pt-5 pb-3 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Документы</h1>
          <p className="text-xs text-gray-500 mt-1">Управление регламентами</p>
        </div>
        <button
          onClick={() => setShowUpload(true)}
          className="bg-brand text-white rounded-xl px-4 py-2 text-sm font-semibold"
        >
          + Загрузить
        </button>
      </div>

      {}
      {showUpload && (
        <div className="fixed inset-0 bg-black/40 z-50 flex items-end">
          <div className="bg-white w-full rounded-t-2xl p-5 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Загрузить регламент</h3>
              <button onClick={() => setShowUpload(false)} className="text-gray-400 text-2xl leading-none">×</button>
            </div>
            <input
              type="text"
              placeholder="Название регламента"
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full border-2 border-gray-200 focus:border-brand rounded-xl px-4 py-3 text-sm outline-none bg-white text-gray-900 placeholder-gray-400"
            />
            <div
              onClick={() => fileRef.current?.click()}
              className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition
                ${file ? 'border-brand bg-brand-light' : 'border-gray-300 hover:border-brand'}`}
            >
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.docx,.txt"
                className="hidden"
                onChange={e => setFile(e.target.files?.[0] || null)}
              />
              {file ? (
                <p className="text-sm text-brand font-medium">📎 {file.name}</p>
              ) : (
                <>
                  <p className="text-2xl mb-2">📁</p>
                  <p className="text-sm text-gray-500">Нажмите для выбора файла</p>
                  <p className="text-xs text-gray-400 mt-1">PDF, DOCX, TXT · до 50MB</p>
                </>
              )}
            </div>
            <button
              onClick={handleUpload}
              disabled={uploading || !file || !title.trim()}
              className="w-full bg-brand text-white rounded-xl py-3.5 font-semibold text-sm disabled:opacity-50"
            >
              {uploading ? 'Загружаем…' : 'Загрузить и обработать'}
            </button>
          </div>
        </div>
      )}

      {}
      <div className="px-4 pb-6 space-y-3">
        {docs.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-4xl mb-3">📂</p>
            <p className="text-sm">Нет загруженных документов</p>
          </div>
        )}
        {docs.map(doc => {
          const st = STATUS_CONFIG[doc.status] || { label: doc.status, color: 'bg-gray-100 text-gray-600' }
          const isProcessing = ['processing', 'generating', 'pending'].includes(doc.status)
          return (
            <div key={doc.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
              <div className="flex items-start justify-between gap-2 mb-2">
                <p className="font-semibold text-sm text-gray-800 flex-1 leading-snug">{doc.title}</p>
                <span className={`text-xs px-2 py-1 rounded-full font-medium flex-shrink-0 ${st.color}`}>
                  {isProcessing ? <span className="flex items-center gap-1"><span className="animate-pulse">●</span> {st.label}</span> : st.label}
                </span>
              </div>
              <p className="text-xs text-gray-400 mb-3">
                {doc.original_name} · {doc.chunk_count} чанков · {doc.scenario_count} сценариев
              </p>
              {doc.error_message && (
                <p className="text-xs text-error bg-red-50 rounded-lg p-2 mb-3">{doc.error_message}</p>
              )}
              <div className="flex gap-2">
                {doc.status === 'indexed' && (
                  <button
                    onClick={() => handleGenerate(doc.id)}
                    className="flex-1 bg-brand text-white rounded-lg py-2 text-xs font-semibold"
                  >
                    ⚡ Генерировать тренировки
                  </button>
                )}
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="px-3 py-2 border border-red-200 text-error rounded-lg text-xs"
                >
                  🗑
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
