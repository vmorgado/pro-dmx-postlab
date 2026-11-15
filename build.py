#!/usr/bin/env python3
"""Build Pro DMX 2 (Chromateq) profiles and project for the Postlab setup.

Source of truth: postlab-lights.md (the "Patch" table drives fixture names and addresses).
Channel functions follow lights.md / postlab-lights.md; the Pro DMX channel *types* below are
the closest Chromateq equivalents.

Outputs (next to this script):
  profiles/<Profile>.cp1     one profile per fixture type
  postlab-setup.cq5/.ls5     Pro DMX 2 project with every fixture patched

  python3 build.py              build into new-setup/
  python3 build.py --install    also copy into ~/Documents/Chromateq (never overwrites
                                files that differ unless --force is given)

File formats (reverse engineered from Pro DMX 2.3.4 files):
  .cp1  4-byte big-endian uncompressed length + zlib-compressed XML
  .ls5  same container as .cp1
  .cq5  plain XML; profiles are embedded in <LPPatch>, LPAddress is 0-based
"""
import argparse
import re
import shutil
import sys
import zlib
from pathlib import Path
from xml.sax.saxutils import quoteattr

HERE = Path(__file__).resolve().parent
MD = HERE / "postlab-lights.md"
PROFILE_DIR = HERE / "profiles"
PROJECT_NAME = "postlab-setup"
CHROMATEQ = Path.home() / "Documents" / "Chromateq"
LIB_SUBDIR = "Postlab"  # profiles are installed to Profiles/Postlab/

# --- Pro DMX constants -------------------------------------------------------------------
# Channel types (LPChannelType), derived from the stock profile library.
PAN, TILT, ROTATION, COLOR_WHEEL, DIMMER, GOBO, SHUTTER, SPEED = 1, 2, 4, 5, 7, 8, 15, 18
SMOKE, RED, GREEN, BLUE, WHITE, MACRO, CONTROL, RESET = 24, 25, 26, 27, 31, 33, 34, 38
# Fixture types (LPFixtType)
FT_LED, FT_MH, FT_LASER, FT_OTHER = 0, 3, 4, 5


def preset(name, start, end, ptype=0, icon="", default=None, **extra):
    a = {
        "LPPresetName": name,
        "LPPresetDmxStart": start,
        "LPPresetDmxEnd": end,
        "LPPresetType": ptype,
        "LPPresetIcon": icon,
        "LPPresetDmxDefault": (start + end) // 2 if default is None else default,
        "LPPresetDefaultPreset": 0,
    }
    a.update(extra)
    return a


DIMMER_PRESET = preset("Dimmer", 0, 255, 4, "System/Presets/Dimmer/Dimmer.png", 255,
                       LPPresetDefaultPreset=1, LPPresetParamMin=0, LPPresetParamMax=100)


def ch(name, ctype, presets=(), **extra):
    return {"name": name, "type": ctype, "presets": list(presets), "extra": extra}


PROFILES = {
    "Postlab Hexagon": {
        "mode": "7ch", "fixt_type": FT_LED, "obj": "System/3D/LED/LED5.png", "pic": "LED 4",
        "size": (38, 38, 7),
        "channels": [
            ch("Dimmer", DIMMER, [DIMMER_PRESET]),
            ch("Red", RED),
            ch("Green", GREEN),
            ch("Blue", BLUE),
            ch("Strobe", SHUTTER, [
                preset("No Strobe", 0, 7, 19, "System/Presets/Shutter/ShutterOpen.png", 0),
                preset("Strobe", 8, 255, 21, "System/Presets/Shutter/ShutterStrob.png",
                       LPPresetParamMin=0, LPPresetParamMax=250, LPPresetEffectType=0),
            ]),
            ch("Mode", MACRO, [
                preset("Use first 5 channels", 0, 10, 0, "System/Presets/DMX.png", 0),
                preset("Solid Color Mode", 11, 60, 0, "System/Presets/Color.png"),
                preset("Gradient Mode", 61, 110, 0, "System/Presets/Auto/Auto1.png"),
                preset("Pulse Mode", 111, 160, 0, "System/Presets/Auto/Auto2.png"),
                preset("Jump Mode", 161, 210, 0, "System/Presets/Auto/Auto3.png"),
                preset("Sound Mode", 211, 255, 0, "System/Presets/Sound.png"),
            ]),
            ch("Speed", SPEED, LPChannelTarget=5, LPChannelParamMin=10000, LPChannelParamMax=0),
        ],
    },
    "Postlab Moving Head": {
        "mode": "9ch", "fixt_type": FT_MH, "obj": "System/3D/MH/MH1.png", "pic": "MOVING HEAD 1",
        "size": (50, 50, 50),
        "channels": [
            ch("Pan", PAN),
            ch("Tilt", TILT),
            ch("Color", COLOR_WHEEL),
            ch("Gobo", GOBO),
            ch("Strobe", SHUTTER),
            ch("Dimmer", DIMMER, [DIMMER_PRESET]),
            ch("Tilt Speed", SPEED),
            ch("Auto", MACRO),
            ch("Reset", RESET),
        ],
    },
    "Postlab Laser": {
        "mode": "16ch", "fixt_type": FT_LASER, "obj": "System/3D/LASER/LASER1.png", "pic": "LASER 1",
        "size": (50, 50, 50),
        "channels": [
            ch("Pan X", PAN),
            # Not typed as Pan, so Pro DMX pan effects don't also drive the continuous rotation.
            ch("Continuous Pan X", CONTROL),
            ch("Pan Y Head 1", TILT),
            ch("Pan Y Head 2", TILT),
            ch("Pan Y Head 3", TILT),
            ch("Pan Speed", SPEED),
            ch("Dimmer", DIMMER, [DIMMER_PRESET]),
            ch("Strobe", SHUTTER),
            ch("Automatic Color", MACRO),
            ch("Automatic Show", MACRO),
            ch("Automatic Speed", SPEED),
            ch("Red", RED),
            ch("Green", GREEN),
            ch("Blue", BLUE),
            ch("White", WHITE, LPChannelColorMin=0, LPChannelColorMax=16777215),
            ch("Reset", RESET),
        ],
    },
    "Postlab Smoke": {
        "mode": "1ch", "fixt_type": FT_OTHER, "obj": "System/3D/OTHER/OTHER1.png", "pic": "",
        "size": (20, 20, 20),
        "channels": [
            ch("Smoke", SMOKE),
        ],
    },
}


# --- XML helpers -------------------------------------------------------------------------
def attrs(d):
    return " ".join(f"{k}={quoteattr(str(v))}" for k, v in d.items())


def profile_body(prof, fixt_path, indent):
    """<LPProfile> element as Pro DMX 2.3.4 writes it (inside a .cp1 or a .cq5 <LPLibrary>)."""
    p = " " * indent
    sx, sy, sz = prof["size"]
    props = {
        "LPName": prof["mode"], "LPFixtType": prof["fixt_type"], "LP3DObject": prof["obj"],
        "LPPicturePath": prof["pic"], "LPPictureIndex": 0, "LPSizeX": sx, "LPSizeY": sy,
        "LPSizeZ": sz, "LPIntensity": 10, "LPBeamClr": 65280, "LPBeamOpening": 16,
        "LPBeamNumber": 1, "LPBeamNumberY": 0, "LPMatrixProfile": 0, "LPDim": 0,
        "LPAmpliPan": 540, "LPAmpliTilt": 270, "LPTimePan": 0, "LPTimeTilt": 0, "LPPanTiltRot": 0,
    }
    chans = prof["channels"]
    out = [
        f'{p}<LPProfile LPFixtPath={quoteattr(fixt_path)}>',
        f'{p} <LPModes LPNbMode="1">',
        f'{p}  <LPMode LPNbChannel="{len(chans)}">',
        f'{p}   <LPProperties {attrs(props)}>',
        f'{p}    <LPBeams LPNbBeam="1">',
        f'{p}     <LPBeam LPBeamZoom="100" LPBeamPosX="0" LPBeamPosY="0" LPShapeType="0"/>',
        f'{p}    </LPBeams>',
        f'{p}   </LPProperties>',
    ]
    for c in chans:
        ca = {"LPChannelName": c["name"], "LPChannelType": c["type"], "LPChannelMSB": 0,
              "LPChannelLSB": 0, "LPChannelCommon": 1, **c["extra"]}
        out.append(f'{p}   <LPChannel {attrs(ca)}>')
        if c["presets"]:
            out.append(f'{p}    <LPPresets LPNbPreset="{len(c["presets"])}">')
            out += [f'{p}     <LPPreset {attrs(pr)}/>' for pr in c["presets"]]
            out.append(f'{p}    </LPPresets>')
        else:
            out.append(f'{p}    <LPPresets LPNbPreset="0"/>')
        out.append(f'{p}   </LPChannel>')
    out += [f'{p}  </LPMode>', f'{p} </LPModes>', f'{p}</LPProfile>']
    return out


def pack(xml_text):
    """Chromateq container: 4-byte BE length + zlib stream."""
    raw = xml_text.encode("utf-8")
    return len(raw).to_bytes(4, "big") + zlib.compress(raw)


def unpack(data):
    if data.startswith(b"<"):
        return data.decode("utf-8")
    n = int.from_bytes(data[:4], "big")
    raw = zlib.decompress(data[4:])
    assert len(raw) == n, "length header mismatch"
    return raw.decode("utf-8")


def lib_path(name):
    return f"{LIB_SUBDIR}/{name}.cp1"


def build_cp1(name):
    lines = ['<LPFile Version="2.1">'] + profile_body(PROFILES[name], lib_path(name), 1) + ["</LPFile>"]
    return "\n".join(lines) + "\n"


# --- Patch table from the markdown -------------------------------------------------------
def read_patch():
    text = MD.read_text()
    m = re.search(r"^## Patch\s*\n(.*?)(?=^## )", text, re.S | re.M)
    if not m:
        sys.exit(f"No '## Patch' section in {MD}")
    rows = []
    for line in m.group(1).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or not cells[2].isdigit():
            continue
        name, prof, start, end = cells[0], cells[1], int(cells[2]), int(cells[3])
        if prof not in PROFILES:
            sys.exit(f"{name}: unknown profile '{prof}' (known: {', '.join(PROFILES)})")
        n = len(PROFILES[prof]["channels"])
        if end != start + n - 1:
            sys.exit(f"{name}: CH {start}-{end} doesn't match {prof} ({n} channels)")
        if not (1 <= start and end <= 512):
            sys.exit(f"{name}: CH {start}-{end} outside 1-512")
        rows.append((name, prof, start))
    used = {}
    for name, prof, start in rows:
        for c in range(start, start + len(PROFILES[prof]["channels"])):
            if c in used:
                sys.exit(f"CH {c} used by both {used[c]} and {name}")
            used[c] = name
    return rows


# --- Project (.cq5 / .ls5) ---------------------------------------------------------------
DEFAULT_EFFECTS_SRC = HERE / "templates" / "default-effects.xml"  # Pro DMX's stock effect buttons


def default_effects_xml():
    """Reuse the stock effect buttons (RGB, Rainbow, ...) that Pro DMX adds to new projects."""
    if not DEFAULT_EFFECTS_SRC.exists():
        return [' <LPEffScenes LPNumber="0"/>'], []
    block = DEFAULT_EFFECTS_SRC.read_text().rstrip("\n")
    names = re.findall(r'<LPEffScene [^>]*LPName="([^"]*)"', block)
    return block.splitlines(), names


def build_cq5(rows):
    o = ['<LPFile Version="2.1">',
         ' <LPParams LPChannelOffset="0" LPDisplayMode="0" LPDefaultStartScenes="-1|-1|-1|-1|-1" '
         'LPDrawPicture="0" LPSAAreas="-1|-1|-1|-1|-1" LPPicture="" LPLiveBoard="0" ShowVersion="2.3.4">',
         '  <LPEffectsTrigger LPMidiFeedBack="0" LPAutoRelease="0" LPOnOff="1" LPPlayInCurPage="1"/>',
         ' </LPParams>',
         f' <LPPatch LPNumber="{len(rows)}">']
    # fixture ids are 1-based in patch order; layout: one row per profile type in the fixture view
    by_prof = {}
    for fid, (name, prof, start) in enumerate(rows, 1):
        by_prof.setdefault(prof, []).append((fid, name, start))
    row_of = {p: i for i, p in enumerate(by_prof)}
    for prof, fixtures in by_prof.items():
        o.append('  <LPFixtures>')
        o.append(f'   <LPLibrary LPName={quoteattr(lib_path(prof))} LPMatrixId="-1">')
        o += profile_body(PROFILES[prof], lib_path(prof), 4)
        o.append('   </LPLibrary>')
        for col, (fid, name, start) in enumerate(fixtures):
            fx = {"LPName": name, "LPId": fid, "LPUniverse": 0, "LPAddress": start - 1,
                  "LPAngle": 0, "LPRdmId": 0, "LPInvPan": 0, "LPInvTilt": 0,
                  "LPGroupParams": f"{60 + 80 * col};{60 + 80 * row_of[prof]};100;2"}
            o.append(f'   <LPFixture {attrs(fx)}/>')
        o.append('  </LPFixtures>')
    o.append(' </LPPatch>')

    trig = '<LPMainTrigger LPMidiFeedBack="0" LPAutoRelease="0" LPOnOff="1" LPPlayInCurPage="1"/>'
    o += [' <LPGroups LPNumber="1">',
          '  <LPGlobalGroup LPSceneImageMode="0" LPSceneDrawImageBack="0" LPGrpSel="1;1" '
          'LPSceneColorSel="4618470" LPName="General" LPSceneBorderSel="2" LPPage="-1" '
          'LPSceneDrawGrid="0" LPSceneImageBack="" LPSceneRectY="400" LPSceneColorBack="16777215" '
          'LPZoom="100" LPSceneRectX="800" LPScrollY="0" LPScrollX="0" LPSceneMagnetGrid="0" LPScale="130">',
          '   <LPMainTrigger LPMidiFeedBack="0" LPAutoRelease="0" LPOnOff="1" LPShortCut="F1" '
          'LPPlayInCurPage="0" LPDmxTrigger="1|0|0|127|127|255"/>',
          f'   <LPSubGroups LPNumber="{len(rows)}">']
    for fid, (name, prof, start) in enumerate(rows, 1):
        sg = {"LPPosX": fid - 1, "LPPosY": 0, "LPName": name, "LPBeams": f"{fid};1", "CQColor": 6579300}
        o += [f'    <LPSubGroup {attrs(sg)}>', f'     {trig}', '    </LPSubGroup>']
    o += ['   </LPSubGroups>', '   <LPPresetConfigs>']
    for prof in by_prof:
        o.append(f'    <LPProfileConfig LPFixtPath={quoteattr(lib_path(prof))}>')
        seen = []
        for c in PROFILES[prof]["channels"]:
            if c["type"] not in seen:
                seen.append(c["type"])
                o.append(f'     <LPPresetConfig LPPosX="-1" LPShowLSB="0" LPChannel="{c["type"]}" '
                         'LPChanIndType="0" LPDisplayType="2" LPPrIconSize="32"/>')
        o.append('    </LPProfileConfig>')
    o += ['   </LPPresetConfigs>', '  </LPGlobalGroup>', ' </LPGroups>']

    sa = '      <LPSaData LPSASceneIndex="-1" LPMemory="0"/>'
    o += [' <LPPages LPNumber="1">',
          '  <LPPage LPDisplayMode="0" LPName="Scenes" LPLiveFloating="0" LPDrawPicture="0" '
          'LPFloating="0" LPPicture="" LPLiveBoard="1" LPDefaultTab="0">',
          f'   {trig}',
          '   <LPScenes LPNumber="1">',
          '    <LPScene LPFadeOutDelay="0" LPRelease="0" LPName="Scene 1" LPLoop="0" LPSoundState="0" '
          'LPFadeOutList="0" LPFadeOutId="-1" LPSoundCoeff="25" LPSoundMode="0" LPCustomFadeIn="0" '
          'LPBeatMode="0" LPDisplayTime="1" LPDisplayClr="13804915" LPFadeIn="0" LPFadeOut="0" '
          'LPDefaultButPic="1" LPSound="" LPDisplayParams="1" LPFadeInList="0" LPCheckInList="0" '
          'LPDynamicFadeIn="1" LPPlaySound="0" LPCustomFadeOut="0" LPButtonSize="2" LPBeatState="0" '
          'LPDynamicFadeOut="1" LPSoundType="-1" LPBeatType="-1" LPFadeInId="-1" LPCheckOutList="0" '
          'LPFadeInDelay="0" LPJumpMode="0" LPPosX="0" LPPosY="0" LPDisplayName="1" LPPwd="" LPPriority="1">',
          '     <LPSaDatas LPNumber="5">', *[sa] * 5, '     </LPSaDatas>',
          f'     {trig}',
          '     <LPActivUniverses LPNumber="4">',
          f'      <LPActivUniverse LPActivBuffer="{"0" * 1024}" LPUniverse="0"/>',
          '     </LPActivUniverses>',
          '     <LPSteps LPNumber="0"/>',
          '    </LPScene>', '   </LPScenes>', '  </LPPage>', ' </LPPages>']

    eff_lines, eff_names = default_effects_xml()
    o += eff_lines
    o += [' <LPFadingButs LPNumber="0"/>',
          ' <LPTimeShow LPNumber="1">',
          '  <LPTimeLines LPTLKeepPlaying="0" LPTLPage="-1" LPTLLock="0" LPTName="New" LPNumber="3" '
          'LPTLLoop="1" LPTLFollowCursor="1" LPTLPlayLen="0" LPTLLockMarker="0" LPTLReleaseAll="0" '
          'LPTAudioDev="" LPTLMoveMarker="1" LPTLPlayFrom="1" LPTLen="900000">',
          f'   {trig}',
          '   <LPTimeLine LPName="Music" Type="1" LPTLDisplay="1" LPTLSound="1"/>',
          '   <LPTimeLine LPName="Video" Type="2" LPTLDisplay="1" LPTLSound="0"/>',
          '   <LPTimeLine LPName="Line 1" Type="0"/>',
          '  </LPTimeLines>',
          ' </LPTimeShow>',
          # The CQSA 512 interface from the earlier postlab project.
          ' <LPDevicesConfig LPNumber="1">',
          '  <LPDevice LPDevCom="0" LPHwUniverses="2" LPStrSerial="B09507" LPDevName="" LPShortName="" '
          'LPDevConfig="2|0|2|0|0|-1|0|-1" LPDevGateWay="" LPDevSaMode="0" LPDevSerial="9507" '
          'LPLongName="" LPMergeInOut="0" LPDevSpeed="45|146|0|1" LPNodeUniverses="-1|-1|-1|-1|-1" '
          'LPDevRef="CQSA 512" LPFirmware="2.4.2.6" LPDevType="12" LPDmxInChan="512" LPDevIp="" '
          'LPDevMask="" LPDHCP="0" LPUniverses="2" LPSubNet="0"/>',
          ' </LPDevicesConfig>',
          '</LPFile>']
    return "\n".join(o) + "\n", eff_names


def build_ls5(eff_names):
    scene = ('LPBeamOn="0" LPName={} LPSpeed="50" LPDimmer="50" LPPhasing="0" LPLiveTilt="0" '
             'LPLivePanTilt="0" LPBlOut="0" LPPause="0" LPLivePan="0" LPLiveColor="0" CQColor="0|0|0|0|0|0"')
    o = ['<LPFile Version="2.1">',
         ' <LPParams LPEFScale="70" LPGroupsTab="0" LPPagesTab="1" LPLiveLevels="0|0|0"/>',
         ' <LPPages LPNumber="1">',
         '  <LPPage LPName="Scenes" LPScale="70">',
         '   <LPScenes LPNumber="1">',
         f'    <LPScene LPPlayingScene="0" {scene.format(quoteattr("Scene 1"))}/>',
         '   </LPScenes>',
         '  </LPPage>',
         ' </LPPages>',
         f' <LPEffScenes LPNumber="{len(eff_names)}">',
         *[f'  <LPEffScene {scene.format(quoteattr(n))}/>' for n in eff_names],
         ' </LPEffScenes>',
         ' <LPTimeShow LPNumber="1" LPTLOnTop="1" LPTLVisible="0" LPTLCurTab="0" LPTLMaximized="0" '
         'LPTLRcVideo="0|0|0|0" LPTLPlaying="0">',
         '  <LPTimeLines LPNumber="3" LPTLZoomPos="-2147483648|-2147483648" LPTLCurTime="0"/>',
         ' </LPTimeShow>',
         '</LPFile>']
    return "\n".join(o) + "\n"


# --- main --------------------------------------------------------------------------------
def install(src, dst, force):
    if dst.exists() and dst.read_bytes() != src.read_bytes() and not force:
        print(f"  SKIP {dst} (exists and differs; use --force)")
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    print(f"  installed {dst}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true", help="copy into ~/Documents/Chromateq")
    ap.add_argument("--force", action="store_true", help="overwrite differing installed files")
    args = ap.parse_args()

    rows = read_patch()
    PROFILE_DIR.mkdir(exist_ok=True)
    outputs = []
    for name in PROFILES:
        f = PROFILE_DIR / f"{name}.cp1"
        f.write_bytes(pack(build_cp1(name)))
        assert unpack(f.read_bytes()) == build_cp1(name)
        outputs.append((f, CHROMATEQ / "Profiles" / lib_path(name)))
    cq5, eff = build_cq5(rows)
    for ext, data in (("cq5", cq5.encode()), ("ls5", pack(build_ls5(eff)))):
        f = HERE / f"{PROJECT_NAME}.{ext}"
        f.write_bytes(data)
        outputs.append((f, CHROMATEQ / "Projects" / f.name))

    for f, _ in outputs:
        print(f"built {f.relative_to(HERE)}")
    print(f"patched {len(rows)} fixtures:")
    for name, prof, start in rows:
        print(f"  {name:<14} {prof:<20} CH {start:03d}-{start + len(PROFILES[prof]['channels']) - 1:03d}")
    if args.install:
        for src, dst in outputs:
            install(src, dst, args.force)


if __name__ == "__main__":
    main()
