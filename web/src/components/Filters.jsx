const selectClass =
  'w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm text-stone-800 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500'

export default function Filters({ species, cameras, value, onChange }) {
  const active = value.speciesId || value.cameraId
  return (
    <div className="mb-5 flex flex-wrap items-end gap-3">
      <label className="min-w-40 flex-1 text-xs font-medium text-stone-500">
        Species
        <select
          className={`${selectClass} mt-1`}
          value={value.speciesId}
          onChange={(e) => onChange({ ...value, speciesId: e.target.value })}
        >
          <option value="">All species</option>
          {species.map((s) => (
            <option key={s.id} value={s.id}>
              {s.common_name}
            </option>
          ))}
        </select>
      </label>
      <label className="min-w-40 flex-1 text-xs font-medium text-stone-500">
        Camera
        <select
          className={`${selectClass} mt-1`}
          value={value.cameraId}
          onChange={(e) => onChange({ ...value, cameraId: e.target.value })}
        >
          <option value="">All cameras</option>
          {cameras.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      {active && (
        <button
          type="button"
          onClick={() => onChange({ speciesId: '', cameraId: '' })}
          className="rounded-lg px-3 py-2 text-sm text-stone-600 hover:bg-stone-200"
        >
          Clear
        </button>
      )}
    </div>
  )
}
