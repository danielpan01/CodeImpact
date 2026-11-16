"""Trusted failure-injection process for worker lifecycle tests, never uploaded source."""

import json
import os
import sys
import time

mode = sys.argv[1]
if mode == "wait":
    time.sleep(30)
elif mode == "memory":
    blocks = []
    for _ in range(100):
        blocks.append(bytearray(1024 * 1024))
        time.sleep(0.005)
    time.sleep(30)
elif mode == "output":
    for _ in range(200):
        sys.stdout.buffer.write(b"x" * 65536)
        sys.stdout.buffer.flush()
elif mode == "invalid":
    sys.stdout.write('{"secret": "do not reflect worker output"}')
elif mode == "exit":
    sys.exit(1)
elif mode == "environment":
    sys.stdout.write(json.dumps(dict(os.environ)))
elif mode in {"cpu", "address_space"}:
    from codeimpact.worker import apply_limits

    if mode == "cpu":
        apply_limits(1, 1024 * 1024 * 1024)
        while True:
            pass
    else:
        apply_limits(15, 64 * 1024 * 1024)
        try:
            blocks = [bytearray(1024 * 1024) for _ in range(200)]
        except MemoryError:
            sys.exit(75)
