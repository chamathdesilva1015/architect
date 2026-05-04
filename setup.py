from setuptools import setup, find_packages

setup(
    name="architect-cli",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "typer",
        "jinja2",
        "rich"
    ],
    entry_points={
        "console_scripts": [
            "architect=cli:main",
        ],
    },
)
