#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
zwbypass.py — Generate, detect, and strip zero-width / homoglyph obfuscations.

USAGE EXAMPLES (after: chmod +x zwbypass.py)
  # Basic: insert Zero Width Space between every character
  ./zwbypass.py -i "admin" --mode every --zw zwsp

  # Random insertion (50% chance between characters)
  ./zwbypass.py -i "select" --mode random --prob 0.5 --zw zwnj

  # Only split specific keywords *inside* a larger string
  ./zwbypass.py -i "user=admin&role=user" --mode keywords --keywords admin,role --zw zwsp

  # Apply homoglyph swaps (Cyrillic/Greek lookalikes)
  ./zwbypass.py -i "script" --mode homoglyphs

  # URL-encode the final output
  ./zwbypass.py -i "admin" --mode every --encode

  # Detect & visualize zero-widths
  ./zwbypass.py -i "adm\u200bin" --mode detect

  # Strip zero-widths and normalize
  ./zwbypass.py -i "adm\u200cin" --mode strip
"""
import argparse, sys, random, unicodedata
from urllib.parse import quote

ZERO_WIDTH_MAP = {
    "zwsp": "\u200B",   # ZERO WIDTH SPACE
    "zwnj": "\u200C",   # ZERO WIDTH NON-JOINER
    "zwj" : "\u200D",   # ZERO WIDTH JOINER
}
ZW_SET = set(ZERO_WIDTH_MAP.values())

# A modest, practical homoglyph map (avoid over-aggressive substitutions)
HOMOGLYPHS = {
    "a": "а",  # Cyrillic a U+0430
    "c": "с",  # Cyrillic es U+0441
    "e": "е",  # Cyrillic ie U+0435
    "i": "і",  # Cyrillic i U+0456
    "o": "ο",  # Greek omicron U+03BF
    "p": "р",  # Cyrillic er U+0440
    "x": "х",  # Cyrillic ha U+0445
    "y": "у",  # Cyrillic u U+0443
    "h": "һ",  # Cyrillic shha U+04BB
    "k": "κ",  # Greek kappa U+03BA
    "m": "м",  # Cyrillic em U+043C
    "t": "т",  # Cyrillic te U+0442
    "B": "Β",  # Greek Beta
    "E": "Ε",  # Greek Epsilon
    "H": "Η",  # Greek Eta
    "K": "Κ",  # Greek Kappa
    "M": "Μ",  # Greek Mu
    "O": "Ο",  # Greek Omicron
    "P": "Р",  # Cyrillic Er
    "T": "Τ",  # Greek Tau
    "X": "Χ",  # Greek Chi
}

def read_input(args):
    if args.input is not None:
        return args.input
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            return f.read().rstrip("\n")
    return sys.stdin.read().rstrip("\n")

def insert_between_every(s, zwchar, between_alnum_only=True, every_n=1):
    out = []
    for i, ch in enumerate(s):
        out.append(ch)
        if i < len(s)-1:
            if (not between_alnum_only) or (ch.isalnum() and s[i+1].isalnum()):
                if every_n <= 1 or ((i+1) % every_n == 0):
                    out.append(zwchar)
    return "".join(out)

def insert_random(s, zwchar, prob=0.5, between_alnum_only=True):
    out = []
    for i, ch in enumerate(s):
        out.append(ch)
        if i < len(s)-1:
            ok = (not between_alnum_only) or (ch.isalnum() and s[i+1].isalnum())
            if ok and random.random() < prob:
                out.append(zwchar)
    return "".join(out)

def insert_into_keywords(s, keywords, zwchar, case_sensitive=False):
    """
    For each keyword, replace it with a zero-width-split version (e.g., a\u200Bd\u200Bm\u200Bi\u200Bn)
    but leave the rest of the string unchanged.
    """
    flags = 0
    replaced = s
    for kw in keywords:
        if not kw:
            continue
        target = kw if case_sensitive else kw.lower()
        hay = replaced if case_sensitive else replaced.lower()
        # Build split version of kw:
        split_kw = insert_between_every(kw, zwchar, between_alnum_only=False)
        # Manual scan to preserve original casing/segments exactly:
        i = 0
        buf = []
        while i < len(replaced):
            segment = replaced[i:i+len(kw)]
            hay_segment = hay[i:i+len(kw)]
            if hay_segment == target:
                buf.append(split_kw)
                i += len(kw)
            else:
                buf.append(replaced[i])
                i += 1
        replaced = "".join(buf)
    return replaced

def apply_homoglyphs(s):
    return "".join(HOMOGLYPHS.get(ch, ch) for ch in s)

def detect_zero_widths(s, show_hex=True):
    """Return a human-readable visualization and a list of positions."""
    positions = []
    vis = []
    for idx, ch in enumerate(s):
        if ch in ZW_SET:
            positions.append((idx, f"U+{ord(ch):04X} {unicodedata.name(ch,'?')}"))
            tag = "[ZWSP]" if ch == ZERO_WIDTH_MAP["zwsp"] else \
                  "[ZWNJ]" if ch == ZERO_WIDTH_MAP["zwnj"] else "[ZWJ]"
            if show_hex:
                tag += f"(U+{ord(ch):04X})"
            vis.append(tag)
        else:
            vis.append(ch)
    return "".join(vis), positions

def strip_zero_widths(s, norm="NFKC"):
    cleaned = "".join(ch for ch in s if ch not in ZW_SET)
    if norm:
        cleaned = unicodedata.normalize(norm, cleaned)
    return cleaned

def main():
    ap = argparse.ArgumentParser(description="Zero-width / homoglyph obfuscation helper (for authorized testing).")
    ap.add_argument("-i", "--input", help="Input string (or use --file or STDIN).")
    ap.add_argument("-f", "--file", help="Read input from file.")
    ap.add_argument("--mode", choices=["every","random","keywords","homoglyphs","detect","strip"],
                    default="every", help="Operation mode.")
    ap.add_argument("--zw", choices=list(ZERO_WIDTH_MAP.keys()), default="zwsp", help="Zero-width character to inject.")
    ap.add_argument("--prob", type=float, default=0.5, help="Probability for --mode random (0..1).")
    ap.add_argument("--every-n", type=int, default=1, help="Insert after every Nth boundary in --mode every.")
    ap.add_argument("--all-boundaries", action="store_true", help="Insert between any chars (not only alnum).")
    ap.add_argument("--keywords", help="Comma-separated keywords for --mode keywords, or @file to load lines.")
    ap.add_argument("--case-sensitive", action="store_true", help="Case-sensitive keyword matching.")
    ap.add_argument("--encode", action="store_true", help="URL-encode the output.")
    ap.add_argument("-o", "--output", help="Write result to file instead of stdout.")
    args = ap.parse_args()

    random.seed(1337)  # deterministic by default (change if you want true random each run)
    text = read_input(args)

    if args.mode == "detect":
        vis, pos = detect_zero_widths(text)
        print(vis)
        if pos:
            print("\nZero-width positions:")
            for idx, meta in pos:
                print(f"  - index {idx}: {meta}")
        else:
            print("\nNo zero-width characters found.")
        return

    if args.mode == "strip":
        result = strip_zero_widths(text)
    elif args.mode == "homoglyphs":
        result = apply_homoglyphs(text)
    else:
        zwchar = ZERO_WIDTH_MAP[args.zw]
        if args.mode == "every":
            result = insert_between_every(
                text, zwchar,
                between_alnum_only=not args.all_boundaries,
                every_n=args.every_n
            )
        elif args.mode == "random":
            result = insert_random(
                text, zwchar,
                prob=max(0.0, min(1.0, args.prob)),
                between_alnum_only=not args.all_boundaries
            )
        elif args.mode == "keywords":
            # Load keywords
            kws = []
            if args.keywords:
                if args.keywords.startswith("@"):
                    with open(args.keywords[1:], "r", encoding="utf-8") as f:
                        kws = [ln.strip() for ln in f if ln.strip()]
                else:
                    kws = [k.strip() for k in args.keywords.split(",") if k.strip()]
            if not kws:
                print("[-] No keywords provided. Use --keywords 'admin,select,script' or --keywords @file", file=sys.stderr)
                sys.exit(2)
            result = insert_into_keywords(text, kws, ZERO_WIDTH_MAP[args.zw], case_sensitive=args.case_sensitive)
        else:
            print("Invalid mode.", file=sys.stderr); sys.exit(2)

    if args.encode:
        result = quote(result, safe="")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        print(result)

if __name__ == "__main__":
    main()
