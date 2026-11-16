# Postlab Pro DMX

Fixture profiles and a ready-to-open Chromateq **Pro DMX 2** project for the Postlab lighting
rig: 1 laser, 2 moving heads, 8 hexagons and a smoke machine on one DMX universe.

The fixture map lives in [`postlab-lights.md`](postlab-lights.md). `build.py` turns it into the
`.cp1` profiles and the `.cq5` project, so the md, the profiles and the project always agree.

## Quick start

1. Clone the repo and install into Pro DMX:

   ```sh
   git clone git@github.com:vmorgado/pro-dmx-postlab.git
   cd pro-dmx-postlab
   python3 build.py --install
   ```

   This copies the profiles to `~/Documents/Chromateq/Profiles/Postlab/` and the project to
   `~/Documents/Chromateq/Projects/postlab-setup.cq5`.
2. In Pro DMX 2, open `postlab-setup.cq5`. All 12 fixtures are already patched.
3. Set each fixture's DMX address to match the patch below, and connect the CQSA 512 interface.

You only need Python 3. There are no other dependencies.

## Patch

| Fixture | Profile | DMX channels |
|---|---|---|
| Laser | Postlab Laser | 001–016 |
| Moving Head 1 | Postlab Moving Head | 020–028 |
| Moving Head 2 | Postlab Moving Head | 030–038 |
| Hexagon 1–8 | Postlab Hexagon | 040, 050, 060 … 110 (7 channels each) |
| Smoke | Postlab Smoke | 512 |

The channel-by-channel map for every fixture is in [`postlab-lights.md`](postlab-lights.md).

## Changing the patch

1. Edit the **Patch** table in `postlab-lights.md`. Change a start or end channel, rename a
   fixture, or add a row to add a fixture.
2. Rebuild:

   ```sh
   python3 build.py             # regenerate into this repo only
   python3 build.py --install   # also copy into ~/Documents/Chromateq
   ```

`build.py` stops with an error if two fixtures share a channel, if a row's channel count doesn't
match its profile, or if a channel falls outside 1–512.

> **Before you program scenes:** `build.py` writes a fresh project containing only the patch.
> Once you've built scenes in Pro DMX, change the patch inside Pro DMX instead, or save under a
> new name first. `--install` won't overwrite an installed file that differs from the build
> unless you add `--force`, and `--force` replaces your scenes.

## Changing a profile

Profiles are defined in the `PROFILES` dictionary in `build.py`. Each channel has a name, a
Pro DMX channel type and optional presets. For example, to give the moving head's Color channel
named colors once you know the DMX ranges:

```python
ch("Color", COLOR_WHEEL, [
    preset("White", 0, 9),
    preset("Red", 10, 19, 1, LPPresetColor=255),   # color is BGR: 0xBBGGRR
    preset("Green", 20, 29, 1, LPPresetColor=65280),
]),
```

Update the channel map in `postlab-lights.md` to match, then rebuild.

How each channel is typed in Pro DMX matters because effects use the type. For example, the
laser's three *Pan Y* heads are typed as tilt so tilt effects move all three together. The full
list is in `postlab-lights.md`.

## Repository layout

| Path | What it is |
|---|---|
| `postlab-lights.md` | Source of truth: patch table and channel map |
| `build.py` | Generates profiles and project, optionally installs them |
| `profiles/*.cp1` | Pro DMX fixture profiles (generated) |
| `postlab-setup.cq5`, `.ls5` | Pro DMX 2 project (generated) |
| `templates/default-effects.xml` | The stock effect buttons Pro DMX puts in new projects |
| `docs/index.html` | This guide as a web page |

## File formats

Chromateq doesn't document these formats. They were worked out from files Pro DMX 2.3.4 writes,
and `build.py` reproduces Pro DMX's own files byte for byte.

- **`.cp1` / `.ls5`**: a 4-byte big-endian length, followed by zlib-compressed XML.
- **`.cq5`**: plain XML. The profiles are embedded in `<LPPatch>`, and `LPAddress` counts from 0,
  so DMX channel 40 is stored as `LPAddress="39"`.

## Open items

- Hexagons 6–8 are placed at CH 090/100/110 following the pattern of the first five. Confirm them
  against the fixtures.
- Check whether the smoke machine (CH 512) keeps running during blackout. If it doesn't, add a
  DMX mask in Pro DMX.
- The moving heads have no named color or gobo presets yet because their DMX ranges are unknown.
