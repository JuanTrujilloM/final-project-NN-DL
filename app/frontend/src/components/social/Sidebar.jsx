import { Link, useLocation } from 'react-router-dom'
import { Bell, Bookmark, Columns2, Ellipsis, Feather, House, LifeBuoy, Mail, Search, User, Users } from 'lucide-react'
import Logo from './Logo'
import Avatar from './Avatar'

const ITEMS = [
  { icon: House, label: 'Inicio', active: true },
  { icon: Search, label: 'Explorar' },
  { icon: Bell, label: 'Notificaciones', badge: 3 },
  { icon: Mail, label: 'Mensajes' },
  { icon: Bookmark, label: 'Guardados' },
  { icon: Users, label: 'Comunidades' },
  { icon: User, label: 'Perfil' },
  { icon: Ellipsis, label: 'Más opciones' },
]

// Links to the other views of the demo; the one for the current page is hidden.
const VIEWS = [
  { icon: LifeBuoy, label: 'Centro de información', to: '/centro' },
  { icon: Columns2, label: 'Vista demo', to: '/demo' },
]

export default function Sidebar({ compact, onCompose }) {
  const { pathname } = useLocation()
  return (
    <header className={`sticky top-0 flex h-[var(--pane-h,100dvh)] shrink-0 flex-col self-start overflow-y-auto scroll-thin ${compact ? 'w-[72px] items-center px-2' : 'w-[275px] px-3'}`}>
      <div className="flex h-[53px] items-center">
        <div className="rounded-full p-3 text-x-text transition hover:bg-x-hover">
          <Logo className="h-7 w-7" />
        </div>
      </div>
      <nav className="flex flex-col gap-1">
        {ITEMS.map(({ icon: Icon, label, active, badge }) => (
          <a key={label} href="#" onClick={(e) => e.preventDefault()}
            className="group flex w-max items-center gap-5 rounded-full p-3 text-x-text transition hover:bg-x-hover">
            <span className="relative">
              <Icon className="h-[26px] w-[26px]" strokeWidth={active ? 2.6 : 1.8} />
              {badge && <span className="absolute -right-2 -top-1.5 rounded-full bg-x-blue px-1.5 text-[11px] font-bold leading-[18px] text-white">{badge}</span>}
            </span>
            {!compact && <span className={`text-xl ${active ? 'font-bold' : ''}`}>{label}</span>}
          </a>
        ))}
        <div className={`my-1 border-t border-x-line ${compact ? 'mx-2' : 'mx-3'}`} />
        {VIEWS.filter((view) => view.to !== pathname).map(({ icon: Icon, label, to }) => (
          <Link key={to} to={to} title={label}
            className="flex w-max items-center gap-5 rounded-full p-3 text-x-text transition hover:bg-x-hover">
            <Icon className="h-[26px] w-[26px]" strokeWidth={1.8} />
            {!compact && <span className="text-xl">{label}</span>}
          </Link>
        ))}
      </nav>
      <button type="button" onClick={onCompose}
        className={`mt-4 rounded-full bg-x-text font-bold text-black transition hover:bg-white/90 ${compact ? 'h-[52px] w-[52px] p-0' : 'h-[52px] w-[233px] text-[17px]'}`}>
        {compact ? <Feather className="mx-auto h-6 w-6" /> : 'Postear'}
      </button>
      <div className={`mb-3 mt-auto flex items-center gap-3 rounded-full p-3 transition hover:bg-x-hover ${compact ? 'justify-center' : ''}`}>
        <Avatar name="Tú" handle="ciudadano_co" />
        {!compact && (
          <>
            <div className="min-w-0 text-[15px] leading-5">
              <div className="font-bold text-x-text">Ciudadano</div>
              <div className="text-x-muted">@ciudadano_co</div>
            </div>
            <Ellipsis className="ml-auto h-5 w-5 text-x-text" />
          </>
        )}
      </div>
    </header>
  )
}
