import { expect, mock, test } from 'claude-code/testing'
import type { TestBody } from 'claude-code/testing'

type On = Parameters<TestBody>[1]

function seed(on: On, disk: { titles: string; env: Record<string, string>; topic?: string }) {
  const labels: string[] = []
  const asked: string[] = []
  on('process.run', (_, e) => {
    if (e.argv[0] === 'rex') labels.push(e.argv[e.argv.length - 1]!)
    const isTitle = e.argv.join(' ').includes('customTitle')
    return { value: { exitCode: 0, stdout: isTitle ? disk.titles : '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('model.complete', (_, e) => {
    const p = String((e as { prompt?: unknown }).prompt ?? '')
    if (p.startsWith('Current line')) asked.push(p.split('\n')[0]!)
    const isThread = p.startsWith('Current line') && disk.topic !== undefined
    return { value: isThread ? { isAnswered: true, text: disk.topic } : { isAnswered: false } } as never
  })
  on('env.get', (_, e) => ({ value: disk.env[e.name] }))
  on('prompt.submit', (_, e) => ({ text: e.text }))
  on('fs.stat', () => ({ value: { kind: 'file', size: 0, mtimeMs: 1, isLink: false } }))
  on('fs.exists', () => ({ value: false }))
  on('command.register', () => ({ value: { command: 'dash' } }))
  on('command.run', { command: 'rename' }, () => ({ text: '' }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/repo' }))
  on('session.repo', () => ({ value: null }))
  on('session.model', () => ({ value: 'claude-fable-5-2' }))
  on('session.id', () => ({ value: 's1' }))
  on('session.turns', () => ({ value: 0 }))
  on('session.usage', () => ({ value: { context: { percent: 0, tokens: 0, window: 0 }, rateLimits: [], startedAt: 0 } }))
  on('settings.read', () => ({ value: {} }))
  return { labels, asked }
}

const REX = { REX_SESSION: 'session:s', REX_BLOCK: 'block:b' }
const start = { cwd: '/repo', surface: 'terminal', isInteractive: true } as const

test('a dispatched name labels the pane and holds through the brief', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const disk = { titles: '', env: REX, topic: 'Wheel key handling for the brush tool' }
  const { labels, asked } = seed(on, disk)
  await $.session.start(start)
  await clock.advance(2000)
  await $.prompt.submit({ text: 'The brief' } as never)
  await clock.advance(10)
  disk.titles = 'custom\tBrush wheel keys · Clara'
  await clock.advance(2000)
  expect(labels).toEqual(['Brush wheel keys · Clara'])
  await $.prompt.submit({ text: 'Next step' } as never)
  await clock.advance(2000)
  expect(asked).toEqual(['Current line: Brush wheel keys'])
})

test('the topic moves on and the persona stays', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const disk = { titles: 'custom\tBrush wheel keys · Clara', env: REX, topic: 'Brush wheel keys' }
  const { labels } = seed(on, disk)
  await $.session.start(start)
  await clock.advance(2000)
  await $.prompt.submit({ text: 'Go' } as never)
  await clock.advance(2000)
  disk.topic = 'Release notes for the brush panel'
  await $.prompt.submit({ text: 'Now the release notes' } as never)
  await clock.advance(2000)
  expect(labels).toEqual(['Brush wheel keys · Clara', 'Release notes for the brush panel · Clara'])
})

test('an unnamed session is labelled by its topic line', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const disk = { titles: 'ai\tFix the wheel keys', env: REX, topic: 'Fixing the wheel keys' }
  const { labels } = seed(on, disk)
  await $.session.start(start)
  await clock.advance(2000)
  expect(labels).toEqual([])
  await $.prompt.submit({ text: 'Fix it' } as never)
  await clock.advance(2000)
  expect(labels).toEqual(['Fixing the wheel keys'])
})

test('a name without a topic stays as given', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const disk = { titles: 'custom\tBob', env: REX, topic: 'Filing the reports' }
  const { labels } = seed(on, disk)
  await $.session.start(start)
  await $.prompt.submit({ text: 'Good morning' } as never)
  await clock.advance(2000)
  expect(labels).toEqual(['Bob'])
})

test('outside Rex nothing is renamed', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const { labels } = seed(on, { titles: 'custom\tBrush wheel keys · Clara', env: {}, topic: 'Brush wheel keys' })
  await $.session.start(start)
  await $.prompt.submit({ text: 'Go' } as never)
  await clock.advance(2000)
  expect(labels).toEqual([])
})

test('/rename with a name relabels the pane and resets the topic', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const { labels } = seed(on, { titles: 'ai\tFix the wheel keys', env: REX })
  await $.session.start(start)
  await $.command.run({ command: 'rename', args: 'Wheel keys · Clara' } as never)
  await clock.advance(2000)
  expect(labels).toEqual(['Wheel keys · Clara'])
})
