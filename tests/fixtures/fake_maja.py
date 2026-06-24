#!/usr/bin/env python3
import argparse, pathlib, sys, time
p=argparse.ArgumentParser(); p.add_argument('--output', required=True); p.add_argument('--sleep', type=float, default=.05); p.add_argument('--fail', action='store_true')
a=p.parse_args(); time.sleep(a.sleep); pathlib.Path(a.output).mkdir(parents=True, exist_ok=True); pathlib.Path(a.output,'PRODUCT_OK.txt').write_text('ok')
sys.exit(3 if a.fail else 0)
