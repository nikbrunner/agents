import { expect, mock, test } from 'claude-code/testing'
import type { TestBody } from 'claude-code/testing'

type On = Parameters<TestBody>[1]

function seed(on: On, disk: { titles: string; env: Record<string, string> }) {
  const renames: string[][] = []
  on('process.run', (_, e) => {
    if (e.argv[0] === 'rex') renames.push([...e.argv])
    const isTitle = e.argv.join(' ').includes('customTitle')
    return { value: { exitCode: 0, stdout: isTitle ? disk.titles : '', stderr: '', isStdoutTruncated: false, isStderrTruncated: false } }
  })
  on('env.get', (_, e) => ({ value: disk.env[e.name] }))
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
  return renames
}

const REX = { REX_SESSION: 'session:s', REX_BLOCK: 'block:b' }

test('a custom title names the Rex pane once', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const renames = seed(on, { titles: 'custom\tBrush wheel keys · Clara', env: REX })
  await $.session.start({ cwd: '/repo', surface: 'terminal', isInteractive: true })
  await clock.advance(10)
  await $.command.run({ command: 'rename', args: '' } as never)
  await clock.advance(10)
  expect(renames).toEqual([['rex', 'block', 'rename', '-s', 'session:s', 'block:b', 'Brush wheel keys · Clara']])
})

test('a title written after the start names the Rex pane at the first prompt', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  on('prompt.submit', (_, e) => ({ text: e.text }))
  on('model.complete', () => ({ value: { isAnswered: false } }) as never)
  const disk = { titles: '', env: REX }
  const renames = seed(on, disk)
  await $.session.start({ cwd: '/repo', surface: 'terminal', isInteractive: true })
  await clock.advance(10)
  disk.titles = 'custom\tBrush wheel keys · Clara'
  await $.prompt.submit({ text: 'Go' } as never)
  await clock.advance(10)
  expect(renames).toEqual([['rex', 'block', 'rename', '-s', 'session:s', 'block:b', 'Brush wheel keys · Clara']])
})

test('an AI title leaves the Rex pane label alone', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const renames = seed(on, { titles: 'ai\tFix the wheel keys', env: REX })
  await $.session.start({ cwd: '/repo', surface: 'terminal', isInteractive: true })
  await clock.advance(10)
  expect(renames).toEqual([])
})

test('outside Rex nothing is renamed', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const renames = seed(on, { titles: 'custom\tBrush wheel keys · Clara', env: {} })
  await $.session.start({ cwd: '/repo', surface: 'terminal', isInteractive: true })
  await clock.advance(10)
  expect(renames).toEqual([])
})

test('/rename with a name renames the Rex pane right away', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const renames = seed(on, { titles: 'ai\tFix the wheel keys', env: REX })
  await $.session.start({ cwd: '/repo', surface: 'terminal', isInteractive: true })
  await $.command.run({ command: 'rename', args: 'Wheel keys · Clara' } as never)
  await clock.advance(10)
  expect(renames).toEqual([['rex', 'block', 'rename', '-s', 'session:s', 'block:b', 'Wheel keys · Clara']])
})
