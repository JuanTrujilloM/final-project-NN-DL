import { forwardRef, useState } from 'react'
import { CalendarClock, Globe, Image, ListOrdered, MapPin, Smile } from 'lucide-react'
import { useLive } from '../../lib/live'
import Avatar from './Avatar'

const LIMIT = 280

// Circular character counter like the one in X's composer.
function Counter({ length }) {
  const left = LIMIT - length
  const radius = left <= 20 ? 13 : 10
  const circumference = 2 * Math.PI * radius
  const progress = Math.min(length / LIMIT, 1)
  const color = left < 0 ? '#f4212e' : left <= 20 ? '#ffd400' : '#1d9bf0'
  return (
    <div className="relative flex h-[30px] w-[30px] items-center justify-center">
      <svg width="30" height="30" viewBox="0 0 30 30" className="absolute -rotate-90">
        <circle cx="15" cy="15" r={radius} fill="none" stroke="#2f3336" strokeWidth="2.2" />
        <circle cx="15" cy="15" r={radius} fill="none" stroke={color} strokeWidth="2.2"
          strokeDasharray={circumference} strokeDashoffset={circumference * (1 - progress)} />
      </svg>
      {left <= 20 && <span className={`relative text-[12px] ${left < 0 ? 'text-red-500' : 'text-x-muted'}`}>{left}</span>}
    </div>
  )
}

const Composer = forwardRef(function Composer(_, ref) {
  const { publish, busy } = useLive()
  const [text, setText] = useState('')
  const [focused, setFocused] = useState(false)
  const sending = busy === 'publish'
  const canPost = text.trim().length > 0 && text.length <= LIMIT && !sending

  async function submit() {
    if (!canPost) return
    try {
      await publish(text.trim())
      setText('')
    } catch {
      return
    }
  }

  return (
    <div className="flex gap-3 border-b border-x-line px-4 pt-3">
      <Avatar name="Tú" handle="ciudadano_co" />
      <div className="min-w-0 flex-1">
        <textarea
          ref={ref}
          value={text}
          rows={focused || text ? 3 : 2}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit() }}
          placeholder="¿Qué está pasando?"
          className="w-full resize-none bg-transparent pt-2 text-xl text-x-text placeholder:text-x-muted focus:outline-none"
        />
        {(focused || text) && (
          <div className="flex items-center gap-1 border-b border-x-line pb-3 text-[15px] font-bold text-x-blue">
            <Globe className="h-4 w-4" /> Cualquier persona puede responder
          </div>
        )}
        <div className="flex items-center justify-between py-2">
          <div className="-ml-2 flex text-x-blue">
            {[Image, ListOrdered, Smile, CalendarClock, MapPin].map((Icon, i) => (
              <span key={i} className="rounded-full p-2 transition hover:bg-x-blue/10"><Icon className="h-5 w-5" /></span>
            ))}
          </div>
          <div className="flex items-center gap-3">
            {text && <Counter length={text.length} />}
            <button type="button" onClick={submit} disabled={!canPost}
              className="rounded-full bg-x-text px-4 py-1.5 text-[15px] font-bold text-black transition hover:bg-white/90 disabled:opacity-50">
              {sending ? 'Posteando…' : 'Postear'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
})

export default Composer
