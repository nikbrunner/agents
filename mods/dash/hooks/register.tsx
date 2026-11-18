import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register, RenderChildren, ResolveInput, SessionUsage } from 'claude-code'

import type { Agent, Task, Usage } from '../types'
import { bar, clip, describeCall, editDelta, duration, heat, oneLine, parseGit, planName, prettyModel, until } from './lib'

const CACHE_TTL_MS = 60 * 60 * 1000
const MODEL = 'haiku'
const PANE = 'dash'
const SUMMARY_INTERVAL_MS = 10_000

const git = atom({ plugin: 'dash', key: 'git' } as const, null)
const agent = atom({ plugin: 'dash', key: 'agent' } as const, {
  model: '',
})
const title = atom({ plugin: 'dash', key: 'title' } as const, '')
const tasks = atom({ plugin: 'dash', key: 'tasks' } as const, [])
const usage = atom({ plugin: 'dash', key: 'usage' } as const, {
  limits: [],
})
const cache = atom({ plugin: 'dash', key: 'cache' } as const, {
  misses: 0,
})
const lines = atom({ plugin: 'dash', key: 'lines' } as const, {
  added: 0,
  removed: 0,
})
const tick = atom({ plugin: 'dash', key: 'tick' } as const, 0)
const thread = atom({ plugin: 'dash', key: 'thread' } as const, '')
const now = atom({ plugin: 'dash', key: 'now' } as const, '')
const tool = atom({ plugin: 'dash', key: 'tool' } as const, '')
const isHidden = atom({ plugin: 'dash', key: 'isHidden' } as const, false)
const isPaneClosed = atom({ plugin: 'dash', key: 'isPaneClosed' } as const, false)
const work = atom({ plugin: 'dash', key: 'work' } as const, {
  cwd: '',
  turns: 0,
})

const EDIT_TOOLS = new Set(['Edit', 'Write', 'MultiEdit'])
const GIT_TOOLS = new Set(['Bash', 'Edit', 'Write', 'NotebookEdit'])
const TASK_TOOLS = new Set(['TaskCreate', 'TaskUpdate'])
const ICON = {
  cache: '\uf06d',
}
// Stroke icons in a 24×24 box, drawn on surfaces whose font has no Nerd Font glyphs.
const ICON_SVG: Record<keyof typeof ICON, string> = {
  cache:
    '<path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.07-2.14-.22-4.05 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.15.43-2.29 1-3a2.5 2.5 0 0 0 2.5 2.5z"/>',
}
const SVG_COLOR: Record<string, string> = {
  claude: '#d77757',
  success: '#4eba65',
  warning: '#ffc107',
  dim: '#999999',
}
const LIMIT_LABEL: Record<string, string> = {
  five_hour: '5h',
  seven_day: '7d',
}

let configDir = ''
let home = ''
let isGitQueued = false
let prompt = ''
let prompts: string[] = []
let recent: string[] = []
let lastSummaryAt = 0
let isSummarizing = false
let isThreading = false
let isReseating = false

async function refreshGit($: EngineInterface) {
  const cwd = await $.session.cwd()
  const run = await $.process.run(
    [
      'sh',
      '-c',
      'cd "$(git rev-parse --show-toplevel)" || exit 1; ' +
        'git --no-optional-locks status --porcelain=v2 --branch || exit 1; ' +
        'printf "# gitdir %s\\n" "$(git rev-parse --absolute-git-dir)"; ' +
        'git log -1 --format="# last %h%x09%cr%x09%s" 2>/dev/null; ' +
        'git --no-optional-locks diff --numstat HEAD 2>/dev/null | sed "s/^/# num /"',
    ],
    { cwd, timeoutMs: 3000 },
  )
  const root = (await $.session.repo())?.root ?? cwd
  const repo = root.split('/').pop() ?? root
  await update($, git, () => (run.exitCode === 0 ? parseGit(repo, run.stdout) : null))
}

function queueGit($: EngineInterface) {
  if (isGitQueued) return
  isGitQueued = true
  $.clock.after(500, () => {
    isGitQueued = false
    void refreshGit($)
  })
}

// Ctrl-\ Ctrl-N reaches normal mode from any nvim mode, where a bare Esc before ':' can read as Alt-:.
const OPEN_IN_EDITOR = `
s="$REX_SESSION"
b=$(rex block ls -s "$s" --json | jq -r '.blocks[] | select(.label == "Editor") | .block_id' | head -1)
[ -n "$b" ] || exit 1
p=$(printf %s "$(git rev-parse --show-toplevel)/$1" | sed 's/[ %#|"\\\\]/\\\\&/g')
fg=$(rex api call -s "$s" block.method "{\\"block_id\\":\\"$b\\",\\"method\\":\\"process\\"}" | jq -r .foreground.name)
case "$fg" in
  nvim) printf '\\034\\016:e %s\\r' "$p" ;;
  *) printf 'nvim %s\\r' "$p" ;;
esac | rex send -s "$s" -b "$b" || exit 1
w=$(rex window ls -s "$s" --json | jq -r '.. | objects | select(.label? == "Edit") | .window_id' | head -1)
c=$(rex client ls --json | jq -r --arg s "$s" '[.clients[] | select(.info.kind == "app" and (.session_ids | index($s)))][0].client_id')
rex do -C "$c" session.select session_id="$s" window_id="$w"
`

async function openInEditor($: EngineInterface, path: string) {
  const run = await $.process.run(['sh', '-c', OPEN_IN_EDITOR, 'sh', path], { cwd: await $.session.cwd(), timeoutMs: 5000 })
  if (run.exitCode !== 0) $.ui.toast(`Opening ${path} failed: ${run.stderr.trim() || `exit ${run.exitCode}`}`)
}

async function refreshTasks($: EngineInterface) {
  const dir = `${configDir}/tasks/${await $.session.id()}`
  if (!(await $.fs.exists(dir))) return
  const files = (await $.fs.list(dir)).filter(f => f.kind === 'file' && f.name.endsWith('.json'))
  const list: Task[] = []
  for (const f of files) {
    try {
      const t = JSON.parse(await $.fs.read(`${dir}/${f.name}`))
      list.push({ subject: t.activeForm ?? t.subject ?? '', status: t.status })
    } catch {}
  }
  await update($, tasks, () => list)
}

async function loadAgent($: EngineInterface) {
  const paths = await $.process.run([
    'sh',
    '-c',
    'printf "%s\\n%s\\n%s\\n%s" "${CLAUDE_CONFIG_DIR:-$HOME/.claude}" "${CLAUDE_CONFIG_DIR:-$HOME}/.claude.json" "$HOME" "$DASH_BADGE"',
  ])
  const [dir = '', configFile = '', homeDir = '', badge = ''] = paths.stdout.split('\n')
  configDir = dir
  home = homeDir
  let account: string | undefined
  let plan: string | undefined
  let isExtraUsage = false
  try {
    const o = JSON.parse(await $.fs.read(configFile)).oauthAccount
    account = o?.emailAddress
    plan = planName(o?.organizationRateLimitTier ?? o?.organizationType)
    isExtraUsage = o?.hasExtraUsageEnabled === true
  } catch {}
  const model = prettyModel(await $.session.model())
  await update($, agent, a => ({
    ...a,
    model,
    account,
    plan,
    isExtraUsage,
    badge: badge.trim() || undefined,
  }))
}

async function refreshTitle($: EngineInterface) {
  const run = await $.process.run([
    'sh',
    '-c',
    'f=$(ls "$1"/projects/*/"$2".jsonl 2>/dev/null | head -1); [ -n "$f" ] || exit 0; ' +
      't=$(grep -o \'"customTitle":"[^"]*"\' "$f" | tail -1); ' +
      '[ -n "$t" ] || t=$(grep -o \'"aiTitle":"[^"]*"\' "$f" | tail -1); ' +
      'printf %s "$t" | sed \'s/.*":"//; s/"$//\'',
    'sh',
    configDir,
    await $.session.id(),
  ])
  const found = run.stdout.trim()
  if (found) await update($, title, () => found)
}

async function refreshWork($: EngineInterface) {
  const cwd = await $.session.cwd()
  const turns = await $.session.turns()
  await update($, work, w => ({
    ...w,
    cwd: home && cwd.startsWith(home) ? `~${cwd.slice(home.length)}` : cwd,
    turns,
  }))
}

async function refreshStyle($: EngineInterface) {
  const style = await $.settings.read({ key: 'outputStyle' })
  await update($, agent, a => ({ ...a, style: typeof style === 'string' ? style : undefined }))
}

function toUsage(u: Pick<SessionUsage, 'context' | 'rateLimits' | 'cost'>): Usage {
  return {
    context: u.context.percent,
    tokens: u.context.tokens,
    window: u.context.window,
    startedAt: 'startedAt' in u ? (u as SessionUsage).startedAt : undefined,
    limits: u.rateLimits.map(l => ({
      kind: l.kind,
      percent: l.percentUsed,
      resetsAt: l.resetsAt,
    })),
    cost: u.cost?.usd,
  }
}

async function refreshUsage($: EngineInterface) {
  const u = await $.session.usage()
  await update($, usage, () => toUsage(u))
}

async function summarizeThread($: EngineInterface) {
  if (isThreading) return
  isThreading = true
  try {
    const r = await $.model.complete({
      model: MODEL,
      maxTokens: 30,
      system:
        'You say what a coding conversation is working on right now: the thread its latest prompts share, not only the last step. ' +
        'Keep the current line unless the work has clearly moved on. ' +
        'Reply with one line of at most 8 words, sentence case, no quotes, no trailing period.',
      prompt: [
        `Current line: ${(await read($, thread)) || '(none)'}`,
        `Developer prompts, oldest first:\n${prompts.map(p => `- ${p.slice(0, 300)}`).join('\n')}`,
      ].join('\n\n'),
    })
    if (r.isAnswered) await update($, thread, () => oneLine(r.text))
  } finally {
    isThreading = false
  }
}

async function summarizeNow($: EngineInterface, answer: string, isDone: boolean) {
  const at = await $.clock.now()
  if (isSummarizing || (!isDone && at - lastSummaryAt < SUMMARY_INTERVAL_MS)) return
  isSummarizing = true
  lastSummaryAt = at
  try {
    const r = await $.model.complete({
      model: MODEL,
      maxTokens: 40,
      system:
        'You watch a coding agent work and report its state in one line of at most 12 words. ' +
        (isDone ? 'The turn just ended: say what it finished or is waiting for.' : 'Say what it is doing right now.') +
        ' Present tense, no quotes, no trailing period.',
      prompt: [
        `Developer asked: ${prompt.slice(0, 1500)}`,
        `Recent tool calls:\n${recent.slice(-8).join('\n') || '(none)'}`,
        `Latest agent text: ${answer.slice(-800) || '(none)'}`,
      ].join('\n\n'),
    })
    if (r.isAnswered) await update($, now, () => oneLine(r.text))
  } finally {
    isSummarizing = false
  }
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    await $.command.register({ name: 'dash', description: 'Hide or show the dash; `side` moves it to a side pane' })
    // Opened unasked, the engine seats it only on a wide terminal and waits otherwise.
    if (!(await read($, isHidden)) && !(await read($, isPaneClosed))) void $.ui.open({ id: PANE, title: 'Dash' })
    await loadAgent($)
    void refreshTitle($)
    void refreshWork($)
    void refreshGit($)
    void refreshTasks($)
    void refreshUsage($)
    void refreshStyle($)
    $.clock.every(1000, () => void update($, tick, n => n + 1))
    return next(e)
  })

  on('prompt.submit', async ($, e, next) => {
    prompt = e.text
    recent = []
    lastSummaryAt = 0
    if (e.text.trim() !== '' && !e.text.startsWith('/')) {
      prompts = [...prompts, e.text].slice(-5)
      void update($, now, () => 'Reading the request')
      void summarizeThread($)
    }
    queueGit($)
    void refreshUsage($)
    void refreshWork($)
    void $.session.model().then(m => update($, agent, a => ({ ...a, model: prettyModel(m) })))
    return next(e)
  })

  on('turn.step', async function* ($, e, next) {
    if (!e.agentId && e.effort !== undefined) void update($, agent, a => ({ ...a, effort: String(e.effort) }))
    const result = yield* next(e)
    if (e.agentId) return result
    if (result.toolUses.length > 0) void summarizeNow($, result.answer, false)
    const u = result.usage
    if (u) {
      const at = await $.clock.now()
      const total = u.cache_read_input_tokens + u.cache_creation_input_tokens + u.input_tokens
      await update($, cache, c => {
        const wasWarm = c.lastAt !== undefined && at - c.lastAt < CACHE_TTL_MS
        const isMiss = wasWarm && u.cache_read_input_tokens === 0
        return {
          hit: total > 0 ? u.cache_read_input_tokens / total : c.hit,
          lastAt: at,
          misses: c.misses + (isMiss ? 1 : 0),
        }
      })
    }
    return result
  })

  on('tool.call', async ($, e, next) => {
    if (!e.agentId) {
      const call = describeCall(e as unknown as Record<string, unknown>)
      recent = [...recent, call].slice(-20)
      void update($, tool, () => call)
    }
    if (EDIT_TOOLS.has(e.tool)) {
      const delta = editDelta(e as unknown as Record<string, unknown>)
      const ran = await next(e)
      if (!ran.isError)
        void update($, lines, l => ({
          added: l.added + delta.added,
          removed: l.removed + delta.removed,
        }))
      queueGit($)
      return ran
    }
    const ran = await next(e)
    if (GIT_TOOLS.has(e.tool)) queueGit($)
    if (!e.agentId && TASK_TOOLS.has(e.tool)) void refreshTasks($)
    return ran
  })

  on('command.run', { command: 'dash' }, async ($, e) => {
    if (e.args.trim() === 'side') {
      await update($, isHidden, () => false)
      await update($, isPaneClosed, () => false)
      await $.ui.open({ id: PANE, title: 'Dash' })
      return { text: 'Dash moved to the side.' }
    }
    let hidden = false
    await update($, isHidden, h => (hidden = !h))
    if (hidden) await $.ui.close({ id: PANE })
    else if (!(await read($, isPaneClosed))) void $.ui.open({ id: PANE, title: 'Dash' })
    return { text: hidden ? 'Dash hidden.' : 'Dash shown.' }
  })

  on('ui.close', async ($, e, next) => {
    if (e.id === PANE && e.origin.kind === 'person') await update($, isPaneClosed, () => true)
    return next(e)
  })

  on('command.run', { command: 'rename' }, async ($, e, next) => {
    const result = await next(e)
    const name = e.args.trim()
    if (name !== '') await update($, title, () => name)
    else void refreshTitle($)
    return result
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    if (!e.agentId) {
      await update($, tool, () => '')
      void summarizeNow($, 'answer' in e ? e.answer : '', true)
      void refreshTitle($)
      void refreshWork($)
      void refreshStyle($)
    }
    return result
  })

  on('session.measure', async ($, e, next) => {
    await update($, usage, prev => ({
      ...toUsage(e),
      startedAt: prev.startedAt,
    }))
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    if (e.props.hasSurvey || (await read($, isHidden))) return next(e)
    await read($, tick)
    if ((await $.ui.panes()).some(p => p.id === PANE && p.isPlaced)) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    const below = await next(e)
    const live = e.props.isWorking ? await read($, tool) : ''
    return (
      <Box flexDirection="column">
        {below}
        <Text dimColor wrap="truncate-end">
          {'╌'.repeat(e.props.bodyColumns)}
        </Text>
        {await draw($, e, e.props.bodyColumns, e.props.bodyColumns >= 150, live)}
      </Box>
    )
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    if (e.props.placement === 'inline') {
      // Inline it would replace the band; reopened unasked it waits undrawn until it can dock.
      if (!isReseating) {
        isReseating = true
        const isFullscreen = e.viewport?.isFullscreen === true
        $.clock.after(0, async () => {
          await $.ui.close({ id: PANE })
          if (isFullscreen) await $.ui.open({ id: PANE, title: 'Dash' })
          isReseating = false
        })
      }
      return $.ui.resolve(e).Box({})
    }
    return draw($, e, e.props.bodyColumns, false, await read($, tool), true)
  })
}

async function draw($: EngineInterface, e: ResolveInput, cols: number, isSplit: boolean, live: string, isSide = false) {
  const els = $.ui.resolve(e)
  const { Box, Text, Button } = els
  // The desktop app's font carries no Nerd Font glyphs and lays text out proportionally.
  const isDesktop = e.surface === 'desktop'
  const Svg = 'Svg' in els ? els.Svg : undefined
  const mark = (key: keyof typeof ICON, color: string) =>
    isDesktop && Svg ? (
      <Svg
        alt={key}
        width={14}
        height={14}
        source={`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="${SVG_COLOR[color] ?? color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICON_SVG[key]}</svg>`}
      />
    ) : (
      <Text color={color === 'dim' ? undefined : color} dimColor={color === 'dim'}>
        {ICON[key]}
      </Text>
    )
  const g = await read($, git)
  const a: Agent = await read($, agent)
  const t = await read($, title)
  const tk = await read($, tasks)
  const u = await read($, usage)
  const c = await read($, cache)
  const ln = await read($, lines)
  const w = await read($, work)
  const th = await read($, thread)
  const nw = await read($, now)
  await read($, tick)
  const at = await $.clock.now()
  const done = tk.filter(x => x.status === 'completed').length
  const isCacheWarm = c.lastAt !== undefined && at - c.lastAt < CACHE_TTL_MS

  const LABEL = 9
  const kv = (
    name: string,
    value: RenderChildren,
    wrap: 'truncate-end' | 'truncate-start' = 'truncate-end',
    lead?: RenderChildren,
  ) => (
    <Box alignItems="center">
      <Box width={LABEL} flexShrink={0}>
        <Text color="inactive">{name}</Text>
      </Box>
      {lead && (
        <Box marginRight={1} flexShrink={0}>
          {lead}
        </Box>
      )}
      <Text wrap={wrap}>{value}</Text>
    </Box>
  )

  const gauge = (percent: number, width: number, fill = 'rate_limit_fill') => {
    if (isDesktop) {
      const pct = Math.min(100, Math.max(0, percent))
      return (
        <Box width={width} height={1} flexShrink={0} alignItems="center">
          <Box width="100%" height={0.4} backgroundColor="rate_limit_empty" overflow="hidden">
            <Box width={`${pct}%`} backgroundColor={fill} />
          </Box>
        </Box>
      )
    }
    const b = bar(percent, width)
    const n = b.lastIndexOf('▰') + 1
    return (
      <Text>
        <Text color={fill}>{b.slice(0, n)}</Text>
        <Text color="rate_limit_empty">{b.slice(n)}</Text>
      </Text>
    )
  }

  const meter = (name: string, percent: number, extra: string) => (
    <Box flexShrink={0}>
      <Text dimColor>{name} </Text>
      {gauge(percent, 6, heat(percent))}
      <Text bold> {String(Math.round(percent)).padStart(3)}%</Text>
      {extra !== '' && <Text dimColor> {extra}</Text>}
    </Box>
  )

  const label = (name: string) => (
    <Box width={LABEL} flexShrink={0}>
      <Text color="inactive">{name}</Text>
    </Box>
  )
  const dot = <Text dimColor> · </Text>
  const modelParts = [
    a.effort && <Text color="warning">{a.effort}</Text>,
    a.style && a.style !== 'default' && <Text>{a.style}</Text>,
    <Text>{w.turns} turns</Text>,
  ].filter(Boolean)
  const accountLine = a.account && (
    <Text wrap="truncate-end">
      <Text color="suggestion">{a.account}</Text>
      {a.badge && (
        <Text color="error" bold>
          {' '}
          ⚠ {a.badge}
        </Text>
      )}
      {a.plan && dot}
      {a.plan && <Text>{a.plan}</Text>}
      {a.isExtraUsage && dot}
      {a.isExtraUsage && <Text color="warning">extra usage on</Text>}
    </Text>
  )
  const actions = (
    <Box gap={1} flexShrink={0}>
      <Box backgroundColor="subtle" paddingX={1}>
        <Button key="review" plain label="Ponytail Review" onPress={() => void $.command.run({ command: 'ponytail:ponytail-review', args: '' })} />
      </Box>
      <Box backgroundColor="subtle" paddingX={1}>
        <Button key="audit" plain label="Ponytail Repo Audit" onPress={() => void $.command.run({ command: 'ponytail:ponytail-audit', args: '' })} />
      </Box>
    </Box>
  )
  const current = tk.find(x => x.status === 'in_progress')

  const lead = th.length
  const room = cols - 4 - lead
  const isNowShown = nw !== '' && (lead === 0 || room >= nw.length + 3)
  const isLiveShown = live !== '' && isNowShown && room >= nw.length + live.length + 6

  const upstream = g?.upstream && g.upstream !== `origin/${g.branch}` ? g.upstream : undefined
  const status = (
    g
      ? [
          [upstream && ` ${upstream}`, undefined],
          [g.ahead > 0 && ` ↑${g.ahead}`, 'success'],
          [g.behind > 0 && ` ↓${g.behind}`, 'error'],
          [g.upstream && g.ahead === 0 && g.behind === 0 && ' ✓', 'success'],
        ]
      : []
  ).filter((s): s is [string, string | undefined] => typeof s[0] === 'string' && s[0] !== '')
  const tail = u.startedAt !== undefined ? ` · ${duration(at - u.startedAt)}` : ''
  const repoWidth = (isSplit ? cols - Math.floor(cols / 2) - 2 : cols - 2) - LABEL
  const repoRoom =
    repoWidth -
    `${g?.repo ?? '-'}${g?.isWorktree ? ' worktree' : ''} `.length -
    tail.length -
    (g ? 3 + status.reduce((n, [s]) => n + s.length, 0) : 0)
  const branch = clip(g ? (g.branch ?? 'detached') : '', repoRoom)
  const repoLine = { branch, cwd: clip(w.cwd, repoRoom - branch.length, true) }

  if (isSide) {
    const rule = (
      <Text dimColor wrap="truncate-end">
        {'╌'.repeat(Math.max(0, cols - 2))}
      </Text>
    )
    const section = (name: string, ...rows: RenderChildren[]) => (
      <Box flexDirection="column">
        <Text color="inactive" bold>
          {name}
        </Text>
        {rows.filter(Boolean)}
      </Box>
    )
    const fileColor: Record<string, string> = { A: 'success', D: 'error', '?': 'suggestion' }
    const wide = (name: string, percent: number, extra: string) => (
      <Box>
        <Box width={5} flexShrink={0}>
          <Text dimColor>{name}</Text>
        </Box>
        {gauge(percent, 12, heat(percent))}
        <Text bold> {String(Math.round(percent)).padStart(3)}%</Text>
        {extra !== '' && <Text dimColor> {extra}</Text>}
      </Box>
    )
    const field = (name: string, value: RenderChildren) => (
      <Box>
        <Box width={7} flexShrink={0}>
          <Text dimColor>{name}</Text>
        </Box>
        {value}
      </Box>
    )
    return (
      <Box flexDirection="column" paddingX={1}>
        {t !== '' && (
          <Text color="claude" bold wrap="wrap">
            {t}
          </Text>
        )}
        <Box flexDirection="column">
          {t !== '' ? (
            <Text color="claude" wrap="truncate-end">
              {'╌'.repeat(Math.max(0, cols - 2))}
            </Text>
          ) : (
            rule
          )}
          <Box flexDirection="column" gap={1}>
            {accountLine && section('account', accountLine)}
            {section(
              'model',
              <Text wrap="truncate-end">
                <Text color="success" bold>
                  {a.model}
                </Text>
                {a.effort && <Text color="warning"> {a.effort}</Text>}
                {a.style && a.style !== 'default' && <Text> · {a.style}</Text>}
              </Text>,
              <Text>
                {w.turns} turns{tail}
              </Text>,
            )}
            {(u.context !== undefined || u.limits.length > 0) &&
              section(
                'usage',
                u.context !== undefined &&
                  wide(
                    'ctx',
                    u.context,
                    u.tokens !== undefined && u.window !== undefined
                      ? `${Math.round(u.tokens / 1000)}k/${u.window >= 1_000_000 ? `${u.window / 1_000_000}M` : `${Math.round(u.window / 1000)}k`}`
                      : '',
                  ),
                ...u.limits.map(l => wide(LIMIT_LABEL[l.kind] ?? l.kind, l.percent, until(l.resetsAt, at))),
              )}
            {section(
              'cache',
              <Box>
                <Box marginRight={1} flexShrink={0}>
                  {mark('cache', isCacheWarm ? 'warning' : 'dim')}
                </Box>
                <Text wrap="truncate-end">
                  <Text>{c.hit !== undefined ? `${Math.round(c.hit * 100)}% hit` : '–'}</Text>
                  <Text dimColor> · {isCacheWarm && c.lastAt ? `expires ${until(c.lastAt + CACHE_TTL_MS, at)}` : 'cold'}</Text>
                  {c.misses > 0 && <Text color="error"> · {c.misses} miss</Text>}
                </Text>
              </Box>,
              <Text wrap="truncate-end">
                {u.cost !== undefined && <Text color="warning">${u.cost.toFixed(2)}</Text>}
                {u.cost !== undefined && dot}
                <Text color="success">+{ln.added}</Text>
                <Text dimColor>/</Text>
                <Text color="error">-{ln.removed}</Text>
                <Text dimColor> lines</Text>
              </Text>,
            )}
          </Box>
        </Box>
        <Box flexDirection="column">
          {rule}
          <Box flexDirection="column" gap={1}>
            {tk.length > 0 &&
              section(
                'tasks',
                <Box>
                  {gauge((done / tk.length) * 100, 12)}
                  <Text bold>
                    {' '}
                    {done}/{tk.length}
                  </Text>
                </Box>,
                ...tk.map(x => (
                  <Text
                    wrap="truncate-end"
                    color={x.status === 'in_progress' ? 'warning' : undefined}
                    dimColor={x.status === 'completed'}
                  >
                    {x.status === 'completed' ? '✓ ' : x.status === 'in_progress' ? '▸ ' : '· '}
                    {x.subject}
                  </Text>
                )),
              )}
            {(th !== '' || nw !== '') && (
              <Box flexDirection="column">
                {th !== '' && (
                  <Text bold wrap="wrap">
                    {th}
                  </Text>
                )}
                {nw !== '' && (
                  <Text dimColor wrap="wrap">
                    {nw}
                  </Text>
                )}
                {live !== '' && (
                  <Text dimColor wrap="truncate-end">
                    ↳ {live}
                  </Text>
                )}
              </Box>
            )}
          </Box>
        </Box>
        {rule}
        {actions}
        <Box flexDirection="column">
          {rule}
          <Box flexDirection="column" gap={1}>
            {section(
              'repo',
              field(
                'name',
                <Text wrap="truncate-end">
                  <Text bold>{g?.repo ?? '-'}</Text>
                  {g?.isWorktree && <Text color="suggestion"> · worktree</Text>}
                </Text>,
              ),
              field(
                'path',
                <Text dimColor wrap="truncate-start">
                  {w.cwd}
                </Text>,
              ),
              g &&
                field(
                  'branch',
                  <Text wrap="truncate-end">
                    <Text color="claude" bold>
                      {g.branch ?? 'detached'}
                    </Text>
                    {status.map(([s, color]) => (
                      <Text color={color}>{s}</Text>
                    ))}
                  </Text>,
                ),
              g?.last &&
                field(
                  'commit',
                  <Text wrap="truncate-end">
                    <Text color="warning">{g.last.hash}</Text>
                    <Text> {g.last.subject}</Text>
                    <Text dimColor> · {g.last.age}</Text>
                  </Text>,
                ),
            )}
            {g &&
              section(
                g.files.length === 0 ? 'changes' : `changes · ${g.files.length}`,
                g.files.length === 0 && <Text color="success">✓ clean</Text>,
                ...g.files.map(f => (
                  <Button key={`file:${f.path}`} plain onPress={() => void openInEditor($, f.path)}>
                    <Text color={fileColor[f.status] ?? 'warning'}>{f.status} </Text>
                    <Text>{f.path}</Text>
                    {f.added !== undefined && <Text color="success"> +{f.added}</Text>}
                    {f.removed !== undefined && <Text color="error"> -{f.removed}</Text>}
                  </Button>
                )),
              )}
          </Box>
        </Box>
      </Box>
    )
  }

  return (
    <Box flexDirection="column">
      <Box paddingX={1}>
        {t !== '' && (
          <Text color="claude" bold wrap="truncate-end">
            {t}
          </Text>
        )}
        <Box flexGrow={1} />
        {actions}
      </Box>
      <Box flexDirection={isSplit ? 'row' : 'column'} paddingX={1}>
        <Box
          flexDirection="column"
          flexShrink={0}
          width={isSplit ? Math.floor(cols / 2) : undefined}
          paddingRight={isSplit ? 2 : 0}
        >
          {accountLine && kv('account', accountLine)}
          {kv(
            'model',
            <Text>
              <Text color="success" bold>
                {a.model}
              </Text>
              <Text> </Text>
              {modelParts.map((p, i) => (
                <Text>
                  {i > 0 && dot}
                  {p}
                </Text>
              ))}
            </Text>,
          )}
          {(u.context !== undefined || u.limits.length > 0) && (
            <Box>
              {label('usage')}
              <Box gap={3} overflow="hidden">
                {u.context !== undefined &&
                  meter(
                    'ctx',
                    u.context,
                    u.tokens !== undefined && u.window !== undefined
                      ? `${Math.round(u.tokens / 1000)}k/${u.window >= 1_000_000 ? `${u.window / 1_000_000}M` : `${Math.round(u.window / 1000)}k`}`
                      : '',
                  )}
                {u.limits.map(l => meter(LIMIT_LABEL[l.kind] ?? l.kind, l.percent, until(l.resetsAt, at)))}
              </Box>
            </Box>
          )}
          {kv(
            'cache',
            <Text>
              <Text>{c.hit !== undefined ? `${Math.round(c.hit * 100)}% hit` : '–'}</Text>
              <Text dimColor>
                {' '}
                · {isCacheWarm && c.lastAt ? `expires ${until(c.lastAt + CACHE_TTL_MS, at)}` : 'cold'}
              </Text>
              {c.misses > 0 && <Text color="error"> · {c.misses} miss</Text>}
              {u.cost !== undefined && dot}
              {u.cost !== undefined && <Text color="warning">${u.cost.toFixed(2)}</Text>}
              {dot}
              <Text color="success">+{ln.added}</Text>
              <Text dimColor>/</Text>
              <Text color="error">-{ln.removed}</Text>
              <Text dimColor> lines</Text>
            </Text>,
            'truncate-end',
            mark('cache', isCacheWarm ? 'warning' : 'dim'),
          )}
        </Box>

        <Box flexDirection="column" flexGrow={1}>
          <Box>
            {label('repo')}
            <Text wrap="truncate-end">
              <Text color="claude" bold>
                {g?.repo ?? '-'}
              </Text>
              {g?.isWorktree && <Text color="suggestion"> worktree</Text>}
              <Text> {repoLine.cwd}</Text>
              {g && dot}
              {g && (
                <Text color="claude" bold>
                  {repoLine.branch}
                </Text>
              )}
              {status.map(([s, color]) => (
                <Text color={color === 'dim' ? undefined : color} dimColor={color === 'dim'}>
                  {s}
                </Text>
              ))}
              {tail !== '' && <Text dimColor>{tail}</Text>}
            </Text>
          </Box>
          {g &&
            kv(
              'changes',
              g.files.length === 0 ? (
                <Text color="success">✓ clean</Text>
              ) : (
                <Text>
                  {g.added > 0 && <Text color="success">+{g.added} added </Text>}
                  {g.modified > 0 && <Text color="warning">~{g.modified} modified </Text>}
                  {g.deleted > 0 && <Text color="error">-{g.deleted} deleted </Text>}
                  {g.untracked > 0 && <Text color="suggestion">?{g.untracked} untracked</Text>}
                </Text>
              ),
            )}
          {g?.last &&
            kv(
              'last',
              <Text>
                <Text color="warning">{g.last.hash}</Text>
                <Text> {g.last.subject}</Text>
                <Text dimColor> · {g.last.age}</Text>
              </Text>,
            )}
        </Box>
      </Box>
      {tk.length > 0 && done < tk.length && (
        <Box paddingX={1}>
          {label('tasks')}
          {gauge((done / tk.length) * 100, 6)}
          <Text bold>
            {' '}
            {done}/{tk.length}
          </Text>
          {current && (
            <Text color="warning" wrap="truncate-end">
              {'  ▸ '}
              {current.subject}
            </Text>
          )}
        </Box>
      )}
      {(lead > 0 || nw !== '') && (
        <Box paddingX={1}>
          <Text wrap="truncate-end">
            {th !== '' && <Text bold>{th}</Text>}
            {isNowShown && (
              <Text dimColor>
                {lead > 0 ? ' · ' : ''}
                {nw}
              </Text>
            )}
            {isLiveShown && <Text dimColor> ↳ {live}</Text>}
          </Text>
        </Box>
      )}
    </Box>
  )
}
