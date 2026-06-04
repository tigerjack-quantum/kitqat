# kitqat
kitqat is a toolkit of utilities and algorithms built on top of the QAT module
for quantum computing research and development. The code can be run on the
open-source [myQLM simulator](https://github.com/myQLM). The usage with the
custom [Qaptiva
appliance](https://atos.net/en/solutions/quantum-learning-machine) is mostly
untested.

# Usage #
## Installation
If you would like to use the code, a possible way is to install it through git
is by using

```
pip install git+ssh://git@github.com/tigerjack/kitqat.git
```

You can additionally install
[myQLM](https://myqlm.github.io/myqlm_specific/install.html) with

```
pip install 'kitqat[myqlm] @ git+ssh://git@github.com/tigerjack/kitqat.git'
```

The reason to make myqlm an optional dependency is that the `kitqat` library
can also be run on the QLM machines.

If you would like to test the code and you do not have access to a QLM, you can
install the open source
[myQLM](https://myqlm.github.io/myqlm_specific/install.html).

The best way to install the code would be through
[pyenv](https://github.com/pyenv/pyenv) and the
[pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv). Refer to their
guides on how to install them. After both of them are installed, you can run.

```
pyenv install 3.12.9
pyenv virtualenv 3.12.9 myqlm_env
```

where `3.12.9` is the python version used for this code and `myqlm_env` is the
name of the virtual environment (you can change whatever name you like). You can
also try for different python version, but the code has not been tested with
them. You can check the python versions available for myQLM on their
[documentation](https://myqlm.github.io/myqlm_specific/install.html).

Then, you can install myQLM inside the environment by launching

```
pyenv activate myqlm_env
pip install myqlm
pip install nptyping sympy
pip install paramaterized
pip install jupyter
```
Then, you can clone this repository and activate the environment.

```
cd <SOME_DIR>
git clone https://github.com/tigerjack/kitqat.git
cd kitqat
pyenv activate myqlm_env
```

where `<SOME_DIR>` can be whatever directory you want this repository to be
contained in.


## Testing libraries

`galois` is used to double-check 
field operations.
`sympy` is only
used in testing to automatically compute the RREF of a matrix and compare the
results against our implementation. `parameterized` is used in order to have
parameterized testing; this is a legacy feature coming from `unittest`, and all
new code uses `pytest` built-in methods instead. `jupyter` is required to launch
notebooks.

## Structure

  * The actual code is under `kitqat`.
  * `examples` directory contains some experiments that have been made.
  * `test` directory contains all the tests for all the implemented routines.

# Tests
The tests can be run using `pytest` (all tests) or 
`pytest -sv test/qatext/qroutines/walk/test_update_reversible0.py` 
(only a specific test case, replacing module name
with the actual name of the module).

When launching tests, you can provide some optional environment variables

  * `LOG_LEVEL`, with values equal to the names provided by Python logging
utilities. E.g. `LOG_LEVEL=DEBUG python -m unittest test.test_qroutine_rref`.
  * `SLOW_TEST_ON=1` to enable also time consuming tests
  * `REVERSIBLE_ON=1` to enable the reversible simulator for circuits made only
    of reversible gates. Keep it on.
  * `QLM_ON=1` to use the QLM instead of myQLM
  * `SIMULATOR`, to pass the name of a simulator. For myQLM, the `pylinalg` and 
    `clinalg`
    simulators are available, and the latter is the default one. 
    For QLM, there are a variety of available
    simulators depending on the version.

# Contributing

This project uses a two-stage development model: internal development in a private
repository, followed by public release on GitHub.

- **External contributors** can submit pull requests on GitHub. All public contributions
  are licensed under the [Apache License 2.0](LICENSE).
- **Internal contributors** must follow the internal development policy described in
  [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md).

Significant contributions will be acknowledged in
[CONTRIBUTORS](./docs/CONTRIBUTORS.md) or release notes.

# Authors and citations #
Part of the code presented here was used in the results of many of my articles.
Check [my website](https://perriello.faculty.polimi.it/) if you are interested.

# List of utilities implemented / to be implemented #

  * Core infrastructure
    * [x] Reversible simulator
    * [x] ProgramWrapper and QRoutineWrapper objects (`kitqat.qatmgmt`)
    * [x] Helper functions for Gate, Observable, Result and Sample objects (`kitqat.qatmgmt`)

  * State preparation
    * [x] Dicke state
    * [ ] Quantum circuits for general multi-qubit gates: [link](https://arxiv.org/pdf/quant-ph/0404089.pdf)
    * [ ] Quantum-state preparation with universal gate decompositions: [link](https://arxiv.org/pdf/1003.5760.pdf)
    * [ ] Quantum Networks for generating arbitrary quantum states: [link](https://arxiv.org/pdf/quant-ph/0407102.pdf)

  * Quantum walk (`kitqat.qroutines.walk`)
    * [x] Update operator, version 0 [link](https://doi.org/10.1109/TC.2025.3625044) [link](https://doi.org/10.1145/3801487.3801826)
    * [x] Update operator, version 1 [TODO link]()

  * Encoding classical data
    * [x] Classical bitstring encoding
    * [x] Binary Index eXtractor (BIX) [link](https://doi.org/10.1145/3649329.3657337)
    * [x] Vertex Binary Encoding (VBE) [TODO link]()
    * [ ] Basis encoding [link](https://arxiv.org/pdf/quant-ph/9807053.pdf)
    * [ ] Amplitude encoding [link](https://arxiv.org/pdf/1703.10793.pdf)
    * [ ] Angle encoding [link](https://arxiv.org/pdf/1711.11240.pdf)
    * [ ] Higher order embedding [link](https://arxiv.org/pdf/1804.11326.pdf)
    * [ ] Variational/trained embedding [link](https://arxiv.org/pdf/2001.03622.pdf)

  * Integer arithmetic (`kitqat.qroutines.arith`)
    * [x] Cuccaro arithmetic
      * [x] Adder/subtractor
      * [x] Different length registers
      * [x] Comparator
      * [x] No overflow
      * [x] Little/big endian
      * [ ] No carry in
    * [x] TKK arithmetic
      * [x] Adder
      * [ ] Subtractor
      * [ ] Comparator
      * [ ] No carry in
      * [ ] Different length registers
      * [ ] No overflow
      * [ ] Little/big endian
    * [x] Perriello arithmetic
      * [x] 2-bit adder
      * [x] 2-bit comparator

  * Arithmetic over finite fields (`kitqat.qroutines.algebraic`)
    * [x] GF(2ⁿ)
      * [x] Basic arithmetic (multiplication, schoolbook reduction)
      * [x] Adders (Cuccaro-style, TKK-style, QFT-based)
      * [x] Toom-Cook / Karatsuba multiplication
      * [x] Field inversion (Fermat's little theorem)
    * [x] GF(p)
      * [x] Barrett reduction
      * [x] Kaliski inversion
    * [x] Montgomery multiplication (`kitqat.qroutines.montgomery`)

  * Linear algebra (`kitqat.qroutines.linalg`)
    * [x] Gauss-Jordan elimination [link](https://doi.org/10.1145/3607256)
    * [x] Column permutations [link](https://doi.org/10.1109/QCE52317.2021.00056)

  * Cryptography (`kitqat.qroutines.crypto`)
    * [x] DES Sbox (Kwan) [link](https://doi.org/10.1109/QCE60285.2024.00011)

  * Data structures (`kitqat.qroutines.datastructure`)
    * [x] Sorted array insertion/deletion [link](https://dam-oclc.bac-lac.gc.ca/download?is_thesis=1&oclc_number=1122760241&id=40c75e28-fea0-4cd1-be3a-94709029fcdc&fileName=Jaques_Samuel.pdf)
    * [x] Sorted array low-width insertion/deletion [TODO link]()
    * [x] Array existence check [link](https://dam-oclc.bac-lac.gc.ca/download?is_thesis=1&oclc_number=1122760241&id=40c75e28-fea0-4cd1-be3a-94709029fcdc&fileName=Jaques_Samuel.pdf)

  * Combinatorial circuits (`kitqat.qroutines`)
    * [x] Sorting network (`sorting`)
    * [x] Benes network (`hamming_weight_generate`)

  * Hamming weight (`kitqat.qroutines`)
    * [x] Compute Hamming weight of a qubit subset (`hamming_weight_compute`)
    * [x] Generate Dicke states / check Hamming weight (`hamming_weight_generate`)

  * Quantum register management (`kitqat.qroutines.qregs_mgmt`)
    * [x] Register reversal
    * [x] Register rotation (left/right)
    * [x] Data initialisation (bitstring, bitarray, int)
    * [x] Matrix initialisation with row/column swap

  * Classical benchmarks (`bin/`, `test/classical_ref/`)
    * [x] Reference implementations for GF(2ⁿ) and GF(p) arithmetic
    * [x] Benchmark metrics (gate count, Toffoli count, depth)
    * [x] Benchmark inversions
