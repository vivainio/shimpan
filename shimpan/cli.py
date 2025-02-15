import argparse
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

emit = print


def create_shims(exe: Path, to: Path, shim_type: str) -> None:
    shim = to / f"{exe.stem}.exe"

    shim_source = Path(__file__).parent / f"shim_{shim_type}.exe"

    shutil.copy(shim_source, shim)
    emit("Shims (.exe, .shim) created at", shim, "pointing to", exe)

    shim.with_suffix(".shim").write_text(f"path = {exe.absolute()}\n")


def direct_shim_create(args: argparse.Namespace) -> None:
    exe = Path(args.exe)
    if not exe.exists():
        emit(f"Error: Target executable '{exe}' does not exist")
        return

    to = Path(args.to) if args.to else Path().absolute()

    create_shims(exe, to, args.shim)


def create_shims_in_tree(root: Path, to: Path, shim_type: str) -> bool:
    exes = list(root.glob("**/*.exe"))
    for exe in exes:
        create_shims(exe, to, shim_type)

    return bool(exes)


def download_and_shim_application(args: argparse.Namespace) -> None:
    url = args.url
    # download and unzip

    prog_files = (
        Path(args.appdir)
        if args.appdir
        else Path(os.environ["LOCALAPPDATA"]) / "Programs"
    )
    apps_target_dir = prog_files.joinpath(
        args.name if args.name else Path(url.split("/")[-1]).stem
    )

    if args.force:
        shutil.rmtree(apps_target_dir, ignore_errors=True)

    if apps_target_dir.exists():
        emit(
            f"{apps_target_dir} already exists. Delete it first by passing --force parameter"
        )
        return

    to = Path(args.to).expanduser().absolute() if args.to else Path().absolute()
    emit("Trying to extract at ", apps_target_dir)

    with tempfile.TemporaryDirectory() as tmpdirname:
        tmpdir = Path(tmpdirname)
        zip_path = tmpdir / "shimpan_temp.zip"

        is_url = url.startswith("http")
        if is_url:
            urlretrieve(url, zip_path)  # noqa: S310 audit for http
        else:
            zip_path = Path(url)

        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            # ensure zip file has top level directory
            zip_ref.extractall(apps_target_dir)

        found = create_shims_in_tree(apps_target_dir, to, args.shim)
        if not found:
            emit("No exe found in the zip file. Did not create shims")


def main(argv: list[str]) -> None:
    version = Path(__file__).parent.joinpath("version.txt").read_text().strip()
    parser = argparse.ArgumentParser(
        description=f"Shimpan: Create shims for exes that are in path. Version: {version}"
    )

    def add_shared_args(parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--to",
            type=str,
            help="The directory where the shim files (.exe, .shim) will be created",
        )

    parser.add_argument(
        "--shim",
        choices=["alt", "scoop"],
        default="scoop",
        help="Shim type. Default is 'scoop'",
    )
    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Command to run"
    )
    create = subparsers.add_parser(
        "create", help="Create a shim for an executable. The lowest level action"
    )
    create.add_argument("exe", type=str, help="Target path to the application")
    add_shared_args(create)

    get = subparsers.add_parser(
        "get",
        help="Download zip file, install it as an application. Also works on local zip files.",
    )
    get.add_argument("url", type=str, help="URL or local path to the zip file")
    get.add_argument(
        "--name",
        type=str,
        help="Name of the application (override autodetect from url)",
    )
    get.add_argument(
        "--force", action="store_true", help="Delete the target directory if it exists"
    )
    parser.add_argument(
        "--appdir",
        type=str,
        help="Override app installation directory (default is LOCALAPPDATA/Programs)",
    )

    add_shared_args(get)

    scan = subparsers.add_parser(
        "scan", help="Scan directory for executables and create shims for them"
    )
    scan.add_argument("dir", type=str, help="Directory to scan for exes")
    add_shared_args(scan)

    args = parser.parse_args(argv[1:])
    if args.command == "create":
        direct_shim_create(args)
    elif args.command == "get":
        download_and_shim_application(args)
    elif args.command == "scan":
        root = Path(args.dir)
        if not root.exists():
            emit(f"Error: Directory '{root}' does not exist")
            return

        to = Path(args.to) if args.to else Path().absolute()

        found = create_shims_in_tree(root, to, args.shim)
        if not found:
            emit(f"No exe found in the directory {root}. Did not create shims")


if __name__ == "__main__":
    main(sys.argv)
