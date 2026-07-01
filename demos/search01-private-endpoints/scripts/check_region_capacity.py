"""Probe candidate Azure regions for available capacity to run this demo.

Two checks per region:
  1. VM SKU restrictions via `az vm list-skus`. Fast, deterministic for
     subscription-level locks. Empty `restrictions` => deployable for your sub.
  2. Azure AI Search 'standard' SKU capacity via an actual create-then-delete
     against a tiny probe service. Azure does not expose a Search capacity
     query API, so this is the only reliable signal. Cost per probe is a
     fraction of a cent (service lives for ~60s).

The script creates a temporary probe resource group per region tested. Each
probe RG is deleted (async, --no-wait) at the end. Any unexpected interruption
leaves probe RGs behind — list/delete them manually:

    az group list --query "[?starts_with(name, 'rg-search01-probe-')]" -o table
    az group delete --name <name> --yes --no-wait

Usage:
    python scripts/check_region_capacity.py
    python scripts/check_region_capacity.py --vm-size Standard_B1s
    python scripts/check_region_capacity.py --regions westeurope,northeurope
    python scripts/check_region_capacity.py --skip-search
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Optional, Tuple

# Use the same Azure CLI resolver the notebooks use so this works on Windows
# (where `az` is actually `az.cmd` and stdlib subprocess won't find it on PATH).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.notebook_helpers import resolve_az_cli  # noqa: E402

AZ_CMD = resolve_az_cli()
if not AZ_CMD:
    sys.exit("Azure CLI not found. Install it and re-run.")

DEFAULT_REGIONS = [
    "westeurope",
    "northeurope",
    "swedencentral",
    "francecentral",
    "uksouth",
    "germanywestcentral",
    "eastus",
    "eastus2",
    "centralus",
    "westus2",
    "westus3",
]

RUN_ID = uuid.uuid4().hex[:6]


def az(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([AZ_CMD, *args], capture_output=True, text=True)


def check_vm_sku(region: str, size: str) -> Tuple[bool, str]:
    res = az("vm", "list-skus", "--location", region, "--size", size,
             "--resource-type", "virtualMachines", "-o", "json")
    if res.returncode != 0:
        return False, f"list-skus error: {res.stderr.strip()[:80]}"
    try:
        skus = json.loads(res.stdout or "[]")
    except json.JSONDecodeError:
        return False, "unparseable list-skus"
    if not skus:
        return False, "not offered in region"
    for sku in skus:
        for r in sku.get("restrictions") or []:
            if r.get("type") == "Location":
                return False, f"restricted ({r.get('reasonCode', 'unknown')})"
    return True, "no restrictions"


def ensure_probe_rg(region: str) -> str:
    name = f"rg-search01-probe-{RUN_ID}-{region}"
    az("group", "create", "--name", name, "--location", region, "-o", "none")
    return name


def delete_probe_rg(rg: str) -> None:
    az("group", "delete", "--name", rg, "--yes", "--no-wait", "-o", "none")


def check_search_capacity(region: str, rg: str) -> Tuple[bool, str]:
    name = f"srch-probe-{RUN_ID}-{uuid.uuid4().hex[:6]}"[:60]
    create = az(
        "search", "service", "create",
        "--name", name,
        "--resource-group", rg,
        "--location", region,
        "--sku", "standard",
        "--partition-count", "1",
        "--replica-count", "1",
        "-o", "none",
    )
    if create.returncode != 0:
        msg = (create.stderr or create.stdout).strip()
        # Surface the most useful chunk of the error
        for keyword in ("ResourcesForSkuUnavailable", "InsufficientResources",
                        "QuotaExceeded", "SubscriptionNotRegistered"):
            if keyword in msg:
                return False, keyword
        return False, msg.split("\n", 1)[0][:80] or "create failed"
    # Cleanup on success
    az("search", "service", "delete", "--name", name, "--resource-group", rg, "--yes", "-o", "none")
    return True, "available"


def fmt_result(ok: Optional[bool], msg: str) -> str:
    if ok is None:
        return f"-- {msg}"
    return f"{'OK' if ok else 'XX'} {msg}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vm-size", default="Standard_B1s",
                        help="VM SKU to check (default: Standard_B1s, matches infra/main.bicep).")
    parser.add_argument("--regions", default=",".join(DEFAULT_REGIONS),
                        help="Comma-separated regions to probe.")
    parser.add_argument("--skip-search", action="store_true",
                        help="Skip AI Search probe (VM check only — instant).")
    args = parser.parse_args()

    regions = [r.strip() for r in args.regions.split(",") if r.strip()]
    print(f"Probing {len(regions)} region(s). VM size: {args.vm_size}. "
          f"Search probe: {'no' if args.skip_search else 'yes'}\n")
    header = f"{'Region':<22} {'VM SKU':<32} {'Search Standard':<32}"
    print(header)
    print("-" * len(header))

    probe_rgs: list[str] = []
    first_green: Optional[str] = None
    try:
        for region in regions:
            vm_ok, vm_msg = check_vm_sku(region, args.vm_size)
            search_ok: Optional[bool]
            if args.skip_search:
                search_ok, search_msg = None, "skipped"
            elif not vm_ok:
                search_ok, search_msg = None, "skipped (VM failed)"
            else:
                rg = ensure_probe_rg(region)
                probe_rgs.append(rg)
                search_ok, search_msg = check_search_capacity(region, rg)
            print(f"{region:<22} {fmt_result(vm_ok, vm_msg):<32} "
                  f"{fmt_result(search_ok, search_msg):<32}")
            if vm_ok and search_ok and first_green is None:
                first_green = region
    finally:
        if probe_rgs:
            print(f"\nDeleting {len(probe_rgs)} probe resource group(s) (async)...")
            for rg in probe_rgs:
                delete_probe_rg(rg)

    print()
    if first_green:
        print(f"First region green for both checks: {first_green}")
        print(f"Set LOCATION = \"{first_green}\" in 01_deploy_infra.ipynb and re-run.")
        return 0
    print("No region passed both checks. Try a wider --regions list.")
    return 2


if __name__ == "__main__":
    sys.exit(main())
