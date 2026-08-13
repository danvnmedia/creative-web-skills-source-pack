#!/usr/bin/env python3
"""Heuristic static scanner for motion/3D frontend red flags.

Usage: python creative_web_static_audit.py <project-path> [--json]
This is not a substitute for runtime profiling; it surfaces code patterns worth review.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

EXTS = {'.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.mjs', '.cjs'}
IGNORE = {'node_modules', '.next', 'dist', 'build', 'coverage', '.git'}

RULES = [
    ('P1', 'react-state-in-useframe', re.compile(r'useFrame\s*\([\s\S]{0,1200}?set[A-Z]\w*\s*\(', re.M), 'Possible React state update inside useFrame; mutate refs for per-frame values.'),
    ('P1', 'uncapped-device-pixel-ratio', re.compile(r'(setPixelRatio\s*\(\s*(?:window\.)?devicePixelRatio|(?:const|let|var)\s+\w*dpr\w*\s*=\s*(?:window\.)?devicePixelRatio\s*;)', re.I), 'Review DPR usage; cap/adapt resolution for heavy canvas scenes.'),
    ('P1', 'per-frame-layout-read', re.compile(r'(requestAnimationFrame|useFrame)\s*\(\s*(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>\s*\{[^}]{0,800}?getBoundingClientRect\s*\(', re.M), 'Layout read appears inside a frame callback; batch/limit measurements.'),
    ('P2', 'scroll-listener', re.compile(r'addEventListener\s*\(\s*[\'\"]scroll[\'\"]', re.I), 'Review scroll listener frequency/passive behavior; prefer native timelines/observer/central scheduler where suitable.'),
    ('P2', 'will-change', re.compile(r'will-change\s*:', re.I), 'Verify will-change is scoped and temporary; overuse increases memory/compositing cost.'),
    ('P2', 'large-fixed-pin', re.compile(r'(pin\s*:\s*true|position\s*:\s*sticky)', re.I), 'Pinned/sticky scene found; verify duration, mobile behavior, and narrative necessity.'),
    ('P2', 'three-shadows', re.compile(r'(castShadow|receiveShadow|shadowMap|<.*Light[^>]*shadow)', re.I), 'Dynamic shadow usage found; review map size/light count and consider baked/fake shadows.'),
    ('P2', 'postprocessing', re.compile(r'(EffectComposer|Bloom|DepthOfField|ChromaticAberration|SSAO)', re.I), 'Post-processing found; tier quality and measure full-screen pass cost.'),
    ('P3', 'layout-property-animation', re.compile(r'(gsap\.(to|fromTo)|animate\s*=)[\s\S]{0,400}?(width|height|top|left|margin|padding)\s*:', re.I), 'Possible layout-property animation; prefer transform where continuous motion is intended.'),
]

REDUCED_MOTION = re.compile(r'prefers-reduced-motion|useReducedMotion', re.I)
THREE_HINT = re.compile(r'@react-three/fiber|from\s+[\'\"]three[\'\"]|<Canvas\b')
MOTION_HINT = re.compile(r'gsap|ScrollTrigger|motion/react|framer-motion|@react-three/fiber|three', re.I)


def files(root: Path):
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        if any(part in IGNORE for part in p.parts):
            continue
        yield p


def line_no(text: str, idx: int) -> int:
    return text.count('\n', 0, idx) + 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('project')
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()
    root = Path(args.project).resolve()
    findings = []
    has_motion = False
    has_reduced = False
    has_three = False
    scanned = 0
    for p in files(root):
        scanned += 1
        try:
            text = p.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        has_motion |= bool(MOTION_HINT.search(text))
        has_reduced |= bool(REDUCED_MOTION.search(text))
        has_three |= bool(THREE_HINT.search(text))
        for severity, rule, rx, message in RULES:
            for m in rx.finditer(text):
                findings.append({
                    'severity': severity,
                    'rule': rule,
                    'file': str(p.relative_to(root)),
                    'line': line_no(text, m.start()),
                    'message': message,
                })
    if has_motion and not has_reduced:
        findings.append({'severity':'P1','rule':'missing-reduced-motion','file':'(project)','line':0,'message':'Motion/3D code detected but no prefers-reduced-motion or useReducedMotion reference found.'})
    if has_three:
        findings.append({'severity':'INFO','rule':'runtime-profile-required','file':'(project)','line':0,'message':'3D code detected: verify draw calls, DPR, texture memory, frame time, offscreen pause, and resource disposal at runtime.'})
    order = {'P0':0,'P1':1,'P2':2,'P3':3,'INFO':4}
    findings.sort(key=lambda x:(order.get(x['severity'],9), x['file'], x['line']))
    out = {'root': str(root), 'files_scanned': scanned, 'findings': findings}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"Creative Web Static Audit: {root}")
        print(f"Files scanned: {scanned}; findings: {len(findings)}")
        for f in findings:
            loc = f"{f['file']}:{f['line']}" if f['line'] else f['file']
            print(f"[{f['severity']}] {f['rule']} — {loc}\n  {f['message']}")

if __name__ == '__main__':
    main()
