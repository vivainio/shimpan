from pathlib import Path
import tempfile

from shimpan import cli


def test_download() -> None:
    # get
    with (
        tempfile.TemporaryDirectory() as tmpdirname,
        tempfile.TemporaryDirectory() as app_progs,
    ):
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
    # create

    with (
        tempfile.TemporaryDirectory() as tmpdirname,
        tempfile.TemporaryDirectory() as app_progs,
        tempfile.TemporaryDirectory() as exedir,
    ):
        Path(exedir).joinpath("dumbapp.exe").write_text("")
        cli.main(["testapp", "--appdir", app_progs, "create", "--to", tmpdirname, exedir])
        listing = list(Path(tmpdirname).iterdir())
        assert len(listing) == 2
