"""Banc de test du ChordDetector : matrice de confusion des power chords,
rendus avec les samples du mode Studio (le timbre réel du joueur).

Usage :  python tools/bench_chords.py   (depuis guitar_trainer/)
Attendu : diagonale OK, tout le reste rejeté, ERREURS MATRICE : 0.
"""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.analysis.chords import ChordDetector
from src.game.preview import PreviewPlayer

SR, BS = 44100, 512

CHORDS = {
    "E5": [(6, 0), (5, 2)], "F5": [(6, 1), (5, 3)], "G5": [(6, 3), (5, 5)],
    "A5": [(5, 0), (4, 2)], "C5": [(5, 3), (4, 5)], "D5": [(5, 5), (4, 7)],
}

pp = PreviewPlayer()
pp._ensure_loaded()

def render_chord(positions):
    parts = []
    for i, (s, f) in enumerate(sorted(positions, key=lambda p: -p[0])):
        smp = pp._get_sample(s, f)
        parts.append((int(i * 0.012 * SR), smp))
    end = max(off + len(x) for off, x in parts)
    out = np.zeros(end, dtype=np.float32)
    for off, x in parts:
        out[off:off + len(x)] += x * 0.9
    return out

def feed(det, sig):
    det.reset()
    seg = sig[int(0.3 * SR):int(0.3 * SR) + 8192 + BS * 4]
    for b in range(len(seg) // BS):
        det.push(seg[b * BS:(b + 1) * BS])

renders = {name: render_chord(pos) for name, pos in CHORDS.items()}
det = ChordDetector(sample_rate=SR)
names = list(CHORDS)

print("joue \\ attendu |", "  ".join("%4s" % n for n in names))
errors = 0
for played in names:
    row = []
    for expected in names:
        feed(det, renders[played])
        r = det.detect(CHORDS[expected])
        good = r["present"] == (played == expected)
        if not good:
            errors += 1
        row.append(("  OK" if r["present"] else "   .") + ("" if good else "!"))
    print("%13s |" % played, "  ".join("%4s" % c for c in row))

print()
print("=== marges sur la diagonale (salience_db par note, seuil %.0f dB) ===" % det.threshold_db)
for name in names:
    feed(det, renders[name])
    r = det.detect(CHORDS[name])
    print("%3s :" % name, ", ".join(
        "(%d,%d) %.1f dB %+.0f cts" % (n["string"], n["fret"], n["salience_db"], n["cents"])
        for n in r["notes"]))

print()
feed(det, np.zeros(8192 + BS * 4, dtype=np.float32))
print("silence vs E5 :", det.detect(CHORDS["E5"])["present"])
root_only = np.zeros(SR, dtype=np.float32)
s6 = pp._get_sample(6, 0)
root_only[:min(SR, len(s6))] = s6[:SR]
feed(det, root_only)
print("root seule (E2) vs E5 :", det.detect(CHORDS["E5"])["present"])
print()
print("ERREURS MATRICE :", errors)
