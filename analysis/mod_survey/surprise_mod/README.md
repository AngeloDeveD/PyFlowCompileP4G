# Surprise Mod: Night Bonus Note

This is a small field-hook test mod built from the patterns found in community
Persona 4 Golden mods.

What it does:

- Hooks `call_lmap` in `f007`.
- Only triggers at night.
- Shows a custom selection before the normal home-exit logic.
- Lets the player pick one small bonus:
  - `3000 yen`
  - `Courage +`
  - `Knowledge +`
  - `Ignore`
- After the custom choice, the original `call_lmap` behavior continues.

Why this mod is useful:

- It uses the same hook pattern as the working `p4gscript.test_mode_dialog`
  smoke test.
- It demonstrates a practical combination of:
  - original-script import
  - hook procedure
  - message window
  - selection dialog
  - yen reward
  - social stat reward
  - continue-into-original behavior with `*_unhooked()`

Files:

- `Source/f007_night_bonus.flow`
- `Source/f007_night_bonus.msg`
- `build_surprise_mod.ps1`

Build output:

- `build/f007.bf`
- `FEmulator/PAK/field/pack/fd007_001.arc/f007.bf`
- `FEmulator/PAK/field/pack/fd007_002.arc/f007.bf`

Dependencies at runtime:

- `p5rpc.modloader`
- `reloaded.universal.fileemulationframework.pak`
