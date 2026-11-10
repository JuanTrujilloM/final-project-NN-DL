import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { GROUP_STYLES, timeAgo } from '../../lib/format'
import { useLive } from '../../lib/live'
import { SHORT_LABELS } from './labels'

// A classified post as a report: text, category, confidence and, on click, the top-3 probabilities.
export default function ReportCard({ post, now, fresh, showLabel = true }) {
  const { groupsById } = useLive()
  const [open, setOpen] = useState(false)
  const c = post.classification
  if (!c) return null
  const style = GROUP_STYLES[groupsById[c.group]?.color ?? 'slate']
  const pct = Math.round(c.confidence * 100)

  return (
    <article
      onClick={() => setOpen(!open)}
      className={`cursor-pointer rounded-xl border border-slate-200 bg-white p-3 shadow-sm transition hover:border-slate-300 hover:shadow ${fresh ? 'animate-arrive animate-glow' : ''}`}
    >
      <div className="flex items-center gap-1.5 text-xs text-slate-500">
        <span className="truncate font-semibold text-slate-800">{post.author}</span>
        <span className="truncate">@{post.handle}</span>
        <span>·</span>
        <span className="shrink-0">{timeAgo(post.created_at, now)}</span>
        {fresh && <span className="ml-auto shrink-0 rounded-full bg-blue-600 px-1.5 py-0.5 text-[10px] font-bold uppercase text-white">nuevo</span>}
      </div>
      <p className={`mt-1 text-[13px] leading-snug text-slate-800 ${open ? '' : 'line-clamp-3'}`}>{post.text}</p>
      <div className="mt-2 flex items-center gap-2">
        {showLabel && (
          <span className={`truncate rounded-md px-1.5 py-0.5 text-[11px] font-semibold ring-1 ${style.chip}`}>
            {SHORT_LABELS[c.label] ?? c.label_name}
          </span>
        )}
        <div className="flex flex-1 items-center gap-1.5" title={`Confianza del modelo: ${pct} %`}>
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div className={`h-full rounded-full ${style.fill}`} style={{ width: `${pct}%` }} />
          </div>
          <span className="w-8 text-right text-[11px] font-semibold tabular-nums text-slate-600">{pct}%</span>
        </div>
        <ChevronDown className={`h-3.5 w-3.5 shrink-0 text-slate-400 transition ${open ? 'rotate-180' : ''}`} />
      </div>
      {open && (
        <div className="mt-2 space-y-1 border-t border-slate-100 pt-2">
          {c.top.map((t) => (
            <div key={t.label} className="flex items-center gap-2 text-[11px] text-slate-600">
              <span className="w-36 truncate">{t.label_name}</span>
              <div className="h-1 flex-1 rounded-full bg-slate-100">
                <div className="h-full rounded-full bg-slate-400" style={{ width: `${Math.round(t.p * 100)}%` }} />
              </div>
              <span className="w-8 text-right tabular-nums">{Math.round(t.p * 100)}%</span>
            </div>
          ))}
          <div className="pt-1 text-[11px] text-slate-400">Clasificado por {c.model_name}</div>
        </div>
      )}
    </article>
  )
}
