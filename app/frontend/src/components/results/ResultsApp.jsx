import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { BarChart3, Database, Loader2, Trophy } from 'lucide-react'
import { api } from '../../lib/api'
import { useLive } from '../../lib/live'

const SET_NAMES = {
  val: 'Val',
  test: 'Test',
  test_intra: 'Test intra',
  chile_2014: 'Chile 2014',
  colombia: 'Colombia',
}

function setName(id) {
  return SET_NAMES[id] ?? id
}

function formatValue(value) {
  if (typeof value !== 'number') return value ?? '—'
  if (Number.isInteger(value)) return value.toLocaleString('es-CO')
  return value.toFixed(Math.abs(value) < 1 ? 4 : 2)
}

// Highest value of each F1 column, to highlight the best model per set.
function columnMax(rows, columns) {
  return Object.fromEntries(columns.filter((c) => c.startsWith('F1')).map((c) => {
    const values = rows.map((r) => r[c]).filter((v) => typeof v === 'number')
    return [c, values.length ? Math.max(...values) : null]
  }))
}

function DataTable({ rows, highlight = true }) {
  if (!rows?.length) return <p className="text-sm text-slate-500">Sin datos.</p>
  const columns = Object.keys(rows[0])
  const best = highlight ? columnMax(rows, columns) : {}
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
      <table className="w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>{columns.map((c) => <th key={c} className="whitespace-nowrap px-3 py-2 font-semibold">{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-t border-slate-100">
              {columns.map((c) => (
                <td key={c} className={`whitespace-nowrap px-3 py-1.5 tabular-nums ${best[c] != null && row[c] === best[c] ? 'font-bold text-emerald-700' : 'text-slate-700'}`}>
                  {formatValue(row[c])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Section({ title, children, note }) {
  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-base font-bold text-slate-900">{title}</h2>
        {note && <p className="text-sm text-slate-500">{note}</p>}
      </div>
      {children}
    </section>
  )
}

function Segmented({ options, value, onChange }) {
  return (
    <div className="flex flex-wrap gap-1 rounded-lg bg-slate-100 p-0.5 text-sm">
      {options.map((o) => (
        <button key={o.id} type="button" onClick={() => onChange(o.id)}
          className={`rounded-md px-2.5 py-1 font-medium transition ${value === o.id ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-800'}`}>
          {o.label}
        </button>
      ))}
    </div>
  )
}

function Bars({ items }) {
  const max = Math.max(...items.map((i) => i.value), 0)
  return (
    <div className="space-y-1.5 rounded-xl border border-slate-200 bg-white p-4">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-3 text-sm">
          <span className="w-64 shrink-0 truncate text-slate-600" title={item.label}>{item.label}</span>
          <div className="h-5 flex-1 rounded bg-slate-100">
            <div className={`h-5 rounded ${item.value === max ? 'bg-emerald-500' : 'bg-blue-500'}`} style={{ width: `${item.value * 100}%` }} />
          </div>
          <span className={`w-14 text-right tabular-nums ${item.value === max ? 'font-bold text-emerald-700' : 'text-slate-700'}`}>{item.value.toFixed(3)}</span>
        </div>
      ))}
    </div>
  )
}

function Overview({ data, names }) {
  const rows = data.all_stages
  const sets = Object.keys(SET_NAMES).filter((s) => rows.some((r) => typeof r[`F1 ${s}`] === 'number'))
  const [set, setSet] = useState(sets.includes('chile_2014') ? 'chile_2014' : sets[0])
  const items = rows
    .filter((r) => typeof r[`F1 ${set}`] === 'number')
    .map((r) => ({ label: `E${r.etapa} · ${names[`etapa${r.etapa}/${r.modelo}`] ?? r.modelo}`, value: r[`F1 ${set}`] }))
    .sort((a, b) => b.value - a.value)
  return (
    <div className="space-y-8">
      <Section title="F1-macro por conjunto"
        note="Chile 2014 y Colombia son idénticos en todas las etapas: son la comparación directa. Test cambia de idioma entre etapas.">
        <Segmented options={sets.map((s) => ({ id: s, label: setName(s) }))} value={set} onChange={setSet} />
        <Bars items={items} />
      </Section>
      <Section title="Comparación de todas las etapas" note="En verde, el mejor valor de cada columna de F1.">
        <DataTable rows={rows} />
      </Section>
    </div>
  )
}

function Stat({ label, value }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white px-3 py-2">
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`break-words font-bold tabular-nums text-slate-900 ${String(value ?? '').length > 14 ? 'text-sm' : 'text-lg'}`}>{value ?? '—'}</div>
    </div>
  )
}

function PerClass({ report, labelNames }) {
  const rows = Object.entries(report).sort((a, b) => b[1]['f1-score'] - a[1]['f1-score'])
  return (
    <div className="space-y-1.5 rounded-xl border border-slate-200 bg-white p-4">
      {rows.map(([label, m]) => (
        <div key={label} className="flex items-center gap-3 text-sm">
          <span className="w-64 shrink-0 truncate text-slate-600" title={label}>{labelNames[label] ?? label}</span>
          <div className="h-4 flex-1 rounded bg-slate-100">
            <div className="h-4 rounded bg-indigo-500" style={{ width: `${m['f1-score'] * 100}%` }} />
          </div>
          <span className="w-14 text-right tabular-nums font-semibold text-slate-800">{m['f1-score'].toFixed(3)}</span>
          <span className="w-28 text-right text-xs tabular-nums text-slate-400">P {m.precision.toFixed(2)} · R {m.recall.toFixed(2)}</span>
          <span className="w-16 text-right text-xs tabular-nums text-slate-400">n {formatValue(m.support)}</span>
        </div>
      ))}
    </div>
  )
}

function Figure({ src, alt }) {
  return src
    ? <a href={src} target="_blank" rel="noreferrer"><img src={src} alt={alt} className="w-full rounded-xl border border-slate-200 bg-white" /></a>
    : <p className="text-sm text-slate-500">Sin imagen.</p>
}

function ModelPanel({ model, labelNames }) {
  const sets = Object.keys(model.results)
  const [set, setSet] = useState(sets.includes('test') ? 'test' : sets[0])
  const [detail, setDetail] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let alive = true
    api.resultDetail(model.id).then((d) => alive && setDetail(d)).catch((e) => alive && setError(e.message))
    return () => { alive = false }
  }, [model.id])

  const metrics = sets.map((s) => ({ conjunto: setName(s), ...Object.fromEntries(
    Object.entries(model.results[s]).map(([k, v]) => [{ f1_macro: 'F1-macro', f1_weighted: 'F1 ponderado', accuracy: 'accuracy', n: 'n' }[k] ?? k, v]),
  ) }))
  const params = model.parameters?.total ?? model.parameters

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
        <Stat label="Mejor F1-macro en val" value={model.val_f1_macro?.toFixed(4)} />
        <Stat label="Épocas" value={model.epochs} />
        <Stat label="Minutos" value={model.minutes} />
        <Stat label="GPU" value={model.gpu} />
        <Stat label="Parámetros" value={typeof params === 'number' ? `${(params / 1e6).toFixed(0)} M` : null} />
        <Stat label="Modelo base" value={model.base_model ?? model.kind} />
      </div>

      <Section title="Métricas por conjunto">
        <DataTable rows={metrics} highlight={false} />
      </Section>

      <Section title="Por clase y matriz de confusión">
        <Segmented options={sets.map((s) => ({ id: s, label: setName(s) }))} value={set} onChange={setSet} />
        <div className="grid gap-4 xl:grid-cols-2">
          {error && <p className="text-sm text-red-600">{error}</p>}
          {!detail && !error && <p className="flex items-center gap-2 text-sm text-slate-500"><Loader2 className="h-4 w-4 animate-spin" /> Cargando…</p>}
          {detail?.per_class[set] && <PerClass report={detail.per_class[set]} labelNames={labelNames} />}
          <Figure src={model.confusion[set]} alt={`Matriz de confusión en ${setName(set)}`} />
        </div>
      </Section>

      <Section title="Curvas de entrenamiento">
        <Figure src={model.curves} alt="Curvas de entrenamiento" />
      </Section>

      {detail && (
        <details className="rounded-xl border border-slate-200 bg-white p-4 text-sm">
          <summary className="cursor-pointer font-semibold text-slate-800">Hiperparámetros</summary>
          <pre className="mt-3 overflow-x-auto text-xs text-slate-600">{JSON.stringify(detail.hyperparameters, null, 2)}</pre>
        </details>
      )}
    </div>
  )
}

function StageView({ stage, labelNames }) {
  const [selected, setSelected] = useState(stage.models.at(-1)?.id)
  const model = stage.models.find((m) => m.id === selected) ?? stage.models[0]
  return (
    <div className="space-y-8">
      <Section title={`Etapa ${stage.number}: modelos finales`}>
        <DataTable rows={stage.comparison} />
      </Section>
      {model && (
        <Section title="Detalle por modelo">
          <Segmented options={stage.models.map((m) => ({ id: m.id, label: m.name }))} value={model.id} onChange={setSelected} />
          <ModelPanel key={model.id} model={model} labelNames={labelNames} />
        </Section>
      )}
      {stage.selection.length > 0 && (
        <Section title="Selección y screening" note="Tablas de results/etapaX/seleccion/.">
          {stage.selection.map((table) => (
            <details key={table.name} className="space-y-2 rounded-xl border border-slate-200 bg-white p-4">
              <summary className="cursor-pointer text-sm font-semibold text-slate-800">{table.name}</summary>
              <div className="mt-3"><DataTable rows={table.rows} highlight={false} /></div>
            </details>
          ))}
        </Section>
      )}
    </div>
  )
}

function DataView({ data }) {
  return (
    <div className="space-y-8">
      {Object.entries(data).map(([name, rows]) => (
        <Section key={name} title={name}>
          <DataTable rows={rows} highlight={false} />
        </Section>
      ))}
    </div>
  )
}

// Metrics, plots and comparison tables of every stage, read from results/ by the backend.
export default function ResultsApp() {
  const { meta } = useLive()
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [tab, setTab] = useState('resumen')

  useEffect(() => {
    api.results().then(setData).catch((e) => setError(e.message))
  }, [])

  const names = useMemo(() => Object.fromEntries(
    (data?.stages ?? []).flatMap((s) => s.models.map((m) => [m.id, m.name])),
  ), [data])
  const labelNames = useMemo(() => Object.fromEntries((meta?.labels ?? []).map((l) => [l.id, l.name])), [meta])

  const tabs = [
    { id: 'resumen', label: 'Resumen', icon: Trophy },
    ...(data?.stages ?? []).map((s) => ({ id: s.id, label: `Etapa ${s.number}`, icon: BarChart3 })),
    { id: 'datos', label: 'Datos', icon: Database },
  ]
  const stage = data?.stages.find((s) => s.id === tab)

  return (
    <div className="min-h-dvh bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-10 flex flex-wrap items-center gap-3 border-b border-slate-200 bg-white px-4 py-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-900 text-white"><BarChart3 className="h-5 w-5" /></div>
          <div className="leading-tight">
            <div className="font-bold">Resultados de los modelos</div>
            <div className="text-xs text-slate-500">Métricas, gráficas y comparaciones de results/</div>
          </div>
        </div>
        <nav className="flex flex-wrap gap-1 text-sm">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button key={id} type="button" onClick={() => setTab(id)}
              className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 font-medium ${tab === id ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100'}`}>
              <Icon className="h-4 w-4" /> {label}
            </button>
          ))}
        </nav>
        <nav className="ml-auto flex gap-1 text-sm">
          <Link to="/centro" className="rounded-lg px-2 py-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800">Centro</Link>
          <Link to="/demo" className="rounded-lg px-2 py-1.5 text-slate-500 hover:bg-slate-100 hover:text-slate-800">Demo</Link>
        </nav>
      </header>

      <main className="mx-auto max-w-7xl p-4 sm:p-6">
        {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-200">{error}</p>}
        {!data && !error && <p className="flex items-center gap-2 text-slate-500"><Loader2 className="h-5 w-5 animate-spin" /> Cargando resultados…</p>}
        {data && tab === 'resumen' && <Overview data={data} names={names} />}
        {stage && <StageView key={stage.id} stage={stage} labelNames={labelNames} />}
        {data && tab === 'datos' && <DataView data={data.data} />}
      </main>
    </div>
  )
}
