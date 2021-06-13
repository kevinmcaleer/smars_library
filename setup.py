import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="smars_library",
    version="1.0.8",
    description="SMARS Robot Python Library",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/kevinmcaleer/smars_library",
    author="Kevin McAleer",
    author_email="kevinmcaleer@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=["smars_library"],
    include_package_data=False,
    install_requires=["adafruit-pca9685","pathlib"],
    )
