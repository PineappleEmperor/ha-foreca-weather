## AI sessions
Before writing or modifying integration code (config flow, platforms, manifest,
websocket, services…), invoke the `ha-integration` skill. Re-invoke it after any
`/compact`, since compaction can drop the skill's guidance from context.

## Git hooks
Run `git config core.hooksPath .githooks` once in every clone.
