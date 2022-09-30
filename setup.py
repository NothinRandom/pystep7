from setuptools import setup

__version__      = '0.2.1'
__license__      = 'MIT'
__author__       = 'Tri Quach'
__author_email__ = 'nothinrandom@gmail.com'
__url__          = 'https://github.com/NothinRandom/pystep7'

setup(
    name="pystep7",
    version=__version__,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    description="A Python Step7 library for communicating with Siemens PLCs.",
    license="MIT",
    packages=["pystep7"],
    python_requires=">=3.7.0",
)
