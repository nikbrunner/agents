import { expect, mock, test } from 'claude-code/testing'

test('a git event from outside the session refreshes the git rows', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  let mtimeMs = 1
  let refreshes = 0
  on('process.run', (_, e) => {
    const isGit = e.argv.join(' ').includes('status --porcelain')
    if (isGit) refreshes++
    return {
      value: {
        exitCode: 0,
        stdout: isGit ? '# branch.head main\n# watch /repo/.git/index\n' : '',
        stderr: '',
        isStdoutTruncated: false,
        isStderrTruncated: false,
      },
    }
  })
  on('fs.stat', () => ({ value: { kind: 'file', size: 0, mtimeMs, isLink: false } }))
  on('fs.exists', () => ({ value: false }))
  on('command.register', () => ({ value: { command: 'dash' } }))
  on('ui.open', () => ({ value: { isPlaced: true } }))
  on('session.start', (_, e) => ({ cwd: e.cwd }))
  on('session.cwd', () => ({ value: '/repo' }))
  on('session.repo', () => ({ value: null }))
  on('session.model', () => ({ value: 'claude-fable-5-2' }))
  on('session.id', () => ({ value: 's1' }))
  on('session.turns', () => ({ value: 0 }))
  on('session.usage', () => ({ value: { context: { percent: 0, tokens: 0, window: 0 }, rateLimits: [], startedAt: 0 } }))
  on('settings.read', () => ({ value: {} }))

  await $.session.start({ cwd: '/repo', surface: 'terminal', isInteractive: true })
  await clock.advance(3000)
  const settled = refreshes
  await clock.advance(3000)
  expect(refreshes).toBe(settled)

  mtimeMs = 2
  await clock.advance(3000)
  expect(refreshes).toBe(settled + 1)
})
