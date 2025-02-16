import argparse
import hashlib
import os
import shutil
import sys
import tarfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


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


def get_app_target_dir(url: str, args: argparse.Namespace) -> Path:
    prog_files = (
        Path(args.appdir)
        if args.appdir
        else Path(os.environ["LOCALAPPDATA"]) / "Programs"
    )
    return prog_files.joinpath(
        args.name if args.name else Path(url.split("/")[-1]).stem
    )


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

    to = Path(os.path.expandvars(args.to)).expanduser().absolute() if args.to else Path().absolute()
    emit("Trying to extract at", apps_target_dir)
    is_url = url.startswith("http")
    zip_path = cached_download(url) if is_url else Path(url)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # ensure zip file has top level directory
        zip_ref.extractall(apps_target_dir)

    found = create_shims_in_tree(apps_target_dir, to, args.shim)
    if not found:
        emit("No exe found in the zip file. Did not create shims")


def cached_download(url: str) -> Path:
    url_hash = hashlib.sha256(url.encode()).hexdigest()
    cache_dir = Path(os.environ["LOCALAPPDATA"]) / "Temp/shimpan_cache"
    cache_dir.mkdir(exist_ok=True)
    file_name = url.split("/")[-1]
    cache_file = cache_dir / f"{url_hash}_{file_name}"

    if not cache_file.exists():
        try:
            urlretrieve(url, cache_file)
        except Exception as e:
            emit(f"Error downloading {url}: {e}")
            cache_file.unlink(missing_ok=True)
            raise

    return cache_file


def download_and_extract(url: str, to: Path) -> None:
    target = cached_download(url)
    if target.suffix == ".zip":
        with zipfile.ZipFile(target, "r") as zip_ref:
            zip_ref.extractall(to)
    elif str(target).endswith(".tar.gz"):
        with tarfile.open(target, "r:gz") as tar:
            tar.extractall(to)


def run_recipe(recipefile: Path, name: str, args: argparse.Namespace) -> None:
    root = recipefile.parent
    d = tomllib.load(recipefile.open("rb"))
    config = d.pop("config", {})

    def relative_to_root(p: str | None) -> Path | None:
        if not p:
            return None
        pth = Path(os.path.expandvars(p)).expanduser()
        return root / pth if not pth.is_absolute() else pth

    for k, v in d.items():
        if k != name and name not in v.get("tags", []):
            continue
        print(f"Running recipe {v}")
        url = v["url"]
        save_as = v.get("saveAs", None)
        if save_as:
            emit(f"Save {url} as {save_as}")
            target = cached_download(url)
            shutil.copy(target, root / save_as)

        unzip_to = relative_to_root(v.get("unzipTo"))
        if unzip_to:
            emit(f"Unzip {url} to {unzip_to}")
            download_and_extract(url, unzip_to)

        create_shims = v.get("shims", False)
        if create_shims:
            shims_to = relative_to_root(v.get("shimDir") or config.get("shimDir"))
            if not shims_to:
                emit(
                    "Error: shims requested without shimDir. Specify it in [config] section or item"
                )
                return
            if not unzip_to:
                emit("Error: shims requested without unzipTo.")
                return

            shims_to.mkdir(exist_ok=True, parents=True)
            emit(f"Create shims for {unzip_to} in {shims_to}")
            create_shims_in_tree(unzip_to, shims_to, v.get("shimType", args.shim))


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

    recipe = subparsers.add_parser(
        "recipe", help="Execute instructions from recipe (toml) file"
    )

    recipe.add_argument("recipefile", type=str, help="Path to the recipe file")
    recipe.add_argument(
        "name", type=str, help="The name or tag within the recipe file to run"
    )
    add_shared_args(recipe)

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
    elif args.command == "recipe":
        run_recipe(Path(args.recipefile), args.name, args)


if __name__ == "__main__":
    main(sys.argv)
