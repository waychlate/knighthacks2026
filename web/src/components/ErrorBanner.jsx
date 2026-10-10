export default function ErrorBanner({ errors }) {
  const list = errors.filter(Boolean)
  if (list.length === 0) return null
  return (
    <div role="alert" className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
      Something went wrong loading data ({list.join('; ')}). The list below may be empty or out of date. Try refreshing.
    </div>
  )
}
