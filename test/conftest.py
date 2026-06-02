"""File automatically read from pytest"""
import logging
from os import getenv
from test.common_pytest import SIMULATOR, CircuitTestHelpers

import pytest

LOGGER = logging.getLogger(__name__)


# Autouse logger setup
@pytest.fixture(scope="session", autouse=True)
def global_logger():
    """Create one logger for all tests and attach to helper base class."""
    logger = logging.getLogger("tests")
    level = getenv("LOG_LEVEL", "ERROR").upper()
    logging_level = getattr(logging, level, logging.ERROR)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(module)-4s %(levelname)-8s %(funcName)-12s %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(logging_level)
    # CircuitTestHelpers.logger = logger
    CircuitTestHelpers.set_logger(logger)
    yield


@pytest.fixture(scope="session", autouse=True)
def global_qpu():
    # Create once for the whole test session
    if SIMULATOR.lower() == "pylinalg":
        from qat.pylinalg import PyLinalg  # type:ignore
        qpu_instance = PyLinalg()
    elif SIMULATOR.lower() == "clinalg":
        from qat.myqlm_clinalg.qpu import CLinalg  # type:ignore
        qpu_instance = CLinalg()
    elif SIMULATOR.lower() == "linalg":
        # default to linalg
        from qat.qpus import LinAlg  # type:ignore
        qpu_instance = LinAlg()
    elif SIMULATOR.lower() == "stabs":
        from qat.qpus import Stabs  # type:ignore

        from kitqat.synthesis.mctrls.mcx import ccnot, x
        qpu_instance = Stabs()
        CircuitTestHelpers.links = [ccnot, x]
    elif SIMULATOR.lower() == "feynman":
        from qat.qpus import Feynman  # type:ignore
        qpu_instance = Feynman()
    elif SIMULATOR.lower() == "mps":
        from qat.qpus import MPS  # type:ignore
        qpu_instance = MPS(lnnize=True)
    elif SIMULATOR.lower() == "bdd":
        from qat.qpus import Bdd  # type:ignore
        qpu_instance = Bdd(48)
    else:
        raise Exception(f"Simulator choice {SIMULATOR} not correct")
    CircuitTestHelpers.set_qpu(qpu_instance)
    yield qpu_instance
    # Optional teardown
    # qpu_instance.shutdown()
