import argparse
from pathlib import Path
import shutil
import sys
import os
from urllib.request import urlretrieve

import tempfile
import zipfile

MASTER_SHIM_EXE = Path(__file__).parent / "shim.exe"


def create_shims(exe: Path, to: Path):
    shim = to / f"{exe.stem}.exe"

    shutil.copy(MASTER_SHIM_EXE, shim)
    print("Shims (.exe, .shim) created at ", shim)

    shim.with_suffix(".shim").write_text(f"path = {exe.absolute()}\n")


def direct_shim_create(args: argparse.Namespace):
    exe = Path(args.exe)
    if not exe.exists():
        print(f"{exe} does not exist")
        return

    if args.to:
        to = Path(args.to)
    else:
        to = Path().absolute()

    create_shims(exe, to)


def download_and_shim_application(args: argparse.Namespace):
    url = args.url
    # download and unzip

    prog_files = Path(os.environ["LOCALAPPDATA"]) / "Programs"
    apps_target_dir = prog_files.joinpath(
        args.name if args.name else Path(url.split("/")[-1]).stem
    )

    if args.force:
        shutil.rmtree(apps_target_dir, ignore_errors=True)

    if apps_target_dir.exists():
        print(f"{apps_target_dir} already exists. Delete it first")
        return

    to = Path(args.to).expanduser().absolute() if args.to else Path().absolute()
    print("Trying to extract at ", apps_target_dir)

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        zip_path = tmpdir / "temp.zip"
        urlretrieve(url, zip_path)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # ensure zip file has top level directory
            zip_ref.extractall(apps_target_dir)

        # find the exe
        exe = None

        exes = list(apps_target_dir.glob("**/*.exe"))
        if not exes:
            print("No exe found in the zip file. Not creating shims")
            return

        for exe in exes:
            create_shims(exe, to)


def main():
    parser = argparse.ArgumentParser(
        description="Shimpan: Create shims for exes that are in path"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser(
        "create", help="Create a shim for an executable. The lowest level action"
    )
    create.add_argument("exe", type=str, help="Target path to the application")
    parser.add_argument(
        "--to",
        type=str,
        help="The directory where the shim files (.exe, .shim) will be created",
    )

    get = subparsers.add_parser(
        "get", help="Download zip file, install it as an application"
    )
    get.add_argument("url", type=str, help="URL to the zip file")
    get.add_argument(
        "--name",
        type=str,
        help="Name of the application (override autodetect from url)",
    )
    get.add_argument(
        "--force", action="store_true", help="Delete the target directory if it exists"
    )
    get.add_argument(
        "--to",
        type=str,
        help="The directory where the shim files (.exe, .shim) will be created",
    )

    args = parser.parse_args()
    if args.command == "create":
        direct_shim_create(args)
    elif args.command == "get":
        download_and_shim_application(args)
