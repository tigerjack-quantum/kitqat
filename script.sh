#!/bin/bash - 
#===============================================================================
#
#          FILE: script.sh
# 
#         USAGE: ./script.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: YOUR NAME (), 
#  ORGANIZATION: 
#       CREATED: 05/22/2026 15:02
#      REVISION:  ---
#===============================================================================

set -o nounset                              # Treat unset variables as an error
# restructure.sh
# Run from the repository root after merging the FedericoPinto branch.
# Renames all Pinto_* files to consistent snake_case names,
# relocates misplaced test files to mirror the source tree,
# and prepends an author comment to every affected Python file.
set -euo pipefail

AUTHOR_COMMENT="# Author: Federico Pinto"

# Prepend author comment if not already present
add_author() {
    local f="$1"
    if [[ -f "$f" ]] && ! head -1 "$f" | grep -q "Author:"; then
        sed -i "1s|^|${AUTHOR_COMMENT}\n|" "$f"
    fi
}

echo "==> Renaming source files..."

# gf2x — Pinto_basic_arith replaces the existing arith.py
git rm qatext/qroutines/algebraic/gf2x/arith.py
git mv qatext/qroutines/algebraic/gf2x/Pinto_basic_arith.py \
       qatext/qroutines/algebraic/gf2x/arith.py
add_author qatext/qroutines/algebraic/gf2x/arith.py

git mv qatext/qroutines/algebraic/gf2x/Pinto_adders.py \
       qatext/qroutines/algebraic/gf2x/adders.py
add_author qatext/qroutines/algebraic/gf2x/adders.py

git mv qatext/qroutines/algebraic/gf2x/Pinto_inversion.py \
       qatext/qroutines/algebraic/gf2x/inversion.py
add_author qatext/qroutines/algebraic/gf2x/inversion.py

git mv qatext/qroutines/algebraic/gf2x/Pinto_toom_cook.py \
       qatext/qroutines/algebraic/gf2x/toom_cook.py
add_author qatext/qroutines/algebraic/gf2x/toom_cook.py

# gfp
git mv qatext/qroutines/algebraic/gfp/Pinto_barret.py \
       qatext/qroutines/algebraic/gfp/barret.py
add_author qatext/qroutines/algebraic/gfp/barret.py

git mv qatext/qroutines/algebraic/gfp/Pinto_kaliski_inversion.py \
       qatext/qroutines/algebraic/gfp/kaliski_inversion.py
add_author qatext/qroutines/algebraic/gfp/kaliski_inversion.py

# montgomery
git mv qatext/qroutines/montgomery/Pinto_montgomery.py \
       qatext/qroutines/montgomery/montgomery.py
add_author qatext/qroutines/montgomery/montgomery.py

echo "==> Setting up missing test directories..."

# algebraic/gf2x test dir (new — doesn't exist in main)
mkdir -p test/qatext/qroutines/algebraic/gf2x
if [[ ! -f test/qatext/qroutines/algebraic/gf2x/__init__.py ]]; then
    touch test/qatext/qroutines/algebraic/gf2x/__init__.py
    git add test/qatext/qroutines/algebraic/gf2x/__init__.py
fi

# algebraic/gfp test dir (existed but had no __init__.py)
if [[ ! -f test/qatext/qroutines/algebraic/gfp/__init__.py ]]; then
    touch test/qatext/qroutines/algebraic/gfp/__init__.py
    git add test/qatext/qroutines/algebraic/gfp/__init__.py
fi

# algebraic __init__.py
if [[ ! -f test/qatext/qroutines/algebraic/__init__.py ]]; then
    touch test/qatext/qroutines/algebraic/__init__.py
    git add test/qatext/qroutines/algebraic/__init__.py
fi

# montgomery test dir (new)
mkdir -p test/qatext/qroutines/montgomery
if [[ ! -f test/qatext/qroutines/montgomery/__init__.py ]]; then
    touch test/qatext/qroutines/montgomery/__init__.py
    git add test/qatext/qroutines/montgomery/__init__.py
fi

echo "==> Relocating and renaming test files..."

# gf2x tests — were wrongly placed in arith/
git mv test/qatext/qroutines/arith/test_pinto_adders.py \
       test/qatext/qroutines/algebraic/gf2x/test_adders.py
add_author test/qatext/qroutines/algebraic/gf2x/test_adders.py

git mv test/qatext/qroutines/arith/test_pinto_basic_arith.py \
       test/qatext/qroutines/algebraic/gf2x/test_arith.py
add_author test/qatext/qroutines/algebraic/gf2x/test_arith.py

git mv test/qatext/qroutines/arith/test_pinto_inversion.py \
       test/qatext/qroutines/algebraic/gf2x/test_inversion.py
add_author test/qatext/qroutines/algebraic/gf2x/test_inversion.py

git mv test/qatext/qroutines/arith/test_Pinto_toom_cook.py \
       test/qatext/qroutines/algebraic/gf2x/test_toom_cook.py
add_author test/qatext/qroutines/algebraic/gf2x/test_toom_cook.py

# gfp tests — right folder, just rename
git mv test/qatext/qroutines/algebraic/gfp/test_Pinto_barret.py \
       test/qatext/qroutines/algebraic/gfp/test_barret.py
add_author test/qatext/qroutines/algebraic/gfp/test_barret.py

git mv test/qatext/qroutines/algebraic/gfp/test_pinto_kaliski_inversion.py \
       test/qatext/qroutines/algebraic/gfp/test_kaliski_inversion.py
add_author test/qatext/qroutines/algebraic/gfp/test_kaliski_inversion.py

# montgomery test — was wrongly placed in arith/
git mv test/qatext/qroutines/arith/test_pinto_montgomery.py \
       test/qatext/qroutines/montgomery/test_montgomery.py
add_author test/qatext/qroutines/montgomery/test_montgomery.py

# test_qft_adder stays in arith/ — no Pinto prefix to strip
add_author test/qatext/qroutines/arith/test_qft_adder.py

echo ""
echo "==> Done. Review the staged changes before committing:"
echo "    git status"
echo "    git diff --cached --stat"
echo ""
echo "    Then commit with:"
echo "    git commit -m 'refactor: rename Pinto_* files, reorganise test tree'"

