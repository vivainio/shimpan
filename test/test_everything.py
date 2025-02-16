import shutil
import tempfile
from pathlib import Path
from urllib.request import urlretrieve
import zipfile
from shimpan import cli

ROOT = Path(__file__).parent


def _create_mini_zip(pth: Path):
    with zipfile.ZipFile(pth, "w") as z:
        z.writestr("test.exe", "dummy content")


def test_download() -> None:
    # get
    with (
        tempfile.TemporaryDirectory() as tmpdirname,
        tempfile.TemporaryDirectory() as app_progs,
    ):
        # from web
        cli.main(
            [
                "testapp",
                "--appdir",
                app_progs,
                "get",
                "--to",
                tmpdirname,
                "https://github.com/vivainio/heymars/releases/download/v1.2.1/heymars-1.2.1.zip",
            ]
        )
        listing = list(Path(tmpdirname).iterdir())
        assert len(listing) == 2

        for p in listing:
            p.unlink()

        # from local zip

        _create_mini_zip(Path(tmpdirname) / "test.zip")
        cli.main(
            [
                "testapp",
                "--appdir",
                app_progs,
                "get",
                "--to",
                tmpdirname,
                str(Path(tmpdirname) / "test.zip"),
            ]
        )
        listing = list(Path(tmpdirname).iterdir())
        print(listing)

        # zip, shim, exe

        assert len(listing) == 3
    # create

    with (
        tempfile.TemporaryDirectory() as tmpdirname,
        tempfile.TemporaryDirectory() as app_progs,
        tempfile.TemporaryDirectory() as exedir,
    ):
        Path(exedir).joinpath("dumbapp.exe").write_text("")
        cli.main(
            ["testapp", "--appdir", app_progs, "create", "--to", tmpdirname, exedir]
        )
        listing = list(Path(tmpdirname).iterdir())
        assert len(listing) == 2


def test_recipe():
    with tempfile.TemporaryDirectory() as tmpdirname:
        tmp = Path(tmpdirname)
        shutil.copy(ROOT / "recipe.toml", tmpdirname)
        cli.main(
            [
                "testapp",
                "recipe",
                tmpdirname + "/recipe.toml",
                "tagtest",
                "--to",
                tmpdirname,
            ]
        )
        listing = {p.name for p in tmp.iterdir()}
        print(listing)
        assert listing == {"recipe.toml", "ziptarget", "testzip.zip", "shimdir"}
        unzipped_files = {p.name for p in (tmp / "ziptarget").iterdir()}
        assert unzipped_files == {"Heymars"}
        shim_files = {p.name for p in (tmp / "shimdir").iterdir()}
        assert shim_files == {"Heymars.exe", "Heymars.shim"}
