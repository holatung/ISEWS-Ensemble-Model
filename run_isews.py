#!/usr/bin/env python3
"""
ISEWS - Internet Shutdown Early Warning System (ChatVE) - prototype runner.

    python run_isews.py                 # full run, writes output/isews_report.html + output/isews_results.json
    python run_isews.py --fast          # smaller training sets, about 10 s
    python run_isews.py --fragment      # also writes a body-only HTML fragment for embedding
"""
import argparse, json, os, pickle, sys
from isews.pipeline import run
from isews.report import render


def main():
    ap = argparse.ArgumentParser(description="ISEWS prototype")
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="output")
    ap.add_argument("--fragment", action="store_true")
    ap.add_argument("--from-pickle", default=None, help="re-render from a saved results pickle")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    if a.from_pickle:
        R = pickle.load(open(a.from_pickle, "rb"))
    else:
        R = run(seed=a.seed, n_train=3000 if a.fast else 9000, n_test=1000 if a.fast else 3000,
                epochs=8 if a.fast else 25)
        pickle.dump(R, open(os.path.join(a.out, "isews_results.pkl"), "wb"))
    slim = {k: v for k, v in R.items() if k != "scenarios"}
    slim["scenarios"] = [{k: v for k, v in s.items() if k not in ("P",)} for s in R["scenarios"]]
    json.dump(slim, open(os.path.join(a.out, "isews_results.json"), "w"), indent=1, default=float)
    open(os.path.join(a.out, "isews_report.html"), "w").write(render(R, full=True))
    if a.fragment:
        open(os.path.join(a.out, "isews_report_fragment.html"), "w").write(render(R, full=False))
    print(f"Report written to {os.path.join(a.out, 'isews_report.html')}")


if __name__ == "__main__":
    sys.exit(main())
