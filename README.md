# qat-utils
A set of useful extensions for Atos qat language used for quantum simulation.

The code here can be run on either the open-source [myQLM
simulator](https://github.com/myQLM) or the [QLM
simulator](https://atos.net/en/solutions/quantum-learning-machine), both
provided by Atos.

# Installation #
If you would like to test the code and you do not have access to a QLM, you can
install the open source
[myQLM](https://myqlm.github.io/myqlm_specific/install.html).

The best way to install the code would be through
[pyenv](https://github.com/pyenv/pyenv) and the
[pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv). Refer to their
guides on how to install them. After both of them are installed, you can run.

```
pyenv install 3.9.7
pyenv virtualenv 3.9.7 myqlm_env
```

where `3.9.7` is the python version used for this code and `myqlm_env` is the
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

`nptyping` is used to get dynamic hints for numpy. `sympy`, up to now, is only
used in testing to automatically compute the RREF of a matrix and compare the
results against our implementation. `parameterized` is used in order to have
parameterized testing. `jupyter` is required to launch notebooks.

Then, you can clone this repository and activate the environment.

```
cd <SOME_DIR>
git clone https://github.com/tigerjack/qat-utils.git
cd qat-utils
pyenv activate myqlm_env
```

where `<SOME_DIR>` can be whatever directory you want this repository to be
contained in.


# Structure #

  * The actual code is below `qat.external`.
  * `experiments` directory contains some experiments that have been made. 
  * The `notebooks` directory contains some jupyter notebooks explaining usage
  of most commonly used routines.
  * `test` directory contains all the tests for all the implemented routines.

# Tests #
The tests can be run using `python -m unittest` (all tests) or `python -m
unittest test.module_name` (only a specific test case, replacing module name
with the actual name of the module). For example, if you want to run all the
tests related to the RREF circuit, go to the root directory and run `python -m
unittest test.test_qroutine_rref`.

When launching tests, you can provide some optional environment variables

  * `LOG_LEVEL`, with values equal to the names provided by Python logging
utilities. E.g. `LOG_LEVEL=DEBUG python -m unittest test.test_qroutine_rref`.
  * `SLOW_TEST_ON=1` to enable also time consuming tests 
  * `QLM_ON=1` to use the QLM instead of myQLM
  * [x] `SIMULATOR`, to pass the name of a simulator. For myQLM, only the `pylinalg`
    simulator is actually available. For QLM, there are a variety of available
    simulators depending on the version.
    
# General Notes #

## Endianness ##

Most quantum toolkits use little-endianness to represent the quantum state. That
is, a 3 qubit register $|a \otimes b \otimes c\rangle$ has $qreg[0] = c$,
$qreg[1] = b$, $qreg[2] = a$.

In myqlm, on the other hand, the same quantum state corresponds to $qreg[0]=a$,
$qreg[1] = b$, $qreg[2] = c$, and therefore the notation can be thought as
big-endian.


# Contribution Guidelines #
If you would like to contribute to the code, please open a [GitHub
issue](https://github.com/tigerjack/qat-utils/issues). You can learn all the
details of myQLM by following the documentation freely available at
[https://myqlm.github.io/](https://myqlm.github.io/). You can also ask for help
on the official [slack channel](https://myqlmworkspace.slack.com/).

# Authors and citations #
Part of the code presented here was used in the results of the following articles

* Simone Perriello, Alessandro Barenghi and Gerardo Pelosi, A Quantum Circuit to
Speed-up the Cryptanalysis of Code-based Cryptosystems. International Workshop
on Post-quantum Cryptography for Secure Communications (PQC-SC). In Proceedings
of the 17th EAI International Conference on Security and Privacy in
Communication Networks - SecureComm 2021, Canterbury, Great Britain (online),
September 6-9, 2021. Lecture Notes of the Institute for Computer Sciences,
Social Informatics and Telecommunications Engineering. [Accepted on July 25th,
2021] [bibtex](TODO)
* Simone Perriello, Alessandro Barenghi and Gerardo Pelosi, A Complete Quantum
Circuit to Solve the Information Set Decoding Problem. In Proc. of the IEEE
International Conference on Quantum Computing and Engineering, (QCE) 2021,
Broomfield, CO, USA, October 18-22, 2021 (Fully virtual event). IEEE Computer
Society 2021. [Accepted on July 31th, 2021] [bibtex](TODO)



# To modify list #
  * [ ] Use slack suggestion for gate definition

# To implement list #
  * Reversible simulator
    * [X] Implementation
    * [ ] Integration with QLM 
    
  * Reversible combinatorial circuits
    * [x] Sorting network
    * [x] Benes network
  * State preparation 
    * [x] Dicke state
    * [ ] Quantum circuits for general multi-qubit gates: [link](https://arxiv.org/pdf/quant-ph/0404089.pdf)
    * [ ] Quantum-state preparation with universal gate decompositions:
      [link](https://arxiv.org/pdf/1003.5760.pdf)
    * [ ] Quantum Networks for generating arbitrary quantum states:
      [link](https://arxiv.org/pdf/quant-ph/0407102.pdf)
  * Encoding classical data
    * [x] Classical bitstring encoding 
    * [ ] Basis encoding - [link](https://arxiv.org/pdf/quant-ph/9807053.pdf)
    * [ ] Amplitude encoding - [link](https://arxiv.org/pdf/1703.10793.pdf)
    * [ ] Angle encoding - [link](https://arxiv.org/pdf/1711.11240.pdf)
    * [ ] Higher order embedding - [link](https://arxiv.org/pdf/1804.11326.pdf)
    * [ ] Variational/trained embedding - [link](https://arxiv.org/pdf/2001.03622.pdf)
  * Linear algebra
    * [x] Matrix init
    * [x] Row/Column swap
    * [x] Gauss-Jordan Elimination (useful to compute the inverse of a matrix)
    * [x] Moving columns to the start/end of the matrix
  * Arithmetic
    * [x] Cuccaro arithmetic
    * [x] TKK arithmetic
    * [x] My arithmetic
  * Qreg management
    * [x] Qreg reversal
    * [x] Qreg shift (left/right)
  * Various
    * [x] Computing Hamming Weight of a subset of qubits
    * [x] Check Hamming Weight of a subset of qubits
