import { Component } from 'react'

// Last resort: if something throws while rendering, show a message and a reload button instead of a blank screen.
export default class ErrorBoundary extends Component {
  state = { error: null }
  static getDerivedStateFromError(error) {
    return { error }
  }
  componentDidCatch(error) {
    console.error('App crashed:', error)
  }
  render() {
    if (!this.state.error) return this.props.children
    return (
      <div role="alert" className="mx-auto max-w-md p-6 text-center" style={{ color: '#edf5df', background: '#10251a', minHeight: '100vh' }}>
        <h1 className="text-xl font-bold">Something went wrong</h1>
        <p className="mt-2 text-sm opacity-80">{String(this.state.error?.message ?? this.state.error)}</p>
        <button type="button" onClick={() => window.location.reload()} className="mt-4 rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white">Reload</button>
      </div>
    )
  }
}
