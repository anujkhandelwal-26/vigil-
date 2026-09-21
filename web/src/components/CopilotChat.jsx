import { useState } from 'react'
import { useCopilotQueryMutation } from '../app/api'

const SUGGESTED = [
  'Why was this flagged?',
  'What changed from this customer\'s normal behavior?',
  'Summarize this case.',
  'Which signals contributed most to the score?',
  'Show me all cases involving this device.',
  'Have we seen a case like this before?',
]

export default function CopilotChat({ applicationId }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [copilotQuery, { isLoading }] = useCopilotQueryMutation()

  async function ask(question) {
    if (!question.trim()) return
    setMessages((m) => [...m, { role: 'user', text: question }])
    setInput('')
    try {
      const res = await copilotQuery({ applicationId, question }).unwrap()
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          text: res.answer,
          grounded: res.grounded,
          intent: res.intent,
          provider: res.provider,
          model: res.model,
          latencyMs: res.latency_ms,
        },
      ])
    } catch (err) {
      setMessages((m) => [...m, { role: 'assistant', text: 'The copilot could not answer that right now.', grounded: false }])
    }
  }

  return (
    <div>
      <div className="chat-log">
        {messages.length === 0 && (
          <span className="faint">Ask about this case — answers are grounded strictly in retrieved case data.</span>
        )}
        {messages.map((m, i) => (
          <div className={`chat-msg ${m.role}`} key={i}>
            {m.text}
            {m.role === 'assistant' && (
              <div style={{ marginTop: 6 }}>
                <span className={`grounded-badge ${m.grounded ? '' : 'fallback'}`}>
                  {m.grounded ? 'grounded ✓' : 'fallback template'} · {m.provider}/{m.model} · {m.latencyMs}ms
                </span>
              </div>
            )}
          </div>
        ))}
        {isLoading && <div className="chat-msg assistant faint">Thinking…</div>}
      </div>
      <div style={{ marginBottom: 8 }}>
        {SUGGESTED.map((q) => (
          <button key={q} className="chip suggested-q" style={{ cursor: 'pointer', border: 'none' }} onClick={() => ask(q)}>
            {q}
          </button>
        ))}
      </div>
      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask(input)}
          placeholder="Ask a question about this case…"
        />
        <button className="secondary" onClick={() => ask(input)} disabled={isLoading}>
          Ask
        </button>
      </div>
    </div>
  )
}
