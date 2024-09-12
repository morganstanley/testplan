#!/usr/bin/env python
import multiprocessing as mp
import os
import signal
import sys
import time
from argparse import ArgumentParser


def handler(p1: mp.Process, p2: mp.Process, mask_sigterm, term_child):
    def _(signum, frame):
        print(f"{signum} received", file=sys.stderr)
        if term_child:
            p1.terminate()
            p2.terminate()
            print("p1 terminated", file=sys.stderr)
            print("p2 terminated", file=sys.stderr)
        if not mask_sigterm:
            signal.signal(signal.SIGTERM, signal.SIG_DFL)
            os.kill(os.getpid(), signal.SIGTERM)

    return _


def child_handler(signum, frame):
    print(f"{signum} received", file=sys.stderr)


def dummy_loop(mask_sigterm):
    if mask_sigterm:
        signal.signal(signal.SIGTERM, child_handler)
    while True:
        time.sleep(1)


def main(mask_sigterm, sleep_time, term_child):
    print(f"curr pid {os.getpid()}")
    child_mask = True if mask_sigterm == "all" else False
    p1 = mp.Process(target=dummy_loop, args=(child_mask,))
    p2 = mp.Process(target=dummy_loop, args=(child_mask,))
    p1.start()
    print(f"child 1 pid {p1.pid}")
    p2.start()
    print(f"child 2 pid {p2.pid}")
    parent_mask = True if mask_sigterm != "none" else False
    print(f"child sigterm mask {child_mask}")
    print(f"parent sigterm mask {parent_mask}")
    signal.signal(signal.SIGTERM, handler(p1, p2, parent_mask, term_child))
    p1.join()
    p2.join()
    if 0 < sleep_time < float("inf"):
        time.sleep(sleep_time)


if __name__ == "__main__":
    parser = ArgumentParser("multi_proc_app")
    parser.add_argument(
        "--mask-sigterm", choices=["all", "parent", "none"], default="none"
    )
    parser.add_argument("--sleep-time", type=float, default=0)
    parser.add_argument("--term-child", default=False, action="store_true")
    args = parser.parse_args()
    print(args)
    main(args.mask_sigterm, args.sleep_time, args.term_child)
