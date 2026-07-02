#!/bin/bash
cd "$(dirname "$0")"
nohup python3 main-craftfacts.py > /dev/null 2>&1 &
disown
