# Postlab Light Fixture Mapping

Source of truth for the Postlab lighting setup. Channel numbers are DMX addresses as set on the
fixtures (1-based, universe 1). `build.py` reads the **Patch** table below to generate the
Pro DMX 2 project, so edit addresses/names here and re-run it.

## Patch

| Fixture | Profile | Start CH | End CH | Channels |
|---|---|---|---|---|
| Laser | Postlab Laser | 001 | 016 | 16 |
| Moving Head 1 | Postlab Moving Head | 020 | 028 | 9 |
| Moving Head 2 | Postlab Moving Head | 030 | 038 | 9 |
| Hexagon 1 | Postlab Hexagon | 040 | 046 | 7 |
| Hexagon 2 | Postlab Hexagon | 050 | 056 | 7 |
| Hexagon 3 | Postlab Hexagon | 060 | 066 | 7 |
| Hexagon 4 | Postlab Hexagon | 070 | 076 | 7 |
| Hexagon 5 | Postlab Hexagon | 080 | 086 | 7 |
| Hexagon 6 | Postlab Hexagon | 090 | 096 | 7 |
| Hexagon 7 | Postlab Hexagon | 100 | 106 | 7 |
| Hexagon 8 | Postlab Hexagon | 110 | 116 | 7 |
| Smoke | Postlab Smoke | 512 | 512 | 1 |

Free channels: 017-019, 029, 039, 047-049, 057-059, ... (each hexagon block leaves 3 spare), 117-511.

## Profiles

Profiles live in `profiles/` and are installed to `~/Documents/Chromateq/Profiles/Postlab/`.

| Profile | File | Channels | Pro DMX type |
|---|---|---|---|
| Postlab Hexagon | `Postlab Hexagon.cp1` | 7 | LED |
| Postlab Moving Head | `Postlab Moving Head.cp1` | 9 | Moving head |
| Postlab Laser | `Postlab Laser.cp1` | 16 | Laser |
| Postlab Smoke | `Postlab Smoke.cp1` | 1 | Other |

How channels are typed in Pro DMX (this decides which Pro DMX effects/presets drive them):

- **Hexagon**: Dimmer (default 255), R/G/B, Strobe = shutter with presets *No Strobe 0-7* /
  *Strobe 8-255*, Mode = macro with presets for the 6 ranges, Speed = speed.
- **Moving Head**: Pan, Tilt, Color = color wheel, Gobo = gobo wheel, Strobe = shutter,
  Dimmer (default 255), Tilt Speed = speed, Auto = macro, Reset = reset. There are no named
  color/gobo presets yet (DMX ranges unknown). Add them once known.
- **Laser**: Pan X = pan; *Continuous Pan X* = generic control (kept off pan so Pro DMX pan
  effects don't spin it); Pan Y Head 1-3 = tilt (tilt effects move all three heads);
  Pan Speed / Automatic Speed = speed; Dimmer (default 255); Strobe = shutter;
  Automatic Color / Automatic Show = macro; R/G/B/W colors; Reset = reset.
- **Smoke**: smoke channel.

## Rebuilding

```
cd new-setup
python3 build.py             # regenerate profiles/ and postlab-setup.cq5/.ls5
python3 build.py --install   # also copy to ~/Documents/Chromateq (Profiles/Postlab, Projects)
```

## Channel Map

### Laser

```
CH 001  000 - 255  Pan X
CH 002  000 - 255  Continuous Pan X
CH 003  000 - 255  Pan Y Head 1
CH 004  000 - 255  Pan Y Head 2
CH 005  000 - 255  Pan Y Head 3
CH 006  000 - 255  Pan Speed
CH 007  000 - 255  Dimmer
CH 008  000 - 255  Strobe
CH 009  000 - 255  Automatic Color
CH 010  000 - 255  Automatic Show
CH 011  000 - 255  Automatic Speed
CH 012  000 - 255  Red
CH 013  000 - 255  Green
CH 014  000 - 255  Blue
CH 015  000 - 255  White
CH 016  000 - 255  Reset
```

### Moving Head 1

```
CH 020  000 - 255  Pan
CH 021  000 - 255  Tilt
CH 022  000 - 255  Color
CH 023  000 - 255  Gobo
CH 024  000 - 255  Strobe
CH 025  000 - 255  Dimmer
CH 026  000 - 255  Tilt Speed
CH 027  000 - 255  Auto
CH 028  000 - 255  Reset
```

### Moving Head 2

```
CH 030  000 - 255  Pan
CH 031  000 - 255  Tilt
CH 032  000 - 255  Color
CH 033  000 - 255  Gobo
CH 034  000 - 255  Strobe
CH 035  000 - 255  Dimmer
CH 036  000 - 255  Tilt Speed
CH 037  000 - 255  Auto
CH 038  000 - 255  Reset
```

### Hexagon 1

```
CH 040  000 - 255  Dimmer
CH 041  000 - 255  Red Dimmer
CH 042  000 - 255  Green Dimmer
CH 043  000 - 255  Blue Dimmer
CH 044  000 - 007  No Strobe
        008 - 255  Strobe - Larger means Faster
CH 045  000 - 010  Use first 5 channels
        011 - 060  Solid Color Mode
        061 - 110  Gradient Mode
        111 - 160  Pulse Mode
        161 - 210  Jump Mode
        211 - 255  Sound Mode
CH 046  000 - 255  Channel 6 related speed
```

### Hexagon 2

```
CH 050  000 - 255  Dimmer
CH 051  000 - 255  Red Dimmer
CH 052  000 - 255  Green Dimmer
CH 053  000 - 255  Blue Dimmer
CH 054  000 - 007  No Strobe
        008 - 255  Strobe - Larger means Faster
CH 055  000 - 010  Use first 5 channels
        011 - 060  Solid Color Mode
        061 - 110  Gradient Mode
        111 - 160  Pulse Mode
        161 - 210  Jump Mode
        211 - 255  Sound Mode
CH 056  000 - 255  Channel 6 related speed
```

### Hexagon 3

```
CH 060  000 - 255  Dimmer
CH 061  000 - 255  Red Dimmer
CH 062  000 - 255  Green Dimmer
CH 063  000 - 255  Blue Dimmer
CH 064  000 - 007  No Strobe
        008 - 255  Strobe - Larger means Faster
CH 065  000 - 010  Use first 5 channels
        011 - 060  Solid Color Mode
        061 - 110  Gradient Mode
        111 - 160  Pulse Mode
        161 - 210  Jump Mode
        211 - 255  Sound Mode
CH 066  000 - 255  Channel 6 related speed
```

### Hexagon 4

```
CH 070  000 - 255  Dimmer
CH 071  000 - 255  Red Dimmer
CH 072  000 - 255  Green Dimmer
CH 073  000 - 255  Blue Dimmer
CH 074  000 - 007  No Strobe
        008 - 255  Strobe - Larger means Faster
CH 075  000 - 010  Use first 5 channels
        011 - 060  Solid Color Mode
        061 - 110  Gradient Mode
        111 - 160  Pulse Mode
        161 - 210  Jump Mode
        211 - 255  Sound Mode
CH 076  000 - 255  Channel 6 related speed
```

### Hexagon 5

```
CH 080  000 - 255  Dimmer
CH 081  000 - 255  Red Dimmer
CH 082  000 - 255  Green Dimmer
CH 083  000 - 255  Blue Dimmer
CH 084  000 - 007  No Strobe
        008 - 255  Strobe - Larger means Faster
CH 085  000 - 010  Use first 5 channels
        011 - 060  Solid Color Mode
        061 - 110  Gradient Mode
        111 - 160  Pulse Mode
        161 - 210  Jump Mode
        211 - 255  Sound Mode
CH 086  000 - 255  Channel 6 related speed
```

### Hexagon 6

```
CH 090  000 - 255  Dimmer
CH 091  000 - 255  Red Dimmer
CH 092  000 - 255  Green Dimmer
CH 093  000 - 255  Blue Dimmer
CH 094  000 - 007  No Strobe
        008 - 255  Strobe - Larger means Faster
CH 095  000 - 010  Use first 5 channels
        011 - 060  Solid Color Mode
        061 - 110  Gradient Mode
        111 - 160  Pulse Mode
        161 - 210  Jump Mode
        211 - 255  Sound Mode
CH 096  000 - 255  Channel 6 related speed
```

### Hexagon 7

```
CH 100  000 - 255  Dimmer
CH 101  000 - 255  Red Dimmer
CH 102  000 - 255  Green Dimmer
CH 103  000 - 255  Blue Dimmer
CH 104  000 - 007  No Strobe
        008 - 255  Strobe - Larger means Faster
CH 105  000 - 010  Use first 5 channels
        011 - 060  Solid Color Mode
        061 - 110  Gradient Mode
        111 - 160  Pulse Mode
        161 - 210  Jump Mode
        211 - 255  Sound Mode
CH 106  000 - 255  Channel 6 related speed
```

### Hexagon 8

```
CH 110  000 - 255  Dimmer
CH 111  000 - 255  Red Dimmer
CH 112  000 - 255  Green Dimmer
CH 113  000 - 255  Blue Dimmer
CH 114  000 - 007  No Strobe
        008 - 255  Strobe - Larger means Faster
CH 115  000 - 010  Use first 5 channels
        011 - 060  Solid Color Mode
        061 - 110  Gradient Mode
        111 - 160  Pulse Mode
        161 - 210  Jump Mode
        211 - 255  Sound Mode
CH 116  000 - 255  Channel 6 related speed
```

### Smoke

```
CH 512  000 - 255  Smoke output (independent of master dimmer / blackout)
```
