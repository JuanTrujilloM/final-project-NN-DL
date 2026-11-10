import { useEffect, useState } from 'react'

const MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sept', 'oct', 'nov', 'dic']

// Relative time in the style of X: "ahora", "45 s", "12 min", "3 h", "9 nov".
export function timeAgo(iso, now = Date.now()) {
  const seconds = Math.max(0, Math.round((now - new Date(iso).getTime()) / 1000))
  if (seconds < 10) return 'ahora'
  if (seconds < 60) return `${seconds} s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)} min`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} h`
  const date = new Date(iso)
  return `${date.getDate()} ${MONTHS[date.getMonth()]}`
}

export function useNow(intervalMs = 15000) {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), intervalMs)
    return () => clearInterval(id)
  }, [intervalMs])
  return now
}

export function hash(text) {
  let h = 0
  for (const char of text) h = (h * 31 + char.charCodeAt(0)) | 0
  return Math.abs(h)
}

const AVATAR_COLORS = ['#1d9bf0', '#f91880', '#00ba7c', '#7856ff', '#ff7a00', '#ffd400', '#00b3ca', '#e0245e']

export function avatarColor(handle) {
  return AVATAR_COLORS[hash(handle) % AVATAR_COLORS.length]
}

export function initials(name) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join('').toUpperCase()
}

export function compactCount(n) {
  if (n >= 1000) return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1).replace('.', ',')} mil`
  return String(n)
}

// Static Tailwind classes per response front (must be literal strings for Tailwind to keep them).
export const GROUP_STYLES = {
  red: { dot: 'bg-red-500', bar: 'bg-red-500', text: 'text-red-700', chip: 'bg-red-50 text-red-700 ring-red-200', soft: 'bg-red-50/60', fill: 'bg-red-500' },
  orange: { dot: 'bg-orange-500', bar: 'bg-orange-500', text: 'text-orange-700', chip: 'bg-orange-50 text-orange-700 ring-orange-200', soft: 'bg-orange-50/60', fill: 'bg-orange-500' },
  amber: { dot: 'bg-amber-500', bar: 'bg-amber-500', text: 'text-amber-700', chip: 'bg-amber-50 text-amber-800 ring-amber-200', soft: 'bg-amber-50/60', fill: 'bg-amber-500' },
  slate: { dot: 'bg-slate-400', bar: 'bg-slate-400', text: 'text-slate-600', chip: 'bg-slate-100 text-slate-700 ring-slate-200', soft: 'bg-slate-50', fill: 'bg-slate-400' },
}
