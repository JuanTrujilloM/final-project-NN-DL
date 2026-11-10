import { Ellipsis, Search } from 'lucide-react'
import Avatar from './Avatar'

const TRENDS = [
  { place: 'Tendencia en Colombia', name: '#SismoChocó', posts: '18,2 mil posts' },
  { place: 'Noticias · Tendencia', name: 'Puente del río', posts: '4.312 posts' },
  { place: 'Tendencia', name: 'Albergue del coliseo', posts: '1.987 posts' },
  { place: 'Solidaridad · Tendencia', name: '#FuerzaPacífico', posts: '9.540 posts' },
]

const FOLLOW = [
  { name: 'Gestión del Riesgo Local', handle: 'riesgolocal' },
  { name: 'Brigada Comunitaria', handle: 'brigada_comunitaria' },
  { name: 'Radio La Ribera', handle: 'radiolaribera' },
]

export default function RightRail() {
  return (
    <aside className="sticky top-0 hidden h-[var(--pane-h,100dvh)] w-[350px] self-start shrink-0 flex-col gap-4 overflow-y-auto pb-6 pl-8 pr-2 pt-1 lg:flex">
      <label className="flex h-[42px] items-center gap-3 rounded-full bg-x-input px-4 text-x-muted focus-within:bg-black focus-within:ring-1 focus-within:ring-x-blue">
        <Search className="h-[18px] w-[18px]" />
        <input placeholder="Buscar" className="w-full bg-transparent text-[15px] text-x-text placeholder:text-x-muted focus:outline-none" />
      </label>

      <section className="rounded-2xl border border-x-line">
        <h2 className="px-4 pb-1 pt-3 text-xl font-extrabold text-x-text">Qué está pasando</h2>
        {TRENDS.map((trend) => (
          <div key={trend.name} className="flex justify-between px-4 py-3 transition hover:bg-white/[0.03]">
            <div>
              <div className="text-[13px] text-x-muted">{trend.place}</div>
              <div className="text-[15px] font-bold text-x-text">{trend.name}</div>
              <div className="text-[13px] text-x-muted">{trend.posts}</div>
            </div>
            <Ellipsis className="h-[18px] w-[18px] text-x-muted" />
          </div>
        ))}
        <div className="rounded-b-2xl px-4 py-3 text-[15px] text-x-blue transition hover:bg-white/[0.03]">Mostrar más</div>
      </section>

      <section className="rounded-2xl border border-x-line">
        <h2 className="px-4 pb-1 pt-3 text-xl font-extrabold text-x-text">A quién seguir</h2>
        {FOLLOW.map((account) => (
          <div key={account.handle} className="flex items-center gap-3 px-4 py-3 transition hover:bg-white/[0.03]">
            <Avatar name={account.name} handle={account.handle} />
            <div className="min-w-0 flex-1 text-[15px] leading-5">
              <div className="truncate font-bold text-x-text">{account.name}</div>
              <div className="truncate text-x-muted">@{account.handle}</div>
            </div>
            <button type="button" className="rounded-full bg-x-text px-4 py-1.5 text-sm font-bold text-black">Seguir</button>
          </div>
        ))}
      </section>

      <p className="px-4 text-[13px] leading-5 text-x-muted">
        Condiciones de servicio · Política de privacidad · Accesibilidad · © 2026 Nexo (demostración)
      </p>
    </aside>
  )
}
