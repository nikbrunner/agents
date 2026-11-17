import { expect, mock, test } from 'claude-code/testing'

test('the band mounts on the terminal', async ($, on) => {
  mock.clock(on, { now: 1_000_000 })
  on('ui.render', ($, e) => $.ui.resolve(e).Box({}))
  on('ui.panes', () => ({ value: [] }))
  for (const requestId of ['dash']) {
    const m = await $.ui.mount({ plugin: 'dash', surface: 'terminal', component: 'AbovePrompt', props: { bodyColumns: 80 }, requestId } as never)
    await (m as { drawn: () => Promise<unknown> }).drawn()
  }
})

test('the band mounts on the desktop without Nerd Font glyphs', async ($, on) => {
  mock.clock(on, { now: 1_000_000 })
  on('ui.render', ($, e) => $.ui.resolve(e).Box({}))
  on('ui.panes', () => ({ value: [] }))
  const m = await $.ui.mount({ plugin: 'dash', surface: 'desktop', component: 'AbovePrompt', props: { bodyColumns: 80 }, requestId: 'dash' } as never)
  const drawn = JSON.stringify(await (m as { drawn: () => Promise<unknown> }).drawn())
  if (/[\uf000-\uf8ff]|[\u{f0000}-\u{fffff}]/u.test(drawn)) throw new Error('private-use glyph on desktop')
  if (!drawn.includes('<svg')) throw new Error('no svg icons on desktop')
})

test('the band steps aside while the pane is placed, and the pane draws the dash', async ($, on) => {
  mock.clock(on, { now: 1_000_000 })
  on('ui.render', ($, e) => $.ui.resolve(e).Box({}))
  on('ui.panes', () => ({ value: [{ id: 'dash', title: 'Dash', isShown: true, isFocused: false, isPlaced: true }] }))
  const band = await $.ui.mount({ plugin: 'dash', surface: 'terminal', component: 'AbovePrompt', props: { bodyColumns: 200 }, requestId: 'dash' } as never)
  if (JSON.stringify(await (band as { drawn: () => Promise<unknown> }).drawn()).includes('model')) throw new Error('band drawn beside the pane')
  const pane = await $.ui.mount({ plugin: 'dash', surface: 'terminal', component: 'Pane', props: { bodyColumns: 60, placement: 'dock' }, requestId: 'dash' } as never)
  if (!JSON.stringify(await (pane as { drawn: () => Promise<unknown> }).drawn()).includes('model')) throw new Error('pane is empty')
})

test('a pane seated inline closes and waits unasked for a dock', async ($, on) => {
  const clock = mock.clock(on, { now: 1_000_000 })
  const calls: string[] = []
  on('ui.render', ($, e) => $.ui.resolve(e).Box({}))
  on('ui.open', (_, e) => (calls.push(`open ${e.id}`), { value: { isPlaced: false, reason: 'narrow' } }))
  on('ui.close', (_, e) => (calls.push(`close ${e.id}`), { value: undefined }))
  const pane = await $.ui.mount({ plugin: 'dash', surface: 'terminal', component: 'Pane', props: { bodyColumns: 90, placement: 'inline' }, viewport: { columns: 90, rows: 40, isFullscreen: true }, requestId: 'dash' } as never)
  await (pane as { drawn: () => Promise<unknown> }).drawn()
  await clock.advance(1)
  expect(calls).toEqual(['close dash', 'open dash'])
})

test('the Review button runs the ponytail review', async ($, on) => {
  mock.clock(on, { now: 1_000_000 })
  const ran: string[] = []
  on('ui.render', ($, e) => $.ui.resolve(e).Box({}))
  on('ui.panes', () => ({ value: [] }))
  on('command.run', { command: 'ponytail:ponytail-review' }, (_, e) => (ran.push(e.command), { text: '' }))
  const band = await $.ui.mount({ plugin: 'dash', surface: 'terminal', component: 'AbovePrompt', props: { bodyColumns: 120 }, requestId: 'dash' } as never)
  await (band as { drawn: () => Promise<unknown> }).drawn()
  await (band as { press: (t: { key: string }) => Promise<unknown> }).press({ key: 'review' })
  expect(ran).toEqual(['ponytail:ponytail-review'])
})
