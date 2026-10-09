"""Adapt local build.sh scripts for the Hack@CHES VM.

Replaces hardcoded local paths with VM paths so POCs can run on the
official appliance (/home/participant/opentitan, /home/participant/verilator).
"""
import re
import sys
from pathlib import Path

LOCAL_OT = "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind"
VM_OT = "/home/participant/opentitan"

LOCAL_VERILATOR = (
    "/data_hdd/tzh24/zgc4/projects/tools/logos/"
    "logos-workspace/contexts/targets/opentitan-ches2026/"
    "runtime-samples/verilator-4.210/v4.210"
)
VM_VERILATOR = "/home/participant/verilator"

LOCAL_HARNESS_OLD = "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow"
LOCAL_HARNESS_CUR = "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-lite"
LOCAL_HARNESS_HCT = "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/hctool"
VM_HARNESS = "/home/participant/hctool"


def adapt_script(src: str) -> str:
    out = src
    # Verilator path (most specific first — longer prefix wins)
    out = out.replace(LOCAL_VERILATOR, VM_VERILATOR)
    # OpenTitan tree (all local variants → VM)
    out = out.replace(LOCAL_OT, VM_OT)
    out = out.replace(LOCAL_OT.replace("_blind", ""), VM_OT)
    # Harness paths
    out = out.replace(LOCAL_HARNESS_OLD, VM_HARNESS)
    out = out.replace(LOCAL_HARNESS_CUR, VM_HARNESS)
    out = out.replace(LOCAL_HARNESS_HCT, VM_HARNESS)
    # Also handle $OT_TREE usage: set default in script header
    if "$OT_TREE" in out and "OT_TREE=" not in out:
        header = f'OT_TREE="${{OT_TREE:-{VM_OT}}}"\nVERILATOR_ROOT="${{VERILATOR_ROOT:-{VM_VERILATOR}}}"\n'
        out = header + out
    return out


def adapt_vuln(vuln_dir: Path, output_dir: Path) -> list[Path]:
    """Adapt all build*.sh in vuln_dir, write to output_dir. Return list of adapted scripts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    adapted = []
    for sh in sorted(vuln_dir.glob("build*.sh")):
        src = sh.read_text(encoding="utf-8", errors="replace")
        vm_src = adapt_script(src)
        dst = output_dir / (sh.stem + "_vm.sh")
        dst.write_text(vm_src, encoding="utf-8")
        adapted.append(dst)
    return adapted


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <poc_dir> <output_dir>")
        sys.exit(1)
    poc_dir = Path(sys.argv[1])
    out_root = Path(sys.argv[2])
    count = 0
    for vd in sorted(poc_dir.glob("VULN-*")):
        if not vd.is_dir():
            continue
        adapted = adapt_vuln(vd, out_root / vd.name)
        if adapted:
            count += 1
            print(f"  {vd.name}: {len(adapted)} script(s) adapted")
    print(f"Total: {count} VULNs adapted")
