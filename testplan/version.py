import os
import time

__version__ = "24.9.0"

dev_build = int(os.environ.get("DEV_BUILD", "0"))
dev_suffix = f"dev{int(time.time())}" if dev_build else ""

__build_version__ = f"{__version__}{dev_suffix}"
