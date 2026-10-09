"""Batch VM verification for Hack@CHES 2026 VULNs.

Runs POC exploits/builds on the official hackches VM via SSH,
captures evidence logs, and generates oracle certification.

Usage:
  python scripts/vm_verify.py --vulns VULN-001,VULN-002,VULN-003   # small batch
  python scripts/vm_verify.py --only-success                        # all 72 poc-success
  python scripts/vm_verify.py --vuln VULN-001 --dry-run             # debug one
"""
import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# --- config ---
SSH_HOST = "participant@localhost"
SSH_PORT = 2223
VM_OT = "/home/participant/opentitan"
VM_VERILATOR = "/home/participant/verilator"
VM_WORK_ROOT = "/tmp/vuln_verify"
VM_HARNESS = "/home/participant/hctool"

LOCAL_OT = "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/opentitan_blind"
LOCAL_VERILATOR = (
    "/data_hdd/tzh24/zgc4/projects/tools/logos/"
    "logos-workspace/contexts/targets/opentitan-ches2026/"
    "runtime-samples/verilator-4.210/v4.210"
)

POC_DIR = Path("campaigns/ches2026-prep/workdir/poc")
OUTPUT_DIR = Path("campaigns/ches2026-prep/workdir/vm_evidence")


def ssh(cmd: str, timeout: int = 300) -> subprocess.CompletedProcess:
    """Run command on VM via SSH. Returns CompletedProcess with rc, stdout, stderr."""
    return subprocess.run(
        ["ssh", "-p", str(SSH_PORT), "-o", "StrictHostKeyChecking=no",
         "-o", "ConnectTimeout=10", SSH_HOST, cmd],
        capture_output=True, text=True, timeout=timeout,
    )


def rsync_to_vm(local: Path, remote: str) -> bool:
    """Rsync local dir/file to VM."""
    r = subprocess.run(
        ["rsync", "-az", "--delete", "-e",
         f"ssh -p {SSH_PORT} -o StrictHostKeyChecking=no",
         str(local) + "/", f"{SSH_HOST}:{remote}/"],
        capture_output=True, text=True, timeout=120,
    )
    if r.returncode != 0:
        print(f"    rsync FAIL: {r.stderr[:200]}", file=sys.stderr)
    return r.returncode == 0


def rsync_from_vm(remote: str, local: Path) -> bool:
    """Rsync remote dir from VM to local."""
    local.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["rsync", "-az", "-e",
         f"ssh -p {SSH_PORT} -o StrictHostKeyChecking=no",
         f"{SSH_HOST}:{remote}/", str(local) + "/"],
        capture_output=True, text=True, timeout=120,
    )
    return r.returncode == 0


def get_poc_success_vulns(poc_dir: Path) -> list[str]:
    """Return sorted list of VULN-NNN dirs that have poc-success in RESULT.md."""
    vulns = []
    for d in sorted(poc_dir.glob("VULN-*")):
        if not d.is_dir():
            continue
        result = d / "RESULT.md"
        if result.exists() and "poc-success" in result.read_text(encoding="utf-8", errors="replace"):
            vulns.append(d.name)
    return vulns


def adapt_build_script(content: str) -> str:
    """Replace local paths with VM paths in build.sh content."""
    out = content
    out = out.replace(LOCAL_VERILATOR, VM_VERILATOR)
    out = out.replace(LOCAL_OT, VM_OT)
    out = out.replace(LOCAL_OT.replace("_blind", ""), VM_OT)
    for old in [
        "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-windflow",
        "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/logos-lite",
        "/data_hdd/tzh24/zgc4/ctf/hack_ches2026/hctool",
    ]:
        out = out.replace(old, VM_HARNESS)
    return out


def find_build_script(vuln_dir: Path) -> Path | None:
    """Find the primary build script for a VULN."""
    if (vuln_dir / "build.sh").exists():
        return vuln_dir / "build.sh"
    candidates = sorted(vuln_dir.glob("build_*.sh"))
    return candidates[0] if candidates else None


def extract_oracle_info(result_md: str) -> dict:
    """Extract oracle certification info from RESULT.md."""
    info = {"twin_diff": [], "oracle_quotes": [], "fidelity": None, "verdict": None}

    # Verdict
    m = re.search(r"Verdict:\s*\*\*(\S+)\*\*", result_md)
    if m:
        info["verdict"] = m.group(1)

    # Fidelity level
    m = re.search(r"—\s*(L[1-4])", result_md)
    if m:
        info["fidelity"] = m.group(1)

    # Twin repair diff lines
    in_diff = False
    for line in result_md.split("\n"):
        if "Twin Repair" in line or "twin.*diff" in line.lower():
            in_diff = True
            continue
        if in_diff and line.strip().startswith(("-", "+")):
            info["twin_diff"].append(line.strip())
        elif in_diff and not line.strip():
            in_diff = False

    # Oracle quotes (SVA, hjson, spec references)
    for pattern in [
        r"预言机依据[^：]*：(.+?)(?:\n|$)",
        r"oracle.*?:\s*(.+?)(?:\n|$)",
        r"SVA\s+\w+Assert",
        r"SEC_CM\s+\w+",
    ]:
        for m in re.finditer(pattern, result_md, re.IGNORECASE):
            quote = m.group(0).strip()
            if quote and quote not in info["oracle_quotes"]:
                info["oracle_quotes"].append(quote)

    return info


def generate_oracle_cert(vuln_id: str, result_md: str, vm_exit: int, evidence: str) -> str:
    """Generate oracle_cert.md content."""
    info = extract_oracle_info(result_md)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# Oracle Certification — {vuln_id}",
        "",
        f"Generated: {now}",
        f"VM verification exit code: {vm_exit} (1 = confirmed)",
        f"Local verdict: {info.get('verdict', 'unknown')}",
        f"Fidelity: {info.get('fidelity', 'unknown')}",
        f"VM result: {'VM-CONFIRMED' if vm_exit == 1 else 'VM-FAILED'}",
        "",
        "## Twin Repair Diff",
        "",
    ]
    if info["twin_diff"]:
        lines.extend(info["twin_diff"])
    else:
        lines.append("(see RESULT.md for twin diff details)")

    lines.extend([
        "",
        "## Oracle References",
        "",
    ])
    if info["oracle_quotes"]:
        for q in info["oracle_quotes"][:10]:
            lines.append(f"- {q}")
    else:
        lines.append("(see RESULT.md for oracle justification)")

    lines.extend([
        "",
        "## Evidence Log (excerpt)",
        "",
        "```",
    ])
    # Last 40 lines of evidence
    ev_lines = evidence.strip().split("\n")
    lines.extend(ev_lines[-40:])
    lines.extend(["```", ""])

    return "\n".join(lines)


def _is_l4_static(result_md: str) -> bool:
    """Check if VULN is L4 static analysis (exit=0 is normal, not failure)."""
    return bool(re.search(r"L4\s+fidelity|L4\s*\(static", result_md))


def _output_confirmed(evidence: str) -> bool:
    """Check if evidence log contains CONFIRMED markers (for L4 exit=0 cases)."""
    return bool(re.search(r"CONFIRMED|vuln_deviation:\s*YES|test_confirmed:\s*YES", evidence))


def _run_on_vm(vm_vuln_dir: str, method: str, timeout: int = 600) -> tuple[int, list[str]]:
    """Execute exploit.py or build_vm.sh on VM. Returns (exit_code, evidence_lines)."""
    if method == "exploit.py":
        # Try with both args, then without --verilator, then without --repo
        for cmd in [
            f"cd {vm_vuln_dir} && python3 exploit.py --repo {VM_OT} --verilator {VM_VERILATOR}/bin/verilator 2>&1",
            f"cd {vm_vuln_dir} && python3 exploit.py --repo {VM_OT} 2>&1",
            f"cd {vm_vuln_dir} && python3 exploit.py 2>&1",
        ]:
            r = ssh(cmd, timeout=timeout)
            # If arg parsing error, try next variant
            if "unrecognized arguments" not in r.stdout:
                break
        lines = r.stdout.split("\n")
        if r.stderr and "unrecognized arguments" not in r.stdout:
            lines.append("--- STDERR ---")
            lines.extend(r.stderr.split("\n"))
        return r.returncode, lines
    else:
        r = ssh(f"cd {vm_vuln_dir} && bash build_vm.sh 2>&1", timeout=timeout)
        lines = r.stdout.split("\n")
        if r.stderr:
            lines.append("--- STDERR ---")
            lines.extend(r.stderr.split("\n"))
        return r.returncode, lines


def verify_one_vuln(vuln_id: str, poc_dir: Path, output_dir: Path,
                    dry_run: bool = False, method_override: str | None = None,
                    timeout: int = 600) -> dict:
    """Verify a single VULN on the VM. Returns result dict."""
    vuln_dir = poc_dir / vuln_id
    out_dir = output_dir / vuln_id
    out_dir.mkdir(parents=True, exist_ok=True)

    result = {
        "vuln_id": vuln_id,
        "status": "pending",
        "vm_exit": None,
        "method": None,
        "started": datetime.now(timezone.utc).isoformat(),
    }

    print(f"[{vuln_id}] Starting...")

    result_md_path = vuln_dir / "RESULT.md"
    result_md = result_md_path.read_text(encoding="utf-8", errors="replace") if result_md_path.exists() else ""
    is_l4 = _is_l4_static(result_md)

    has_exploit = (vuln_dir / "exploit.py").exists()
    build_sh = find_build_script(vuln_dir)

    if dry_run:
        method = method_override or ("exploit.py" if has_exploit else ("build.sh" if build_sh else "none"))
        print(f"[{vuln_id}] DRY RUN: method={method}, has_exploit={has_exploit}, build={build_sh}, L4={is_l4}")
        result["status"] = "dry-run"
        result["method"] = method
        return result

    # Step 1: rsync POC to VM
    vm_vuln_dir = f"{VM_WORK_ROOT}/{vuln_id}"
    print(f"[{vuln_id}] Syncing to VM...")
    ssh(f"mkdir -p {VM_WORK_ROOT}", timeout=10)
    if not rsync_to_vm(vuln_dir, vm_vuln_dir):
        result["status"] = "rsync-fail"
        print(f"[{vuln_id}] rsync FAILED")
        return result

    # Upload adapted build script (always, for fallback)
    if build_sh:
        build_content = build_sh.read_text(encoding="utf-8")
        vm_build = adapt_build_script(build_content)
        import tempfile
        with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
            f.write(vm_build)
            tmp_sh = Path(f.name)
        try:
            subprocess.run(
                ["scp", "-P", str(SSH_PORT), "-o", "StrictHostKeyChecking=no",
                 str(tmp_sh), f"{SSH_HOST}:{vm_vuln_dir}/build_vm.sh"],
                capture_output=True, timeout=30,
            )
        finally:
            tmp_sh.unlink()

    # Step 2: Execute on VM
    vm_exit = -1
    evidence_lines = []

    # Determine primary method
    primary = method_override or ("exploit.py" if has_exploit else "build.sh")
    fallback = "build.sh" if primary == "exploit.py" and build_sh else None

    for attempt_method in [primary, fallback]:
        if attempt_method is None:
            continue
        if attempt_method == "build.sh" and not build_sh:
            continue
        result["method"] = attempt_method
        print(f"[{vuln_id}] Running {attempt_method} on VM (timeout={timeout}s)...")
        try:
            vm_exit, evidence_lines = _run_on_vm(vm_vuln_dir, attempt_method, timeout)
        except subprocess.TimeoutExpired:
            print(f"[{vuln_id}] TIMEOUT ({timeout}s)")
            result["status"] = "timeout"
            evidence_lines = [f"TIMEOUT after {timeout}s"]
            vm_exit = -1
            continue
        except Exception as e:
            print(f"[{vuln_id}] EXCEPTION: {e}")
            result["status"] = "exception"
            evidence_lines = [f"EXCEPTION: {e}"]
            vm_exit = -1
            continue

        # If exploit.py failed with exit!=1 and we have a build fallback, try it
        if attempt_method == "exploit.py" and vm_exit not in (0, 1) and fallback:
            print(f"[{vuln_id}] exploit.py exit={vm_exit}, trying build.sh fallback...")
            continue
        break

    if not evidence_lines:
        result["status"] = "no-method"
        return result

    result["vm_exit"] = vm_exit
    evidence = "\n".join(evidence_lines)

    # Step 3: Save evidence log
    (out_dir / "evidence.log").write_text(evidence, encoding="utf-8")

    # Step 4: Pull back obj/ if exists
    rsync_from_vm(f"{vm_vuln_dir}/obj", out_dir / "obj")

    # Step 5: Determine status — L4 static uses exit=0, dynamic uses exit=1
    confirmed = (vm_exit == 1) or (is_l4 and vm_exit == 0 and _output_confirmed(evidence))
    if confirmed:
        result["status"] = "VM-CONFIRMED"
        cert = generate_oracle_cert(vuln_id, result_md, vm_exit, evidence)
        (out_dir / "oracle_cert.md").write_text(cert, encoding="utf-8")
        print(f"[{vuln_id}] VM-CONFIRMED (exit={vm_exit})")
    else:
        result["status"] = "VM-FAILED"
        cert = generate_oracle_cert(vuln_id, result_md, vm_exit, evidence)
        (out_dir / "oracle_cert.md").write_text(cert, encoding="utf-8")
        print(f"[{vuln_id}] VM-FAILED (exit={vm_exit})")

    if result_md:
        (out_dir / "RESULT_local.md").write_text(result_md, encoding="utf-8")

    result["finished"] = datetime.now(timezone.utc).isoformat()
    return result


def main():
    ap = argparse.ArgumentParser(description="Batch VM verification for CHES VULNs")
    ap.add_argument("--poc-dir", type=Path, default=POC_DIR)
    ap.add_argument("--output", type=Path, default=OUTPUT_DIR)
    ap.add_argument("--vuln", help="Single VULN to verify (e.g. VULN-001)")
    ap.add_argument("--vulns", help="Comma-separated VULN list")
    ap.add_argument("--only-success", action="store_true", help="Verify all poc-success VULNs")
    ap.add_argument("--parallel", type=int, default=1, help="Parallel VM sessions (careful: VM has 8 CPUs)")
    ap.add_argument("--method", choices=["exploit.py", "build.sh"], help="Force verification method")
    ap.add_argument("--timeout", type=int, default=600, help="Per-VULN SSH timeout in seconds")
    ap.add_argument("--retry-failed", action="store_true", help="Retry VM-FAILED VULNs from existing output")
    ap.add_argument("--dry-run", action="store_true", help="Show what would be done")
    args = ap.parse_args()

    # Determine VULN list
    vuln_list = []
    if args.retry_failed:
        # Find VULNs that are VM-FAILED or exception in existing output
        for d in sorted(args.output.glob("VULN-*")):
            rj = d / "result.json"
            if rj.exists():
                rdata = json.loads(rj.read_text())
                if rdata.get("status") in ("VM-FAILED", "exception", "timeout"):
                    vuln_list.append(d.name)
        print(f"Retrying {len(vuln_list)} failed VULNs")
    elif args.vuln:
        vuln_list = [args.vuln]
    elif args.vulns:
        vuln_list = [v.strip() for v in args.vulns.split(",")]
    elif args.only_success:
        vuln_list = get_poc_success_vulns(args.poc_dir)
        print(f"Found {len(vuln_list)} poc-success VULNs")
    else:
        print("Specify --vuln, --vulns, or --only-success")
        sys.exit(1)

    args.output.mkdir(parents=True, exist_ok=True)

    # Verify VM connectivity
    print("Checking VM connectivity...")
    r = ssh("whoami && echo OK")
    if "OK" not in r.stdout:
        print(f"VM SSH failed: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    print(f"VM connected as {r.stdout.strip().split()[0]}")

    # Ensure VM work dir exists
    ssh(f"mkdir -p {VM_WORK_ROOT}")

    # Run verifications
    results = []
    if args.parallel <= 1 or len(vuln_list) <= 1:
        for vid in vuln_list:
            r = verify_one_vuln(vid, args.poc_dir, args.output, args.dry_run,
                                method_override=args.method, timeout=args.timeout)
            results.append(r)
    else:
        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            futures = {pool.submit(verify_one_vuln, vid, args.poc_dir, args.output, args.dry_run,
                                   method_override=args.method, timeout=args.timeout): vid for vid in vuln_list}
            for fut in as_completed(futures):
                try:
                    r = fut.result()
                    results.append(r)
                except Exception as e:
                    vid = futures[fut]
                    print(f"[{vid}] EXCEPTION: {e}")
                    results.append({"vuln_id": vid, "status": "exception", "error": str(e)})

    # Write per-VULN result JSON
    for r in results:
        vid = r.get("vuln_id", "unknown")
        (args.output / vid).mkdir(parents=True, exist_ok=True)
        (args.output / vid / "result.json").write_text(
            json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # Summary
    confirmed = sum(1 for r in results if r.get("status") == "VM-CONFIRMED")
    failed = sum(1 for r in results if r.get("status") == "VM-FAILED")
    other = len(results) - confirmed - failed
    print(f"\n{'='*60}")
    print(f"VM Verification Summary: {len(results)} VULNs")
    print(f"  VM-CONFIRMED: {confirmed}")
    print(f"  VM-FAILED:    {failed}")
    print(f"  Other:        {other}")
    print(f"{'='*60}")

    # Write SUMMARY.md
    summary_lines = [
        f"# VM Verification Summary",
        f"",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"VM: {SSH_HOST}:{SSH_PORT}",
        f"",
        f"| VULN | Status | Exit | Method |",
        f"|------|--------|------|--------|",
    ]
    for r in sorted(results, key=lambda x: x.get("vuln_id", "")):
        vid = r.get("vuln_id", "?")
        status = r.get("status", "?")
        exit_code = r.get("vm_exit", "-")
        method = r.get("method", "-")
        summary_lines.append(f"| {vid} | {status} | {exit_code} | {method} |")

    summary_lines.extend([
        "",
        f"**Total**: {len(results)} | **VM-CONFIRMED**: {confirmed} | **VM-FAILED**: {failed} | **Other**: {other}",
    ])
    (args.output / "SUMMARY.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"Summary written to {args.output / 'SUMMARY.md'}")


if __name__ == "__main__":
    main()
