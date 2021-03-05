# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


install_requirements = [
    "qat-comm",
    "qat-core",
    "qat-lang",
    "typing",
    "numpy>=1.15",
]

tests_requirements = [
        "parameterized",
        "sympy",
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
    install_requires=install_requirements,
    tests_requires=tests_requirements,
    test_suite="unittest",
    include_package_data=True,
    python_requires=">=3.8,<3.9",
)
