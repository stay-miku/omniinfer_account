from setuptools import setup
from setuptools import find_packages


VERSION = "0.0.10"

setup(
    name="omni_infer_api_account",
    version=VERSION,
    description="A secondary distribution account system based on omni infer api.",
    packages=find_packages(),
    author="stay_miku",
    author_email="miku@miku.pics",
    url="",
    install_requires=[
        "omni-infer-api"
    ]
)

