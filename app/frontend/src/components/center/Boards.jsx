import { useState } from 'react'
import { ChevronDown, ChevronRight } from 'lucide-react'
import { GROUP_STYLES } from '../../lib/format'
import { useLive } from '../../lib/live'
import { SHORT_LABELS } from './labels'
import ReportCard from './ReportCard'

function byLabel(posts) {
  const out = {}
  for (const post of posts) {
    const label = post.classification?.label
    if (label) (out[label] ??= []).push(post)
  }
  return out
}

function Empty({ text = 'Sin reportes todavía' }) {
  return <p className="rounded-lg border border-dashed border-slate-200 p-4 text-center text-xs text-slate-400">{text}</p>
}

// One column per response front; its categories work as filters. "Contexto" starts collapsed.
function GroupColumn({ group, postsByLabel, now, fresh }) {
  const style = GROUP_STYLES[group.color]
  const [filter, setFilter] = useState(null)
  const [open, setOpen] = useState(group.id !== 'contexto')
  const all = group.labels.flatMap((label) => postsByLabel[label] ?? [])
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
  const shown = filter ? all.filter((p) => p.classification.label === filter) : all

  return (
    <section className={`flex min-h-0 flex-col rounded-2xl border border-slate-200 ${style.soft}`}>
      <div className={`h-1 rounded-t-2xl ${style.bar}`} />
      <button type="button" onClick={() => setOpen(!open)} className="flex items-center gap-2 px-3 pb-2 pt-2.5 text-left">
        <span className={`text-sm font-bold ${style.text}`}>{group.name}</span>
        <span className="rounded-full bg-white px-2 text-xs font-bold tabular-nums text-slate-700 ring-1 ring-slate-200">{all.length}</span>
        {open ? <ChevronDown className="ml-auto h-4 w-4 text-slate-400" /> : <ChevronRight className="ml-auto h-4 w-4 text-slate-400" />}
      </button>
      <div className="flex flex-wrap gap-1 px-3 pb-2">
        {group.labels.map((label) => {
          const count = postsByLabel[label]?.length ?? 0
          const active = filter === label
          return (
            <button key={label} type="button" onClick={() => setFilter(active ? null : label)}
              className={`rounded-md px-1.5 py-0.5 text-[11px] font-medium ring-1 transition ${active ? `${style.chip} font-bold` : 'bg-white text-slate-600 ring-slate-200 hover:ring-slate-300'}`}>
              {SHORT_LABELS[label]} <span className="tabular-nums opacity-70">{count}</span>
            </button>
          )
        })}
      </div>
      {open && (
        <div className="min-h-0 flex-1 space-y-2 overflow-y-auto px-3 pb-3 scroll-thin">
          {shown.length ? shown.map((post) => (
            <ReportCard key={post.id} post={post} now={now} fresh={Boolean(fresh[post.id])} showLabel={!filter} />
          )) : <Empty />}
        </div>
      )}
      {!open && <p className="px-3 pb-3 text-xs text-slate-500">{all.length} reportes de contexto, sin acción inmediata.</p>}
    </section>
  )
}

export function GroupBoard({ posts, now, compact }) {
  const { meta, fresh } = useLive()
  const postsByLabel = byLabel(posts)
  return (
    <div className={`grid min-h-0 flex-1 gap-3 ${compact ? 'grid-cols-2 2xl:grid-cols-4' : 'grid-cols-2 xl:grid-cols-4'}`}>
      {meta.groups.map((group) => (
        <GroupColumn key={group.id} group={group} postsByLabel={postsByLabel} now={now} fresh={fresh} />
      ))}
    </div>
  )
}

// One card per category (the 10 HumAID labels), ordered by response front.
export function LabelBoard({ posts, now, compact }) {
  const { meta, fresh } = useLive()
  const postsByLabel = byLabel(posts)
  return (
    <div className={`grid min-h-0 flex-1 auto-rows-[minmax(220px,1fr)] gap-3 overflow-y-auto pb-1 scroll-thin ${compact ? 'grid-cols-2 2xl:grid-cols-3' : 'grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5'}`}>
      {meta.groups.flatMap((group) => group.labels.map((label) => {
        const style = GROUP_STYLES[group.color]
        const items = postsByLabel[label] ?? []
        const name = meta.labels.find((l) => l.id === label)?.name ?? label
        return (
          <section key={label} className="flex min-h-0 flex-col rounded-2xl border border-slate-200 bg-white">
            <div className="flex items-start gap-2 border-b border-slate-100 px-3 py-2.5">
              <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${style.dot}`} />
              <div className="min-w-0 flex-1">
                <div className="text-[13px] font-bold leading-tight text-slate-800">{name}</div>
                <div className={`text-[11px] ${style.text}`}>{group.name}</div>
              </div>
              <span className="rounded-full bg-slate-100 px-2 text-xs font-bold tabular-nums text-slate-700">{items.length}</span>
            </div>
            <div className="min-h-0 flex-1 space-y-2 overflow-y-auto p-2 scroll-thin">
              {items.length ? items.map((post) => (
                <ReportCard key={post.id} post={post} now={now} fresh={Boolean(fresh[post.id])} showLabel={false} />
              )) : <Empty />}
            </div>
          </section>
        )
      }))}
    </div>
  )
}
