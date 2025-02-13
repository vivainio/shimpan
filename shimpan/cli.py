import argparse
from pathlib import Path
import shutil
import sys
import os
from urllib.request import urlretrieve

import tempfile
import zipfile


def create_shims(exe: Path, to: Path, shim_type: str):
    shim = to / f"{exe.stem}.exe"

    shim_source = Path(__file__).parent / f"shim_{shim_type}.exe"

    shutil.copy(shim_source, shim)
    print("Shims (.exe, .shim) created at", shim)

    shim.with_suffix(".shim").write_text(f"path = {exe.absolute()}\n")


def direct_shim_create(args: argparse.Namespace):
    exe = Path(args.exe)
    if not exe.exists():
        print(f"Error: Target executable '{exe}' does not exist")
        return

    to = Path(args.to) if args.to else Path().absolute()

    create_shims(exe, to, args.shim)


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
            create_shims(exe, to, args.shim)


def main() -> None:
    version = Path(__file__).parent.joinpath("version.txt").read_text().strip()
    parser = argparse.ArgumentParser(
        description=f"Shimpan: Create shims for exes that are in path. Version: {version}"
    )

    parser.add_argument(
        "--shim",
        choices=["alt", "scoop"],
        default="scoop",
        help="Shim type. Default is 'scoop'",
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
