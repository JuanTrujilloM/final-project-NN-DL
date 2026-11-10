import { useState } from 'react'
import { BadgeCheck, Bookmark, ChartNoAxesColumn, Ellipsis, Heart, MessageCircle, Repeat2, Share } from 'lucide-react'
import { compactCount, hash, timeAgo } from '../../lib/format'
import Avatar from './Avatar'

// Hashtags, mentions and links in blue, like X.
function RichText({ text }) {
  return text.split(/(\s+)/).map((part, i) =>
    /^(#|@)\w+/.test(part) || /^https?:\/\//.test(part)
      ? <span key={i} className="text-x-blue">{part}</span>
      : part,
  )
}

function Action({ icon: Icon, count, hover, active, onClick }) {
  return (
    <button type="button" onClick={onClick} className={`group flex items-center gap-1 text-[13px] ${active ? hover.text : 'text-x-muted'} ${hover.group}`}>
      <span className={`rounded-full p-2 transition ${hover.bg}`}>
        <Icon className="h-[18px] w-[18px]" fill={active ? 'currentColor' : 'none'} />
      </span>
      {count > 0 && <span className="-ml-1">{compactCount(count)}</span>}
    </button>
  )
}

const HOVER = {
  blue: { group: 'hover:text-x-blue', bg: 'group-hover:bg-x-blue/10', text: 'text-x-blue' },
  green: { group: 'hover:text-[#00ba7c]', bg: 'group-hover:bg-[#00ba7c]/10', text: 'text-[#00ba7c]' },
  pink: { group: 'hover:text-[#f91880]', bg: 'group-hover:bg-[#f91880]/10', text: 'text-[#f91880]' },
}

export default function Tweet({ post, now, fresh }) {
  const seed = hash(post.id)
  const own = post.handle === 'ciudadano_co'
  const base = own ? { replies: 0, reposts: 0, likes: 0, views: 1 } : {
    replies: seed % 40, reposts: (seed >> 3) % 120, likes: (seed >> 5) % 900, views: 1000 + ((seed >> 7) % 40000),
  }
  const [liked, setLiked] = useState(false)
  const [reposted, setReposted] = useState(false)
  const verified = !own && seed % 3 === 0

  return (
    <article className={`flex gap-3 border-b border-x-line px-4 py-3 transition hover:bg-white/[0.03] ${fresh ? 'animate-arrive' : ''}`}>
      <Avatar name={post.author} handle={post.handle} />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1 text-[15px] leading-5">
          <span className="truncate font-bold text-x-text">{post.author}</span>
          {verified && <BadgeCheck className="h-[18px] w-[18px] shrink-0 fill-x-blue text-black" />}
          <span className="truncate text-x-muted">@{post.handle}</span>
          <span className="text-x-muted">·</span>
          <span className="shrink-0 text-x-muted">{timeAgo(post.created_at, now)}</span>
          <Ellipsis className="ml-auto h-[18px] w-[18px] shrink-0 text-x-muted" />
        </div>
        <p className="mt-0.5 whitespace-pre-wrap break-words text-[15px] leading-5 text-x-text"><RichText text={post.text} /></p>
        <div className="-ml-2 mt-1.5 flex max-w-[425px] justify-between">
          <Action icon={MessageCircle} count={base.replies} hover={HOVER.blue} />
          <Action icon={Repeat2} count={base.reposts + (reposted ? 1 : 0)} hover={HOVER.green} active={reposted} onClick={() => setReposted(!reposted)} />
          <Action icon={Heart} count={base.likes + (liked ? 1 : 0)} hover={HOVER.pink} active={liked} onClick={() => setLiked(!liked)} />
          <Action icon={ChartNoAxesColumn} count={base.views} hover={HOVER.blue} />
          <div className="flex">
            <Action icon={Bookmark} count={0} hover={HOVER.blue} />
            <Action icon={Share} count={0} hover={HOVER.blue} />
          </div>
        </div>
      </div>
    </article>
  )
}
