"""Temporary: grab the screen every few seconds and report Power BI Desktop window titles."""
import os
import subprocess
import sys
import time

from PIL import ImageGrab

out = os.path.join(os.environ["TEMP"], "tashots")
os.makedirs(out, exist_ok=True)
n = int(sys.argv[1]) if len(sys.argv) > 1 else 16
step = float(sys.argv[2]) if len(sys.argv) > 2 else 4
ps = "(Get-Process PBIDesktop -ErrorAction SilentlyContinue | ForEach-Object { $_.MainWindowTitle }) -join '|'"
for i in range(n):
    time.sleep(step)
    ImageGrab.grab(all_screens=True).save(os.path.join(out, f"scr_{i:02d}.png"))
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    print(i, repr(r.stdout.strip()), flush=True)
