from typing import NamedTuple, Type, Union


class QRegsProperties(NamedTuple):
    # This is for 1 or more collection of qregs
    slic: slice
    # number of qregs aggregated
    n: int | None
    # size of each qreg
    m: int | None
    qtype: Type[Union[int, str]]
    # if True, should set the slice stop to -1, and n to -1, and m to -1
    unknown_size: bool = False
