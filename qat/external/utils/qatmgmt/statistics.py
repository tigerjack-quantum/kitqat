def reformat_statistics(stats: dict):
    """Reformat the statistics utility of a circuit object in order to merge
    same gates w/ different names."""
    gates = stats["gates"].copy()
    delete = []
    for gatename, numbers in gates.items():
        if gatename in ("C-X", "C-NOT"):
            gates["CNOT"] = gates.get("CNOT", 0) + numbers
            delete.append(gatename)
        elif gatename in ("C-C-X", "C-C-NOT", "C-CNOT"):
            gates["CCNOT"] = gates.get("CCNOT", 0) + numbers
            delete.append(gatename)
        elif gatename in ("C-SWAP"):
            gates["CSWAP"] = gates.get("CSWAP", 0) + numbers
            delete.append(gatename)
    for gatename in delete:
        gates.pop(gatename)
    stats["gates"] = gates
    return stats
