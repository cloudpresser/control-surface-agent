'use client'

import { useEffect, useMemo, useState } from 'react'

import { api } from '../lib/api'

type Example = {
  id: string
  label: string
  company_name: string
  profile_id: string
  description: string
  job_description: string
}

type RunState = {
  run_id: string
  status: string
  input: {
    example_id?: string
    company_name: string
    job_description: string
    profile_id: string
    constraints: string[]
  }
  intent?: Record<string, unknown>
  plan?: { steps: Array<Record<string, unknown>>; needs_retrieval: boolean; assumptions: string[]; confidence: number }
  current_step_id?: string | null
  evidence: Array<Record<string, unknown>>
  telemetry: Array<Record<string, unknown>>
  reconciliation_reports: Array<Record<string, unknown>>
  operator_actions: Array<Record<string, unknown>>
  artifact?: Record<string, unknown> | null
  confidence: number
}

const defaultForm = {
  example_id: 'stripe_em_dev_productivity_ai',
  company_name: 'Stripe',
  profile_id: 'luiz_default',
  job_description:
    'Engineering Manager, Developer Productivity AI. Remote US. Compensation $214,600 - $321,800. Lead a new team focused on LLM agents for engineering workflow automation and transform how engineers work.',
  constraints: 'optimize for long-term growth\navoid generic advice',
}

export default function Home() {
  const [examples, setExamples] = useState<Example[]>([])
  const [form, setForm] = useState(defaultForm)
  const [runState, setRunState] = useState<RunState | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedbackNote, setFeedbackNote] = useState('Need more evidence before locking the verdict.')
  const [feedbackAction, setFeedbackAction] = useState('force_retrieval')

  useEffect(() => {
    api<Example[]>('/examples')
      .then(setExamples)
      .catch((err) => setError(err.message))
  }, [])

  const latestReconciliation = useMemo(() => {
    if (!runState?.reconciliation_reports?.length) return null
    return runState.reconciliation_reports[runState.reconciliation_reports.length - 1]
  }, [runState])

  async function createRun() {
    setLoading(true)
    setError(null)
    try {
      const payload = {
        example_id: form.example_id,
        company_name: form.company_name,
        profile_id: form.profile_id,
        job_description: form.job_description,
        constraints: form.constraints
          .split('\n')
          .map((item) => item.trim())
          .filter(Boolean),
      }
      const response = await api<{ run_state: RunState }>('/runs', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
      setRunState(response.run_state)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create run')
    } finally {
      setLoading(false)
    }
  }

  async function execute(mode: 'next' | 'all') {
    if (!runState) {
      await createRun()
      return
    }
    setLoading(true)
    setError(null)
    try {
      const response = await api<RunState>(`/runs/${runState.run_id}/execute`, {
        method: 'POST',
        body: JSON.stringify({ mode }),
      })
      setRunState(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute run')
    } finally {
      setLoading(false)
    }
  }

  async function sendFeedback() {
    if (!runState) return
    setLoading(true)
    setError(null)
    try {
      const response = await api<RunState>(`/runs/${runState.run_id}/feedback`, {
        method: 'POST',
        body: JSON.stringify({
          action: feedbackAction,
          payload: feedbackAction === 'retry_with_constraint' ? { constraint: feedbackNote } : {},
          feedback: {
            target: 'plan_step',
            target_id: 'step_retrieve_context',
            feedback_type: 'missing_evidence',
            note: feedbackNote,
          },
        }),
      })
      setRunState(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send feedback')
    } finally {
      setLoading(false)
    }
  }

  function loadExample(exampleId: string) {
    const selected = examples.find((example) => example.id === exampleId)
    setForm((current) => ({
      ...current,
      example_id: exampleId,
      company_name: selected?.company_name ?? current.company_name,
      job_description: selected?.job_description ?? current.job_description,
      profile_id: selected?.profile_id ?? current.profile_id,
    }))
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">control-surface-agent</p>
          <h1>Supervised AI decision workflows as a control system.</h1>
          <p className="hero-copy">
            This operator console exposes intent, plan, telemetry, reconciliation, and human intervention.
            The example domain is opportunity evaluation. The product is the supervision architecture.
          </p>
        </div>
        <div className="hero-metrics panel compact">
          <div>
            <span>Status</span>
            <strong>{runState?.status ?? 'idle'}</strong>
          </div>
          <div>
            <span>Confidence</span>
            <strong>{runState ? runState.confidence.toFixed(2) : '0.00'}</strong>
          </div>
          <div>
            <span>Current step</span>
            <strong>{runState?.current_step_id ?? 'not started'}</strong>
          </div>
        </div>
      </section>

      <section className="grid-layout">
        <div className="column column-left">
          <Panel title="Inputs">
            <label>
              Bundled example
              <select value={form.example_id} onChange={(event) => loadExample(event.target.value)}>
                {examples.map((example) => (
                  <option key={example.id} value={example.id}>
                    {example.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Company name
              <input value={form.company_name} onChange={(event) => setForm({ ...form, company_name: event.target.value })} />
            </label>
            <label>
              Job description
              <textarea
                rows={10}
                value={form.job_description}
                onChange={(event) => setForm({ ...form, job_description: event.target.value })}
              />
            </label>
            <label>
              Constraints
              <textarea rows={5} value={form.constraints} onChange={(event) => setForm({ ...form, constraints: event.target.value })} />
            </label>
            <div className="button-row">
              <button onClick={createRun} disabled={loading}>
                Initialize Run
              </button>
              <button onClick={() => execute('all')} disabled={loading}>
                Run All
              </button>
              <button onClick={() => execute('next')} disabled={loading}>
                Execute Next Step
              </button>
            </div>
            {error ? <p className="error-text">{error}</p> : null}
          </Panel>

          <Panel title="Intent">
            {runState?.intent ? <IntentSummary intent={runState.intent} /> : <EmptyState message="Intent appears after initialization." />}
          </Panel>

          <Panel title="Plan">
            <div className="stacked-list">
              {runState?.plan?.steps?.map((step) => (
                <div className="list-item" key={String(step.id)}>
                  <strong>{String(step.label)}</strong>
                  <span>{String(step.status)}</span>
                </div>
              )) ?? <EmptyState message="Initialize a run to materialize the execution plan." />}
            </div>
          </Panel>
        </div>

        <div className="column column-center">
          <Panel title="Reconciliation" highlight>
            {latestReconciliation ? (
              <div className="reconciliation-card">
                <div className="pill-row">
                  <span className="pill">scope: {String(latestReconciliation.scope)}</span>
                  <span className="pill">alignment: {String(latestReconciliation.intent_alignment)}</span>
                  <span className="pill">coverage: {String(latestReconciliation.evidence_coverage)}</span>
                </div>
                <p>{String(latestReconciliation.summary)}</p>
                <p>
                  <strong>Recommended action:</strong> {String(latestReconciliation.recommended_action ?? 'none')}
                </p>
                <p>
                  <strong>Unknowns:</strong>{' '}
                  {Array.isArray(latestReconciliation.unknowns_detected)
                    ? latestReconciliation.unknowns_detected.join(', ') || 'none'
                    : 'none'}
                </p>
              </div>
            ) : (
              <EmptyState message="Reconciliation becomes active after the first executed step." />
            )}
          </Panel>

          <Panel title="Telemetry">
            <div className="table-shell">
              <table>
                <thead>
                  <tr>
                    <th>Step</th>
                    <th>Action</th>
                    <th>Status</th>
                    <th>Summary</th>
                    <th>Delta</th>
                  </tr>
                </thead>
                <tbody>
                  {runState?.telemetry?.length ? (
                    runState.telemetry.map((event, index) => {
                      const before = Number(event.confidence_before ?? 0)
                      const after = Number(event.confidence_after ?? 0)
                      const delta = (after - before).toFixed(2)
                      return (
                        <tr key={`${event.step_id}-${index}`}>
                          <td>{String(event.step_id)}</td>
                          <td>{String(event.action)}</td>
                          <td>{String(event.status)}</td>
                          <td>{String(event.summary)}</td>
                          <td>{delta}</td>
                        </tr>
                      )
                    })
                  ) : (
                    <tr>
                      <td colSpan={5}>
                        <EmptyState message="Telemetry appears as the workflow executes." />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </Panel>

          <Panel title="Evidence">
            <div className="stacked-list">
              {runState?.evidence?.length ? (
                runState.evidence.map((item) => (
                  <div className="evidence-card" key={String(item.id)}>
                    <div className="evidence-header">
                      <strong>{String(item.title)}</strong>
                      <span>{String(item.id)}</span>
                    </div>
                    <p>{String(item.summary)}</p>
                    <p>
                      <strong>Purpose:</strong> {String(item.purpose)}
                    </p>
                  </div>
                ))
              ) : (
                <EmptyState message="No evidence collected yet." />
              )}
            </div>
          </Panel>
        </div>

        <div className="column column-right">
          <Panel title="Decision Artifact">
            {runState?.artifact ? <ArtifactSummary artifact={runState.artifact} /> : <EmptyState message="The final artifact appears after the output step completes." />}
          </Panel>

          <Panel title="Operator Controls" testId="operator-controls-panel">
            <label>
              Action
              <select value={feedbackAction} onChange={(event) => setFeedbackAction(event.target.value)}>
                <option value="force_retrieval">force_retrieval</option>
                <option value="retry_with_constraint">retry_with_constraint</option>
                <option value="approve_step">approve_step</option>
                <option value="reject_step">reject_step</option>
                <option value="escalate">escalate</option>
              </select>
            </label>
            <label>
              Note
              <textarea rows={4} value={feedbackNote} onChange={(event) => setFeedbackNote(event.target.value)} />
            </label>
            <div className="button-row">
              <button onClick={sendFeedback} disabled={loading || !runState}>
                Apply Feedback
              </button>
              <button onClick={() => execute('all')} disabled={loading || !runState}>
                Re-run
              </button>
            </div>
            <div className="stacked-list">
              {runState?.operator_actions?.length ? (
                runState.operator_actions.map((action, index) => (
                  <div className="list-item" key={`${action.action}-${index}`}>
                    <strong>{String(action.action)}</strong>
                    <span>{String(action.timestamp)}</span>
                  </div>
                ))
              ) : (
                <EmptyState message="No operator actions recorded yet." />
              )}
            </div>
          </Panel>
        </div>
      </section>
    </main>
  )
}

function IntentSummary({ intent }: { intent: Record<string, unknown> }) {
  return (
    <div className="structured-card">
      <Row label="Intent" value={String(intent.intent ?? 'unknown')} />
      <Row label="Objective" value={String(intent.objective ?? 'unknown')} />
      <TagBlock label="Constraints" items={toStringArray(intent.constraints)} />
      <TagBlock label="Success Criteria" items={toStringArray(intent.success_criteria)} />
      <TagBlock label="Missing Information" items={toStringArray(intent.missing_information)} />
    </div>
  )
}

function ArtifactSummary({ artifact }: { artifact: Record<string, unknown> }) {
  const reasoning = Array.isArray(artifact.reasoning) ? artifact.reasoning : []

  return (
    <div className="structured-card">
      <Row label="Verdict" value={String(artifact.verdict ?? 'unknown')} />
      <Row label="Confidence" value={String(artifact.confidence ?? '0.00')} />
      <SectionTitle title="Reasoning" />
      <div className="stacked-list compact-list">
        {reasoning.map((item, index) => {
          const claim = item as { claim?: string; evidence_ids?: string[] }
          return (
            <div className="list-item tall" key={`${claim.claim ?? 'claim'}-${index}`}>
              <div>
                <strong>{claim.claim ?? 'Unnamed claim'}</strong>
                <span>{(claim.evidence_ids ?? []).join(', ')}</span>
              </div>
            </div>
          )
        })}
      </div>
      <TagBlock label="Risks" items={toStringArray(artifact.risks)} />
      <TagBlock label="Unknowns" items={toStringArray(artifact.unknowns)} />
      <TagBlock label="Next Actions" items={toStringArray(artifact.next_actions)} />
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="detail-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function SectionTitle({ title }: { title: string }) {
  return <h3 className="section-title">{title}</h3>
}

function TagBlock({ label, items }: { label: string; items: string[] }) {
  return (
    <div className="tag-block">
      <span>{label}</span>
      <div className="pill-row">
        {items.length ? items.map((item) => <span className="pill" key={item}>{item}</span>) : <span className="pill muted-pill">none</span>}
      </div>
    </div>
  )
}

function toStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)) : []
}

function Panel({ title, children, highlight = false, compact = false, testId }: { title: string; children: React.ReactNode; highlight?: boolean; compact?: boolean; testId?: string }) {
  return (
    <section data-testid={testId} className={`panel ${highlight ? 'panel-highlight' : ''} ${compact ? 'compact' : ''}`}>
      <div className="panel-header">
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  )
}

function EmptyState({ message }: { message: string }) {
  return <p className="empty-state">{message}</p>
}
