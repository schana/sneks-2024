import pathlib
import shutil
import subprocess

import requests

import sneks


def main():
    shutil.rmtree("modules", ignore_errors=True)
    get_template_readme()
    get_template()
    build_docs()


def build_docs():
    sneks_path = str(pathlib.Path(sneks.__file__).resolve().parent)
    subprocess.run(
        [
            "sphinx-apidoc",
            "--separate",
            "--module-first",
            "--force",
            "--no-toc",
            "-o",
            "modules",
            sneks_path,
            f"{sneks_path}/submission",
            f"{sneks_path}/infrastructure",
            f"{sneks_path}/application/backend",
            f"{sneks_path}/application/engine/engine",
            f"{sneks_path}/application/engine/gui",
            f"{sneks_path}/application/engine/validator",
            f"{sneks_path}/application/engine/config",
            f"{sneks_path}/application/engine/template",
        ]
    )
    subprocess.run(["sphinx-build", "-b", "html", ".", "build/docs"])


def get_template_readme():
    prefix = pathlib.Path("modules")
    prefix.mkdir(exist_ok=True)
    response = requests.get(
        "https://github.com/schana/sneks-submission/raw/main/README.md"
    )
    with open(prefix / "README.md", "wb") as f:
        for chunk in response.iter_content():
            f.write(chunk)


def get_template():
    prefix = pathlib.Path("build/template")
    shutil.rmtree(prefix, ignore_errors=True)
    prefix.mkdir(exist_ok=True)
    response = requests.get(
        "https://github.com/schana/sneks-submission/archive/refs/heads/main.zip"
    )
    with open(prefix / "template.zip", "wb") as f:
        for chunk in response.iter_content():
            f.write(chunk)

    response = requests.get(
        "https://github.com/schana/sneks-submission/raw/main/README.md"
    )
    with open(pathlib.Path("modules/README.md"), "wb") as f:
        for chunk in response.iter_content():
            f.write(chunk)


if __name__ == "__main__":
    main()
