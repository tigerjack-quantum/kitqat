# Endianness #

Most quantum toolkits use little-endianness to represent the quantum state. That
is, a 3 qubit register $|a \otimes b \otimes c\rangle$ has $qreg[0] = c$,
$qreg[1] = b$, $qreg[2] = a$.

In myqlm, on the other hand, the same quantum state corresponds to $qreg[0]=a$,
$qreg[1] = b$, $qreg[2] = c$, and therefore the notation can be thought as
big-endian.



