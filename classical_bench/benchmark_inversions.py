import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
from qat.lang.AQASM import Program

# Add project root to PYTHONPATH for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from qatext.qroutines.algebraic.gf2x.inversion import flt_div
    from qatext.qroutines.algebraic.gfp.kaliski_inversion import kaliski_block
    from qatext.utils.statistics.depth import compute_circuit_depth
except ImportError as e:
    print(f"Error importing routines: {e}")
    sys.exit(1)

def get_m_bits(n):
    """Restituisce il polinomio irriducibile in formato intero per GF(2^n)."""
    if n == 4: return 0x13
    if n == 6: return 0x43 # x^6 + x + 1 # x^4 + x + 1
    if n == 8: return 0x11B # x^8 + x^4 + x^3 + x + 1
    if n == 10: return 0x409 # x^10 + x^3 + 1
    if n == 12: return 0x1009 # x^12 + x^3 + 1
    if n == 16: return 0x1002B # x^16 + x^5 + x^3 + x + 1
    if n == 32: return 0x10000008D # x^32 + x^7 + x^3 + x^2 + 1
    if n == 64: return 0x1000000000000001B # x^64 + x^4 + x^3 + x + 1
    if n == 128: return 0x100000000000000000000000000000087 # x^128 + x^7 + x^2 + x + 1
    return (1 << n) | 3

def compute_all_metrics(circ):
    """
    Stessa identica logica di estrazione usata in benchmark_metrics.py
    """
    toffoli_count = 0
    cnot_count = 0
    h_count = 0
    x_count = 0
    other_count = 0
    
    depth_array_toffoli = [0] * circ.nbqbits
    total_gates = 0
    
    try:
        # Contiamo i gate totali e le porte in modo granulare
        for op in circ.iterate_simple():
            total_gates += 1
            gate_name, _, qbits = op
            
            is_toffoli = False
            if gate_name == 'CCNOT' or gate_name == 'C-CCNOT':
                toffoli_count += 1
                is_toffoli = True
            elif gate_name == 'CNOT' or gate_name == 'C-CNOT':
                cnot_count += 1
            elif gate_name == 'H' or gate_name == 'C-H':
                h_count += 1
            elif gate_name == 'X' or gate_name == 'C-X':
                x_count += 1
            else:
                other_count += 1
            
            max_d_toffoli = 0
            for q in qbits:
                if depth_array_toffoli[q] > max_d_toffoli:
                    max_d_toffoli = depth_array_toffoli[q]
            
            if is_toffoli:
                max_d_toffoli += 1
                
            for q in qbits:
                depth_array_toffoli[q] = max_d_toffoli
    except Exception as e:
        total_gates = len(circ.ops)
        print(f"Errore nello srotolamento per le metriche: {e}")
        
    toffoli_depth = max(depth_array_toffoli) if depth_array_toffoli else 0
    
    # Calcolo della profondità totale (tutte le porte)
    try:
        total_depth, _, _ = compute_circuit_depth(circ)
    except:
        total_depth = 0
        
    return {
        "total_gates": total_gates,
        "total_depth": total_depth,
        "toffoli_count": toffoli_count,
        "toffoli_depth": toffoli_depth,
        "cnot_count": cnot_count,
        "h_count": h_count,
        "x_count": x_count,
        "other_count": other_count
    }

def get_metrics(routine_factory, algo_name, n, *args, **kwargs):
    """
    Crea il programma, alloca i qubit esatti e calcola le metriche fisiche
    del circuito quantistico.
    """
    prog = Program()
    try:
        if algo_name == "FLT Inversion":
            arity = 3 * n
        elif algo_name == "Kaliski Inversion":
            arity = 5 * n + 4 + 2 * n - 1 # ~7n + 3
        else:
            arity = 3 * n
            
        res = routine_factory(*args, **kwargs)
        routine = res._qroutine if hasattr(res, "_qroutine") else res
                
        qbits = prog.qalloc(arity)
        prog.apply(routine, qbits)
        
    except Exception as e:
        return {"width": None, "total_gates": None, "total_depth": None, "toffoli_count": None, "error": str(e)}

    circuit = prog.to_circ()
    nb_qubits = circuit.nbqbits
    metrics = compute_all_metrics(circuit)
    
    metrics["width"] = nb_qubits
    metrics["depth_width"] = metrics["total_depth"] * nb_qubits
        
    return metrics

def plot_category_linear(category_name, df, output_dir):
    metrics = ["total_gates", "total_depth", "toffoli_count", "depth_width"]
    pretty_metrics = [
        "Total Gates (Tutte le porte)", 
        "Total Depth (Profondità Totale)", 
        "Toffoli Count (N. Porte Toffoli)", 
        "Depth x Width (Figure of Merit)"
    ]
    
    for metric, title in zip(metrics, pretty_metrics):
        plt.figure(figsize=(10, 6))
        for algo in df['algo'].unique():
            algo_df = df[df['algo'] == algo]
            algo_df = algo_df.sort_values(by='n')
            plt.plot(algo_df['n'], algo_df[metric], marker='o', label=algo, linewidth=2)
        
        plt.title(f"{category_name}: {title} vs n")
        plt.xlabel("n (bits)")
        plt.ylabel(title)
        
        plt.xscale('linear')
        plt.yscale('linear')
        
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.7)
        
        filename = f"{category_name.lower()}_{metric}_linear.png"
        plt.savefig(os.path.join(output_dir, filename))
        plt.close()

def main():
    output_dir = os.path.join(os.path.dirname(__file__), "visual_inversions_real")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # N values scelti per essere simulabili in tempi ragionevoli dal framework
    test_sizes = [4, 6,8, 10, 12]

    inversions = [
        ("FLT Inversion", flt_div, test_sizes),
        ("Kaliski Inversion", kaliski_block, test_sizes)
    ]

    print("# Quantum Arithmetic - Actual Inversion Metrics")
    cat_results = []
    
    for algo_name, factory, sizes in inversions:
        algo_results = []
        for n in sizes:
            if algo_name == "FLT Inversion":
                args = [n, get_m_bits(n)]
            elif algo_name == "Kaliski Inversion":
                args = [n]
                
            m = get_metrics(factory, algo_name, n, *args)
            if m.get("error"):
                print(f"Errore in {algo_name} n={n}: {m['error']}")
                continue
                
            m['algo'] = algo_name
            m['n'] = n
            m['category'] = "Inversions"
            cat_results.append(m)
            algo_results.append(m)
        
        print(f"\n### {algo_name}")
        print("| n | Width | Total Gates | Depth | D x W | Toffoli | CNOT | X |")
        print("|---|-------|-------------|-------|-------|---------|------|---|")
        for r in algo_results:
            print(f"| {r['n']} | {r['width']} | {r['total_gates']} | {r['total_depth']} | {r['depth_width']} | {r['toffoli_count']} | {r['cnot_count']} | {r['x_count']} |")

    df_cat = pd.DataFrame(cat_results).dropna(subset=['width'])
    if not df_cat.empty:
        plot_category_linear("Inversions", df_cat, output_dir)
        
    print(f"\nI grafici estratti dall'implementazione reale sono in {output_dir}/")

if __name__ == "__main__":
    main()