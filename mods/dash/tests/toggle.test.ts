import { expect, test } from 'claude-code/testing'

test('/dash alternates between hiding and showing', async $ => {
  const run = () => $.command.run({ command: 'dash', args: '' } as never) as Promise<unknown>
  expect(await run()).toMatchObject({ text: 'Dash hidden.' })
  expect(await run()).toMatchObject({ text: 'Dash shown.' })
  expect(await run()).toMatchObject({ text: 'Dash hidden.' })
})
