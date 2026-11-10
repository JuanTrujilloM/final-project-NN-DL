import { useRef, useState } from 'react'
import { useLive } from '../../lib/live'
import { useNow } from '../../lib/format'
import Composer from './Composer'
import RightRail from './RightRail'
import Sidebar from './Sidebar'
import Tweet from './Tweet'

const TABS = ['Para ti', 'Siguiendo']

// The social network: a feed in the style of X where anyone posts; it never shows the classification.
export default function SocialApp({ compact = false }) {
  const { posts, fresh } = useLive()
  const now = useNow()
  const [tab, setTab] = useState(TABS[0])
  const composer = useRef(null)

  return (
    <div className="flex h-full justify-center overflow-y-auto bg-x-bg text-x-text scroll-thin">
      <Sidebar compact={compact} onCompose={() => composer.current?.focus()} />
      <main className={`min-h-full border-x border-x-line ${compact ? 'min-w-0 flex-1' : 'w-[600px] shrink-0'}`}>
        <div className="sticky top-0 z-10 flex border-b border-x-line bg-black/70 backdrop-blur-md">
          {TABS.map((name) => (
            <button key={name} type="button" onClick={() => setTab(name)}
              className="flex h-[53px] flex-1 justify-center transition hover:bg-white/10">
              <span className={`relative flex items-center text-[15px] ${tab === name ? 'font-bold text-x-text' : 'text-x-muted'}`}>
                {name}
                {tab === name && <span className="absolute bottom-0 left-0 h-1 w-full rounded-full bg-x-blue" />}
              </span>
            </button>
          ))}
        </div>
        <Composer ref={composer} />
        {posts.map((post) => <Tweet key={post.id} post={post} now={now} fresh={Boolean(fresh[post.id])} />)}
        {posts.length === 0 && <p className="p-8 text-center text-x-muted">Todavía no hay posts.</p>}
      </main>
      {!compact && <RightRail />}
    </div>
  )
}
