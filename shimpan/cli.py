import argparse
from pathlib import Path
import shutil
import sys
import os

MASTER_SHIM_EXE = Path(__file__).parent / "shim.exe"


def direct_shim_create(args: argparse.Namespace):
    exe = Path(args.exe)
    if not exe.exists():
        print(f"{exe} does not exist")
        return

    if args.to:
        to = Path(args.to)
    else:
        to = Path().absolute()

    shim = to / f"{exe.stem}.exe"

    shutil.copy(MASTER_SHIM_EXE, shim)
    print("Shims (.exe, .shim) created at ", shim)

    shim.with_suffix(".shim").write_text(f"path = {exe.absolute()}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Shimpan: Create shims for exes that are in path"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create", help="Create a shim for an exe")
    create.add_argument("exe", type=str, help="Target path to the exe")
    create.add_argument(
        "--to", type=str, help="The directory where the exe shim will be created"
    )

    args = parser.parse_args()
    if args.command == "create":
        direct_shim_create(args)
