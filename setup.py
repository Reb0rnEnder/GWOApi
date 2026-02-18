from setuptools import setup, find_packages
from pathlib import Path

readme = (Path(__file__).parent / "README.md").read_text()

setup(
    name="gwo",
    version="0.1.9",
    packages=find_packages(),
    long_description=readme,
    long_description_content_type="text/markdown",
    author="RebornEnder",
    author_email="contact@dotbend.xyz",
    description="a damn fine wrapper for reverse-enginered gwo api",
    url="https://github.com/Reb0rnEnder/GWOApi",
    license="LICENCE",
    install_requires=[
        "aiohttp>=3.12.15",
        "beautifulsoup4>=4.14.2"
    ]
)