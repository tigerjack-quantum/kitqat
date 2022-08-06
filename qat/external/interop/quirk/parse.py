import math
from sympy import parsing
import numpy as np

UNI_TO_UTF = {
    "½": '1 / 2',
    "¼": '1 / 4',
    "¾": '3 / 4',
    "⅓": '1 / 3',
    "⅔": '2 / 3',
    "⅕": '1 / 5',
    "⅖": '2 / 5',
    "⅗": '3 / 5',
    "⅘": '4 / 5',
    "⅙": '1 / 6',
    "⅚": '5 / 6',
    "⅐": '1 / 7',
    "⅛": '1 / 8',
    "⅜": '3 / 8',
    "⅝": '5 / 8',
    "⅞": '7 / 8',
    "⅑": '1 / 9',
    "⅒": '1 / 10',
}
UNI_TO_UTF_T = str.maketrans(UNI_TO_UTF)

_RM_CHARS_T = str.maketrans({'\'': '', '{': '', '}': ''})


def parse_matrix(matrix: str):
    """Expect something like {{√½,√½i},{√½i,√½}}"""

    matrix_arr = matrix.strip().translate(_RM_CHARS_T).split(',')
    rc = math.log2(len(matrix_arr))
    assert rc.is_integer(), "Dimensions are wrong"
    rc = int(rc)

    def del_sqrt_symbol():
        # It seems it uses sqrt only for simple expressions
        if '√' not in matrix:
            return matrix_arr
        arr = []
        for elem in matrix_arr:
            try:
                idx = elem.index('√')
                has_other_terms = len(elem) > idx + 2
                elem_tmp = 'sqrt(' + elem[idx + 1:idx + 2] + ')'
                if has_other_terms:
                    elem_tmp += '*' + elem[idx + 2:]
                elem = elem_tmp
            except ValueError:
                pass
            finally:
                elem_mat = parsing.parse_expr(elem.translate(UNI_TO_UTF_T)).n()
                elem_mat = elem_mat.subs({'i': '1j'})
                arr.append(elem_mat)
        return arr

    matrix_arr_math = del_sqrt_symbol()
    matrix_arr_math = np.array(matrix_arr_math, dtype=complex).reshape(rc, rc)

    return matrix_arr_math
