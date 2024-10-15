#!/usr/bin/env python
import multiprocessing as mp
import os
import signal
import sys
import time
from argparse import ArgumentParser


# XXX: clumsy, works
def handler(p1: mp.Process, p2: mp.Process, mask_sigterm):
    def _(signum, frame):
        print(f"{signum} received", file=sys.stderr)
        os.kill(p1.pid, signal.SIGTERM)
        os.kill(p2.pid, signal.SIGTERM)
        if mask_sigterm == "child":
            # pretend parent proc know something going wrong in child
            os._exit(1)
        if mask_sigterm == "none":
            os._exit(0)

    return _


def child_handler(signum, frame):
    print(f"{signum} received", file=sys.stderr)


def dummy_loop(mask_sigterm):
    if mask_sigterm:
        signal.signal(signal.SIGTERM, child_handler)
    while True:
        time.sleep(1)


def main(mask_sigterm, sleep_time):
    print(f"parent pid {os.getpid()}")
    child_mask = True if mask_sigterm in ("all", "child") else False
    parent_mask = True if mask_sigterm in ("all", "parent") else False
    p1 = mp.Process(target=dummy_loop, args=(child_mask,))
    p2 = mp.Process(target=dummy_loop, args=(child_mask,))
    p1.start()
    print(f"child 1 pid {p1.pid}")
    p2.start()
    print(f"child 2 pid {p2.pid}")
    print(f"mask_sigterm {mask_sigterm}")
    print(f"child sigterm mask {child_mask}")
    print(f"parent sigterm mask {parent_mask}")
    signal.signal(signal.SIGTERM, handler(p1, p2, mask_sigterm))
    p1.join()
    p2.join()
    if 0 < sleep_time < float("inf"):
        time.sleep(sleep_time)


if __name__ == "__main__":
    parser = ArgumentParser("multi_proc_app")
    parser.add_argument(
        "--mask-sigterm",
        choices=["all", "parent", "child", "none"],
        default="none",
    )
    parser.add_argument("--sleep-time", type=float, default=0)
    args = parser.parse_args()
    print(args)
    main(args.mask_sigterm, args.sleep_time)
