import { avatarColor, initials } from '../../lib/format'

export default function Avatar({ name, handle, size = 40 }) {
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-full font-bold text-white"
      style={{ width: size, height: size, background: avatarColor(handle), fontSize: size * 0.36 }}
    >
      {initials(name)}
    </div>
  )
}
