'use client'

import type { ButtonHTMLAttributes, ReactNode } from 'react'
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

type Health = {
  status: string
  model: string
  agent_mode: string
}

type Usage = {
  model: string
  agent_mode: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  latency_ms: number
}

type PlanStep = {
  id: string
  label: string
  status: string
  notes?: string | null
}

type TelemetryEvent = {
  step_id: string
  action: string
  status: string
  summary: string
  confidence_before: number
  confidence_after: number
  evidence_ids?: string[]
  usage?: Usage | null
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
  plan?: { steps: PlanStep[]; needs_retrieval: boolean; assumptions: string[]; confidence: number }
  current_step_id?: string | null
  evidence: Array<Record<string, unknown>>
  telemetry: TelemetryEvent[]
  reconciliation_reports: Array<Record<string, unknown>>
  operator_actions: Array<Record<string, unknown>>
  artifact?: Record<string, unknown> | null
  artifacts_by_step?: Record<string, Record<string, unknown>>
  confidence: number
  usage_summary?: Usage | null
}

const defaultForm = {
  example_id: 'stripe_em_dev_productivity_ai',
  company_name: 'Stripe',
  profile_id: 'luiz_default',
  job_description:
    'Engineering Manager, Developer Productivity AI. Remote US. Compensation $214,600 - $321,800. Lead a new team focused on LLM agents for engineering workflow automation and transform how engineers work.',
  constraints: 'optimize for long-term growth\navoid generic advice',
}

const planSkeleton: PlanStep[] = [
  { id: 'step_extract_requirements', label: 'Extract role requirements', status: 'pending' },
  { id: 'step_retrieve_context', label: 'Retrieve company context', status: 'pending' },
  { id: 'step_compare_fit', label: 'Compare role to profile', status: 'pending' },
  { id: 'step_assess_unknowns', label: 'Assess risks and unknowns', status: 'pending' },
  { id: 'step_generate_artifact', label: 'Generate structured artifact', status: 'pending' },
]

export default function Home() {
  const [examples, setExamples] = useState<Example[]>([])
  const [form, setForm] = useState(defaultForm)
  const [runState, setRunState] = useState<RunState | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  const [feedbackNote, setFeedbackNote] = useState('Need more evidence before locking the verdict.')
  const [feedbackAction, setFeedbackAction] = useState('force_retrieval')
  const [traceExpanded, setTraceExpanded] = useState(false)
  const [expandedTraceRows, setExpandedTraceRows] = useState<string[]>([])
  const [expandedArtifactSections, setExpandedArtifactSections] = useState<string[]>([])
  const [expandedReconciliation, setExpandedReconciliation] = useState(false)
  const [activeAction, setActiveAction] = useState<string | null>(null)
  const [requestStartedAt, setRequestStartedAt] = useState<number | null>(null)

  useEffect(() => {
    api<Example[]>('/examples')
      .then(setExamples)
      .catch((err) => setError(err.message))

    api<Health>('/health')
      .then(setHealth)
      .catch((err) => setError(err.message))
  }, [])

  const latestReconciliation = useMemo(() => {
    if (!runState?.reconciliation_reports?.length) return null
    return runState.reconciliation_reports[runState.reconciliation_reports.length - 1]
  }, [runState])

  const hasRun = Boolean(runState)
  const elapsedMs = useElapsed(requestStartedAt, loading)
  const planSteps = useMemo(() => {
    if (runState?.plan?.steps?.length) return runState.plan.steps
    if (hasRun) return planSkeleton
    return []
  }, [hasRun, runState])

  const inputsSummary = runState?.input
    ? {
        exampleId: runState.input.example_id ?? form.example_id,
        companyName: runState.input.company_name,
        jobDescription: runState.input.job_description,
        constraints: runState.input.constraints,
      }
    : {
        exampleId: form.example_id,
        companyName: form.company_name,
        jobDescription: form.job_description,
        constraints: form.constraints.split('\n').map((item) => item.trim()).filter(Boolean),
      }

  const traceSummary = runState?.telemetry?.length
    ? {
        steps: runState.telemetry.length,
        lastAction: runState.telemetry[runState.telemetry.length - 1].action,
        totalTokens: runState.usage_summary?.total_tokens ?? 0,
        latency: runState.usage_summary?.latency_ms ?? 0,
      }
    : null

  async function createRun() {
    setActiveAction('initialize')
    setRequestStartedAt(Date.now())
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
      setActiveAction(null)
      setRequestStartedAt(null)
    }
  }

  async function execute(mode: 'next' | 'all') {
    if (!runState) {
      await createRun()
      return
    }
    setActiveAction(mode === 'all' ? 'run-all' : 'run-next')
    setRequestStartedAt(Date.now())
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
      setActiveAction(null)
      setRequestStartedAt(null)
    }
  }

  async function sendFeedback() {
    if (!runState) return
    setActiveAction('apply-feedback')
    setRequestStartedAt(Date.now())
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
      setActiveAction(null)
      setRequestStartedAt(null)
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

  function resetSetup() {
    setRunState(null)
    setError(null)
    setFeedbackAction('force_retrieval')
    setFeedbackNote('Need more evidence before locking the verdict.')
    setTraceExpanded(false)
    setExpandedTraceRows([])
    setExpandedArtifactSections([])
    setExpandedReconciliation(false)
    setActiveAction(null)
    setRequestStartedAt(null)
  }

  function toggleTraceRow(rowId: string) {
    setExpandedTraceRows((current) =>
      current.includes(rowId) ? current.filter((id) => id !== rowId) : [...current, rowId],
    )
  }

  function toggleArtifactSection(section: string) {
    setExpandedArtifactSections((current) =>
      current.includes(section) ? current.filter((item) => item !== section) : [...current, section],
    )
  }

  function applyRecommendedAction() {
    const action = String(latestReconciliation?.recommended_action ?? '').trim()
    if (!action) return
    setFeedbackAction(action)
    setFeedbackNote(`Apply reconciliation recommendation: ${action}`)
    document.getElementById('operator-controls-anchor')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  const recommendedAction = String(latestReconciliation?.recommended_action ?? '').trim()
  const activePhaseLabel = runState?.status === 'in_progress' ? `Running ${runState.current_step_id ?? 'workflow'} · elapsed ${formatDuration(elapsedMs)}` : null

  return (
    <main className="page-shell">
      {activePhaseLabel ? (
        <section className="activity-strip">
          <span className="activity-dot" />
          <strong>{activePhaseLabel}</strong>
        </section>
      ) : null}
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
          <div>
            <span>Agent mode</span>
            <strong>{runState?.usage_summary?.agent_mode ?? health?.agent_mode ?? 'unknown'}</strong>
          </div>
          <div>
            <span>Model</span>
            <strong>{runState?.usage_summary?.model ?? health?.model ?? 'unknown'}</strong>
          </div>
          <div>
            <span>Total tokens</span>
            <strong>{runState?.usage_summary?.total_tokens ?? 0}</strong>
          </div>
          <div>
            <span>Latency</span>
            <strong>{runState?.usage_summary ? `${runState.usage_summary.latency_ms} ms` : '0 ms'}</strong>
          </div>
        </div>
      </section>

      <section className="grid-layout">
        <div className="column column-left">
          <Panel title="Inputs" testId="inputs-panel">
            {hasRun ? (
              <div className="structured-card">
                <Row label="Bundled Example" value={labelForExample(examples, inputsSummary.exampleId)} />
                <Row label="Company" value={inputsSummary.companyName} />
                <SectionTitle title="Job Description" />
                <div className="read-only-block">{inputsSummary.jobDescription}</div>
                <TagBlock label="Constraints" items={inputsSummary.constraints} />
                <div className="button-row top-space">
                  <button className="button-secondary" onClick={resetSetup} disabled={loading}>
                    Reset Setup
                  </button>
                </div>
              </div>
            ) : (
              <>
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
                </div>
              </>
            )}
            {error ? <p className="error-text">{error}</p> : null}
          </Panel>

          <Panel title="Operator Controls" testId="operator-controls-panel">
            <div id="operator-controls-anchor" />
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
              <ActionButton onClick={sendFeedback} disabled={loading || !runState} loading={loading && activeAction === 'apply-feedback'}>
                Apply Feedback
              </ActionButton>
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

        <div className="column column-center">
          <Panel
            title="Plan"
            testId="plan-panel"
            highlight={runState?.status === 'in_progress'}
            actions={
              <div className="button-row plan-actions">
                <ActionButton onClick={() => execute('all')} disabled={loading || !runState} loading={loading && activeAction === 'run-all'}>
                  Run All
                </ActionButton>
                <ActionButton className="button-secondary" onClick={() => execute('next')} disabled={loading || !runState} loading={loading && activeAction === 'run-next'}>
                  Execute Next Step
                </ActionButton>
                <ActionButton className="button-secondary" onClick={() => execute('all')} disabled={loading || !runState} loading={false}>
                  Re-run
                </ActionButton>
              </div>
            }
          >
            <div className={`plan-shell ${runState?.status === 'in_progress' ? 'plan-shell-active' : ''}`}>
              {planSteps.length ? (
                <div className="stacked-list plan-list">
                  {planSteps.map((step) => {
                    const status = normalizeStepStatus(step.status)
                    const isCurrent = runState?.current_step_id === step.id
                    return (
                      <div className={`plan-step plan-step-${status} ${isCurrent ? 'plan-step-current' : ''}`} key={step.id}>
                        <div className="plan-step-main">
                          <strong>{step.label}</strong>
                          <span className={`status-badge status-${status}`}>
                            {status === 'in_progress' ? <span className="spinner-inline" aria-hidden="true" /> : null}
                            {status.replace('_', ' ')}
                          </span>
                        </div>
                        {step.notes ? <p className="plan-step-notes">{step.notes}</p> : null}
                      </div>
                    )
                  })}
                </div>
              ) : (
                <EmptyState message="Initialize a run to materialize the execution plan." />
              )}
            </div>
          </Panel>

          <Panel title="Reconciliation" highlight>
            {latestReconciliation ? (
              <div className="reconciliation-card">
                {recommendedAction ? (
                  <div className={`reconciliation-banner reconciliation-banner-${actionTone(recommendedAction)}`}>
                    <div>
                      <span>Recommended action</span>
                      <strong>{recommendedAction}</strong>
                    </div>
                    <button className="button-secondary" onClick={applyRecommendedAction}>
                      Apply Recommended Action
                    </button>
                  </div>
                ) : null}
                <div className="pill-row">
                  <span className="pill">scope: {String(latestReconciliation.scope)}</span>
                  <span className={`pill pill-tone-${toneForValue(String(latestReconciliation.intent_alignment))}`}>alignment: {String(latestReconciliation.intent_alignment)}</span>
                  <span className={`pill pill-tone-${toneForValue(String(latestReconciliation.evidence_coverage))}`}>coverage: {String(latestReconciliation.evidence_coverage)}</span>
                </div>
                <p className="reconciliation-summary">{shortSummary(String(latestReconciliation.summary ?? ''))}</p>
                <div className="reconciliation-unknowns">
                  <strong>Unknowns</strong>
                  <ul>
                    {toStringArray(latestReconciliation.unknowns_detected).slice(0, expandedReconciliation ? undefined : 4).map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
                <button className="button-secondary" onClick={() => setExpandedReconciliation((current) => !current)}>
                  {expandedReconciliation ? 'Hide Full Reconciliation' : 'Show Full Reconciliation'}
                </button>
                {expandedReconciliation ? <div className="reconciliation-fulltext">{String(latestReconciliation.summary)}</div> : null}
              </div>
            ) : (
              <EmptyState message="Reconciliation becomes active after the first executed step." />
            )}
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
          <Panel title="Decision Artifact" testId="artifact-panel">
            {runState?.artifact ? (
              <ArtifactSummary
                artifact={runState.artifact}
                expandedSections={expandedArtifactSections}
                onToggleSection={toggleArtifactSection}
              />
            ) : (
              <EmptyState message="The final artifact appears after the output step completes." />
            )}
          </Panel>

          <Panel title="Intent">
            {runState?.intent ? <IntentSummary intent={runState.intent} /> : <EmptyState message="Intent appears after initialization." />}
          </Panel>
        </div>
      </section>

      <section className="telemetry-section">
        <Panel
          title="Telemetry"
          testId="telemetry-panel"
          actions={
            <div className="telemetry-summary-row">
              <span>{traceSummary ? `${traceSummary.steps} events` : '0 events'}</span>
              <span>{traceSummary ? `last action: ${traceSummary.lastAction}` : 'trace idle'}</span>
              <span>{traceSummary ? `${traceSummary.totalTokens} tokens` : '0 tokens'}</span>
              <span>{traceSummary ? `${traceSummary.latency} ms` : '0 ms'}</span>
              <button className="button-secondary" onClick={() => setTraceExpanded((current) => !current)}>
                {traceExpanded ? 'Collapse Trace' : 'Expand Trace'}
              </button>
            </div>
          }
        >
          {traceExpanded ? (
            <div className="table-shell">
              <table>
                <thead>
                  <tr>
                    <th>Step</th>
                    <th>Action</th>
                    <th>Status</th>
                    <th>Summary</th>
                    <th>Delta</th>
                    <th>Model</th>
                    <th>Tokens</th>
                    <th>Latency</th>
                    <th>Trace</th>
                  </tr>
                </thead>
                <tbody>
                  {runState?.telemetry?.length ? (
                    runState.telemetry.flatMap((event, index) => {
                      const before = Number(event.confidence_before ?? 0)
                      const after = Number(event.confidence_after ?? 0)
                      const delta = (after - before).toFixed(2)
                      const usage = event.usage ?? null
                      const rowId = `${event.step_id}-${index}`
                      const expanded = expandedTraceRows.includes(rowId)

                      return [
                        <tr key={rowId}>
                          <td>{String(event.step_id)}</td>
                          <td>{String(event.action)}</td>
                          <td>
                            <span className={`status-badge status-${normalizeStepStatus(event.status)}`}>{String(event.status)}</span>
                          </td>
                          <td>{String(event.summary)}</td>
                          <td>{delta}</td>
                          <td>{usage?.model ?? 'n/a'}</td>
                          <td>{usage?.total_tokens ?? 0}</td>
                          <td>{usage ? `${usage.latency_ms} ms` : '0 ms'}</td>
                          <td>
                            <button className="button-inline" onClick={() => toggleTraceRow(rowId)}>
                              {expanded ? 'Hide' : 'View'}
                            </button>
                          </td>
                        </tr>,
                        expanded ? (
                          <tr className="trace-details-row" key={`${rowId}-details`}>
                            <td colSpan={9}>
                              <div className="trace-details-grid">
                                <div>
                                  <span>Confidence Before</span>
                                  <strong>{before.toFixed(2)}</strong>
                                </div>
                                <div>
                                  <span>Confidence After</span>
                                  <strong>{after.toFixed(2)}</strong>
                                </div>
                                <div>
                                  <span>Evidence IDs</span>
                                  <strong>{event.evidence_ids?.length ? event.evidence_ids.join(', ') : 'none'}</strong>
                                </div>
                                <div>
                                  <span>Prompt Tokens</span>
                                  <strong>{usage?.prompt_tokens ?? 0}</strong>
                                </div>
                                <div>
                                  <span>Completion Tokens</span>
                                  <strong>{usage?.completion_tokens ?? 0}</strong>
                                </div>
                                <div>
                                  <span>Agent Mode</span>
                                  <strong>{usage?.agent_mode ?? health?.agent_mode ?? 'unknown'}</strong>
                                </div>
                                <div>
                                  <span>Latency Share</span>
                                  <div className="latency-bar-shell">
                                    <div
                                      className={`latency-bar latency-bar-${normalizeStepStatus(event.status)}`}
                                      style={{ width: `${latencyWidthPercent(usage?.latency_ms ?? 0, runState?.usage_summary?.latency_ms ?? 0)}%` }}
                                    />
                                  </div>
                                </div>
                                <div className="trace-details-summary">
                                  <span>Event Summary</span>
                                  <strong>{String(event.summary)}</strong>
                                </div>
                                <div className="trace-details-summary">
                                  <span>Payload Preview</span>
                                  <pre className="payload-preview">{formatPayloadPreview(runState?.artifacts_by_step?.[event.step_id])}</pre>
                                </div>
                              </div>
                            </td>
                          </tr>
                        ) : null,
                      ]
                    })
                  ) : (
                    <tr>
                      <td colSpan={9}>
                        <EmptyState message="Telemetry appears as the workflow executes." />
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState message="Expand the trace to inspect per-step telemetry, usage, evidence refs, and confidence transitions." />
          )}
        </Panel>
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

function ArtifactSummary({
  artifact,
  expandedSections,
  onToggleSection,
}: {
  artifact: Record<string, unknown>
  expandedSections: string[]
  onToggleSection: (section: string) => void
}) {
  const reasoning = Array.isArray(artifact.reasoning) ? artifact.reasoning : []
  const verdict = String(artifact.verdict ?? 'unknown')
  const visibleReasoning = expandedSections.includes('reasoning') ? reasoning : reasoning.slice(0, 2)
  const risks = toStringArray(artifact.risks)
  const unknowns = toStringArray(artifact.unknowns)
  const nextActions = toStringArray(artifact.next_actions)

  return (
    <div className="structured-card">
      <div className={`artifact-hero artifact-hero-${artifactVerdictTone(verdict)}`}>
        <div>
          <span>Verdict</span>
          <strong>{verdict}</strong>
        </div>
        <div>
          <span>Confidence</span>
          <strong>{String(artifact.confidence ?? '0.00')}</strong>
          <div className="confidence-bar-shell">
            <div className="confidence-bar" style={{ width: `${Math.min(Number(artifact.confidence ?? 0) * 100, 100)}%` }} />
          </div>
        </div>
      </div>
      <SectionTitle title="Reasoning" />
      <div className="stacked-list compact-list">
        {visibleReasoning.map((item, index) => {
          const claim = item as { claim?: string; evidence_ids?: string[] }
          return (
            <div className="list-item tall" key={`${claim.claim ?? 'claim'}-${index}`}>
              <div>
                <strong>{claim.claim ?? 'Unnamed claim'}</strong>
                <div className="pill-row compact-pills">
                  {(claim.evidence_ids ?? []).map((evidenceId) => (
                    <span className="pill" key={evidenceId}>{evidenceId}</span>
                  ))}
                </div>
              </div>
            </div>
          )
        })}
      </div>
      {reasoning.length > 2 ? (
        <button className="button-secondary" onClick={() => onToggleSection('reasoning')}>
          {expandedSections.includes('reasoning') ? 'Show Fewer Reasoning Claims' : `Show All ${reasoning.length} Claims`}
        </button>
      ) : null}
      <TagBlock
        label="Risks"
        items={expandedSections.includes('risks') ? risks : risks.slice(0, 3)}
        extraCount={Math.max(risks.length - 3, 0)}
        onToggle={risks.length > 3 ? () => onToggleSection('risks') : undefined}
        expanded={expandedSections.includes('risks')}
      />
      <TagBlock
        label="Unknowns"
        items={expandedSections.includes('unknowns') ? unknowns : unknowns.slice(0, 3)}
        extraCount={Math.max(unknowns.length - 3, 0)}
        onToggle={unknowns.length > 3 ? () => onToggleSection('unknowns') : undefined}
        expanded={expandedSections.includes('unknowns')}
      />
      <TagBlock label="Next Actions" items={nextActions} />
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

function TagBlock({
  label,
  items,
  extraCount = 0,
  onToggle,
  expanded = false,
}: {
  label: string
  items: string[]
  extraCount?: number
  onToggle?: () => void
  expanded?: boolean
}) {
  return (
    <div className="tag-block">
      <span>{label}</span>
      <div className="pill-row">
        {items.length ? items.map((item) => <span className="pill" key={item}>{item}</span>) : <span className="pill muted-pill">none</span>}
      </div>
      {onToggle ? (
        <button className="button-inline" onClick={onToggle}>
          {expanded ? `Show Fewer ${label}` : `Show ${extraCount} More`}
        </button>
      ) : null}
    </div>
  )
}

function ActionButton({
  children,
  loading,
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean }) {
  return (
    <button className={className} {...props}>
      {loading ? <span className="spinner-inline" aria-hidden="true" /> : null}
      {children}
    </button>
  )
}

function EmptyState({ message }: { message: string }) {
  return <p className="empty-state">{message}</p>
}

function Panel({
  title,
  children,
  highlight = false,
  compact = false,
  testId,
  actions,
}: {
  title: string
  children: ReactNode
  highlight?: boolean
  compact?: boolean
  testId?: string
  actions?: ReactNode
}) {
  return (
    <section data-testid={testId} className={`panel ${highlight ? 'panel-highlight' : ''} ${compact ? 'compact' : ''}`}>
      <div className="panel-header">
        <h2>{title}</h2>
        {actions ? <div className="panel-actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  )
}

function normalizeStepStatus(status: string | undefined) {
  if (!status) return 'pending'
  if (status === 'in_progress') return 'in_progress'
  if (status === 'completed') return 'completed'
  if (status === 'failed') return 'failed'
  if (status === 'skipped') return 'skipped'
  return 'pending'
}

function labelForExample(examples: Example[], exampleId: string) {
  return examples.find((example) => example.id === exampleId)?.label ?? exampleId
}

function toStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item)) : []
}

function formatDuration(ms: number) {
  const totalSeconds = Math.floor(ms / 1000)
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, '0')
  const seconds = String(totalSeconds % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
}

function useElapsed(startedAt: number | null, active: boolean) {
  const [now, setNow] = useState(0)

  useEffect(() => {
    if (!startedAt || !active) return
    const id = window.setInterval(() => setNow(Date.now()), 250)
    return () => window.clearInterval(id)
  }, [active, startedAt])

  return startedAt && active ? Math.max(0, now - startedAt) : 0
}

function actionTone(action: string) {
  if (action === 'approve_step') return 'success'
  if (action === 'escalate') return 'danger'
  return 'warning'
}

function toneForValue(value: string) {
  if (value === 'strong' || value === 'sufficient') return 'success'
  if (value === 'partial') return 'warning'
  return 'danger'
}

function artifactVerdictTone(value: string) {
  if (value === 'pursue') return 'success'
  if (value === 'conditionally_pursue') return 'accent'
  return 'warning'
}

function shortSummary(summary: string) {
  const trimmed = summary.trim()
  const sentences = trimmed.split(/(?<=[.!?])\s+/)
  return sentences.slice(0, 2).join(' ')
}

function latencyWidthPercent(latencyMs: number, totalLatencyMs: number) {
  if (!totalLatencyMs) return 0
  return Math.max(6, Math.min(100, (latencyMs / totalLatencyMs) * 100))
}

function formatPayloadPreview(payload: Record<string, unknown> | undefined) {
  if (!payload) return 'No payload recorded for this step.'
  return JSON.stringify(payload, null, 2)
}
