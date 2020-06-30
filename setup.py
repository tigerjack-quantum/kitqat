# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


requirements = [
    "qat-comm",
    "qat-core",
    "qat-lang",
    "typing",
    "numpy>=1.15",
]

setup(
    name="qat-utils",
    version="0.2.0",
    description="Some useful extension to Atos Qat language",
    url="https://github.com/tigerjack/qat-utils",
    author="tigerjack",
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Topic :: Scientific/Engineering",
    ],
    keywords="qat atos quantum qlm",
    packages=find_packages(exclude=['test*', 'experiments*']),
    install_requires=requirements,
    include_package_data=True,
    python_requires=">=3.6,<3.7",
)
