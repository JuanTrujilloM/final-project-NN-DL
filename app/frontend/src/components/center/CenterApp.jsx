import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Columns3, Cpu, LayoutGrid, LifeBuoy, Loader2, RefreshCw, X } from 'lucide-react'
import { GROUP_STYLES, timeAgo, useNow } from '../../lib/format'
import { useLive } from '../../lib/live'
import { GroupBoard, LabelBoard } from './Boards'

const VIEW_KEY = 'alertanexo.view'

function readView() {
  try {
    return localStorage.getItem(VIEW_KEY) || 'frentes'
  } catch {
    return 'frentes'
  }
}

function activeTitle(meta) {
  const model = meta.models.find((m) => m.id === meta.active_model)
  if (!model) return ''
  const f1 = model.val_f1_macro ? ` · F1-macro en val ${model.val_f1_macro.toFixed(3)}` : ''
  return `${model.name} · etapa ${model.stage}${f1}`
}

function ModelSelect() {
  const { meta, setModel, busy } = useLive()
  return (
    <label title={activeTitle(meta)} className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-sm shadow-sm">
      <Cpu className="h-4 w-4 text-slate-500" />
      <span className="hidden text-slate-500 md:inline">Modelo</span>
      <select value={meta.active_model ?? ''} disabled={busy === 'model'}
        onChange={(e) => setModel(e.target.value).catch(() => {})}
        className="max-w-[230px] bg-transparent font-semibold text-slate-800 focus:outline-none">
        {meta.models.map((m) => (
          <option key={m.id} value={m.id} disabled={!m.available}>
            {m.name} · E{m.stage}{m.available ? '' : ' (sin pesos)'}
          </option>
        ))}
      </select>
    </label>
  )
}

function ViewToggle({ view, setView }) {
  const options = [
    { id: 'frentes', label: 'Por frentes', icon: LayoutGrid },
    { id: 'categorias', label: 'Por categoría', icon: Columns3 },
  ]
  return (
    <div className="flex rounded-lg bg-slate-100 p-0.5 text-sm">
      {options.map(({ id, label, icon: Icon }) => (
        <button key={id} type="button" onClick={() => setView(id)}
          className={`flex items-center gap-1.5 rounded-md px-2.5 py-1 font-medium transition ${view === id ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}>
          <Icon className="h-4 w-4" /> {label}
        </button>
      ))}
    </div>
  )
}

// Information center for responders: classified posts grouped by response front or by category.
export default function CenterApp({ compact = false }) {
  const { meta, posts, connected, busy, error, clearError, reclassify, groupsById, activeModel } = useLive()
  const now = useNow(10000)
  const [view, setViewState] = useState(readView)
  const setView = (value) => {
    setViewState(value)
    try { localStorage.setItem(VIEW_KEY, value) } catch { return }
  }

  if (!meta) {
    return <div className="flex h-full items-center justify-center bg-slate-50 text-slate-500">{error ?? 'Conectando con el centro…'}</div>
  }

  const classified = posts.filter((p) => p.classification)
  const counts = Object.fromEntries(meta.groups.map((g) => [g.id, 0]))
  for (const post of classified) counts[post.classification.group] += 1
  const outdated = classified.filter((p) => p.classification.model !== meta.active_model).length
  const last = classified[0]

  return (
    <div className="relative flex h-full flex-col bg-slate-50 text-slate-900">
      <header className="flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-white"><LifeBuoy className="h-5 w-5" /></div>
          <div className="leading-tight">
            <div className="font-bold">AlertaNexo</div>
            <div className="text-xs text-slate-500">Centro de información en tiempo real</div>
          </div>
        </div>
        <span className={`flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-semibold ${connected ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
          <span className={`h-2 w-2 rounded-full ${connected ? 'animate-pulse bg-emerald-500' : 'bg-slate-400'}`} />
          {connected ? 'En vivo' : 'Reconectando…'}
        </span>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          <ModelSelect />
          <button type="button" onClick={() => reclassify().catch(() => {})} disabled={busy !== null}
            title="Clasifica de nuevo todos los reportes con el modelo seleccionado"
            className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-sm font-medium shadow-sm transition disabled:opacity-50 ${outdated ? 'border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100' : 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'}`}>
            <RefreshCw className={`h-4 w-4 ${busy === 'reclassify' ? 'animate-spin' : ''}`} />
            Reclasificar{outdated ? ` (${outdated})` : ''}
          </button>
          <ViewToggle view={view} setView={setView} />
          {!compact && (
            <nav className="flex gap-1 text-sm">
              <Link to="/red" className="rounded-lg px-2 py-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800">Red social</Link>
              <Link to="/demo" className="rounded-lg px-2 py-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800">Demo</Link>
            </nav>
          )}
        </div>
      </header>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 border-b border-slate-200 bg-white/60 px-4 py-2 text-xs text-slate-600">
        <span><b className="tabular-nums text-slate-900">{classified.length}</b> reportes</span>
        {meta.groups.map((g) => (
          <span key={g.id} className="flex items-center gap-1.5">
            <span className={`h-2 w-2 rounded-full ${GROUP_STYLES[g.color].dot}`} />
            {groupsById[g.id].name} <b className="tabular-nums text-slate-900">{counts[g.id]}</b>
          </span>
        ))}
        {last && <span className="ml-auto text-slate-400">Último reporte {timeAgo(last.created_at, now)}</span>}
        {activeModel && <span className="text-slate-400">· Clasifica: <b className="font-semibold text-slate-600">{activeModel.name}</b></span>}
      </div>

      {error && (
        <div className="mx-4 mt-3 flex items-center gap-2 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">
          {error}
          <button type="button" onClick={clearError} className="ml-auto"><X className="h-4 w-4" /></button>
        </div>
      )}

      <div className="flex min-h-0 flex-1 flex-col p-3">
        {view === 'frentes'
          ? <GroupBoard posts={classified} now={now} compact={compact} />
          : <LabelBoard posts={classified} now={now} compact={compact} />}
      </div>

      {(busy === 'model' || busy === 'reclassify') && (
        <div className="absolute inset-0 z-20 flex items-center justify-center bg-white/60 backdrop-blur-[1px]">
          <div className="flex items-center gap-3 rounded-xl bg-white px-4 py-3 text-sm font-medium text-slate-700 shadow-lg ring-1 ring-slate-200">
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
            {busy === 'model' ? 'Cargando modelo… los Transformers large tardan unos segundos' : 'Reclasificando reportes…'}
          </div>
        </div>
      )}
    </div>
  )
}
