#!/usr/bin/env python3
import sys

with open('run_vtr_flow.py.cmd', 'a') as f:
    f.write(' '.join(sys.argv[1:]) + '\n')
