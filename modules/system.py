"""
System information module for JARVIS.

Reports CPU usage, memory, and disk info using the standard library only
(psutil is used when available for richer data).
"""

from __future__ import annotations

import logging
import os
import platform

logger = logging.getLogger(__name__)

try:
    import psutil  # type: ignore

    _PSUTIL = True
except ImportError:
    _PSUTIL = False
    logger.debug("psutil not installed – basic system info only.")


def _with_psutil() -> str:
    """Return system info using psutil."""
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    mem_total_gb = mem.total / (1024 ** 3)
    mem_used_gb = mem.used / (1024 ** 3)
    disk_total_gb = disk.total / (1024 ** 3)
    disk_used_gb = disk.used / (1024 ** 3)

    return (
        f"System Information:\n"
        f"  OS: {platform.system()} {platform.release()}\n"
        f"  CPU Usage: {cpu:.1f}%\n"
        f"  Memory: {mem_used_gb:.1f} GB / {mem_total_gb:.1f} GB "
        f"({mem.percent:.1f}% used)\n"
        f"  Disk: {disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB "
        f"({disk.percent:.1f}% used)"
    )


def _without_psutil() -> str:
    """Return basic system info using the standard library."""
    uname = platform.uname()
    return (
        f"System Information:\n"
        f"  OS: {uname.system} {uname.release}\n"
        f"  Machine: {uname.machine}\n"
        f"  Processor: {uname.processor or 'unknown'}\n"
        f"  Python: {platform.python_version()}\n"
        f"  (Install psutil for more detailed information)"
    )


def handle_system_info(_text: str) -> str:
    """
    Handler called by JARVIS for 'system_info' intent.

    Returns:
        Formatted system information string.
    """
    try:
        if _PSUTIL:
            return _with_psutil()
        return _without_psutil()
    except Exception as exc:
        logger.error("System info error: %s", exc)
        return f"Could not retrieve system information: {exc}"
