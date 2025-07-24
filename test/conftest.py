"""File automatically read from pytest"""
import logging
from os import getenv
from test.common_pytest import REVERSIBLE_ON, SIMULATOR

import pytest

LOGGER = logging.getLogger(__name__)


# Autouse logger setup
@pytest.fixture(autouse=True)
def setup_logger():
    logger = logging.getLogger(__name__)
    level = getenv("LOG_LEVEL")
    if level:
        logging_level = getattr(logging, level.upper(), logging.ERROR)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(module)-4s %(levelname)-8s %(funcName)-12s %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging_level)
    yield


# Simulator setup
@pytest.fixture(scope="class", autouse=True)
def setup_simulator(request):
    cls = request.cls
    cls.logger = logging.getLogger(cls.__name__)
    cls.qpu = None  # Override this in subclasses if needed
    cls.reversible_on = True if REVERSIBLE_ON else False
    if SIMULATOR.lower() == "pylinalg":
        from qat.pylinalg import PyLinalg  # type:ignore
        cls.qpu = PyLinalg()
    elif SIMULATOR.lower() == "linalg":
        # default to linalg
        from qat.qpus import LinAlg  # type:ignore
        cls.qpu = LinAlg()
    elif SIMULATOR.lower() == "stabs":
        from qat.qpus import Stabs  # type:ignore
        from qatext.synthesis.mctrls.mcx import ccnot, x
        cls.qpu = Stabs()
        cls.links = [ccnot, x]
    elif SIMULATOR.lower() == "feynman":
        from qat.qpus import Feynman  # type:ignore
        cls.qpu = Feynman()
    elif SIMULATOR.lower() == "mps":
        from qat.qpus import MPS  # type:ignore
        cls.qpu = MPS(lnnize=True)
    elif SIMULATOR.lower() == "bdd":
        from qat.qpus import Bdd  # type:ignore
        cls.qpu = Bdd(48)
    else:
        raise Exception(f"Simulator choice {SIMULATOR} not correct")
    yield
