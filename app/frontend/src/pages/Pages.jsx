import { Link } from 'react-router-dom'
import { ArrowRight, Cpu, ExternalLink } from 'lucide-react'
import CenterApp from '../components/center/CenterApp'
import SocialApp from '../components/social/SocialApp'
import Logo from '../components/social/Logo'

export function SocialPage() {
  return <div className="h-dvh" style={{ '--pane-h': '100dvh' }}><SocialApp /></div>
}

export function CenterPage() {
  return <div className="h-dvh"><CenterApp /></div>
}

const BAR_H = 44

// Both platforms side by side: what is posted on the left is cleaned, classified and shown on the right.
export function DemoPage() {
  const paneHeight = `calc(100dvh - ${BAR_H}px)`
  return (
    <div className="flex h-dvh flex-col bg-black">
      <div className="flex shrink-0 items-center gap-3 border-b border-slate-800 bg-slate-950 px-4 text-xs text-slate-300" style={{ height: BAR_H }}>
        <span className="font-semibold text-white">Demo</span>
        <span className="flex items-center gap-1.5"><Logo className="h-4 w-4" /> Red social</span>
        <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
        <span className="flex items-center gap-1.5"><Cpu className="h-3.5 w-3.5" /> limpieza + modelo</span>
        <ArrowRight className="h-3.5 w-3.5 text-slate-500" />
        <span>Centro de información</span>
        <div className="ml-auto flex gap-1">
          <Link to="/red" target="_blank" className="flex items-center gap-1 rounded-md px-2 py-1 hover:bg-slate-800">Red social <ExternalLink className="h-3 w-3" /></Link>
          <Link to="/centro" target="_blank" className="flex items-center gap-1 rounded-md px-2 py-1 hover:bg-slate-800">Centro <ExternalLink className="h-3 w-3" /></Link>
        </div>
      </div>
      <div className="flex min-h-0 flex-1">
        <div className="w-[38%] min-w-[420px] shrink-0 border-r border-slate-800" style={{ '--pane-h': paneHeight }}>
          <SocialApp compact />
        </div>
        <div className="min-w-0 flex-1">
          <CenterApp compact />
        </div>
      </div>
    </div>
  )
}
