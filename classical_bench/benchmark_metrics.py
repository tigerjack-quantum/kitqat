import sys
import os
import math
import pandas as pd
import matplotlib.pyplot as plt
from qat.lang.AQASM import Program

# Add project root to PYTHONPATH for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from qatext.qroutines.algebraic.gf2x.Pinto_adders import cuccaro_adder_int, tkk_adder_int, qft_adder_int
    from qatext.qroutines.algebraic.gf2x.Pinto_basic_arith import mul_n_bit, schoolbook_reduction_int, adder_n_bit
    from qatext.qroutines.algebraic.gf2x.Pinto_toom_cook import karatsuba_modular, toom3_mult
    from qatext.qroutines.algebraic.gfp.Pinto_barret import barrett_reduction
    from qatext.qroutines.montgomery.Pinto_montgomery import montgomery_mult
    from qatext.utils.statistics.depth import compute_circuit_depth
except ImportError as e:
    print(f"Error importing routines: {e}")
    sys.exit(1)

def compute_all_metrics(circ):
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
            if gate_name == 'CCNOT':
                toffoli_count += 1
                is_toffoli = True
            elif gate_name == 'CNOT':
                cnot_count += 1
            elif gate_name == 'H':
                h_count += 1
            elif gate_name == 'X':
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
    prog = Program()
    try:
        arity = None
        if algo_name == "Barrett Redux":
            arity = 3 * n
        elif algo_name == "Toom-Cook 3":
            arity = 4 * n
        elif algo_name == "Karatsuba (Mod)":
            arity = 3 * n
        elif algo_name == "Montgomery Mult":
            arity = 3 * n
        elif algo_name == "QFT Adder":
            arity = 2 * n
            
        res = routine_factory(*args, **kwargs)
        routine = res._qroutine if hasattr(res, "_qroutine") else res
            
        if arity is None:
            if hasattr(routine, "arity"):
                arity = routine.arity
            elif hasattr(routine, "nbqbits"):
                arity = routine.nbqbits
            else:
                arity = 2*n 
                
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
    output_dir = os.path.join(os.path.dirname(__file__), "visual_linear")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    std_sizes = [8, 16, 32, 64, 128, 256, 512, 1024]
    toom_sizes = [9, 18, 27, 36, 45, 54, 63, 72, 90, 108, 126]
    redu_sizes = [8, 16, 32, 64, 128]
    qft_sizes = [8, 16, 32, 64, 128]

    categories = {
        "Adders": [ 
            ("Cuccaro Adder", cuccaro_adder_int, std_sizes),
            ("TKK Adder", tkk_adder_int, std_sizes),
            ("QFT Adder", qft_adder_int, qft_sizes),
        ],
        "Multipliers": [
            ("Schoolbook Mult", mul_n_bit, std_sizes),
            ("Karatsuba (Mod)", karatsuba_modular, std_sizes),
            ("Toom-Cook 3", toom3_mult, toom_sizes)
        ],
        "Reductions": [
            ("Schoolbook Reduction", schoolbook_reduction_int, redu_sizes),
            ("Montgomery Mult", montgomery_mult, redu_sizes),
            ("Barrett Redux", barrett_reduction, redu_sizes)
        ]
    }

    print("# Quantum Arithmetic FULL Metrics Report (Extended)")
    
    for cat_name, algos in categories.items():
        cat_results = []
        print(f"\n## {cat_name}")
        
        for algo_name, factory, sizes in algos:
            algo_results = []
            for n in sizes:
                args = [n, n]
                if algo_name in ["Schoolbook Mult", "Toom-Cook 3"]:
                    args = [n]
                elif algo_name in ["Karatsuba (Mod)", "Schoolbook Reduction"]:
                    args = [n, (1 << n) | 1]
                elif algo_name in ["Cuccaro Adder", "TKK Adder", "QFT Adder"]:
                    args = [n, n, False]
                elif algo_name == "Montgomery Mult":
                    p = (1 << n) - 1
                    if p % 2 == 0: p += 1
                    args = [n, p]
                elif algo_name == "Barrett Redux":
                    args = [n, (1 << (n-1)) + 1]

                m = get_metrics(factory, algo_name, n, *args)
                m['algo'] = algo_name
                m['n'] = n
                m['category'] = cat_name
                cat_results.append(m)
                algo_results.append(m)
            
            print(f"\n### {algo_name}")
            print("| n | Width | Depth | D x W | Toffoli | CNOT | H | X |")
            print("|---|-------|-------|-------|---------|------|---|---|")
            for r in algo_results:
                print(f"| {r['n']} | {r['width']} | {r['total_depth']} | {r['depth_width']} | {r['toffoli_count']} | {r['cnot_count']} | {r['h_count']} | {r['x_count']} |")

        df_cat = pd.DataFrame(cat_results).dropna(subset=['width'])
        if not df_cat.empty:
            plot_category_linear(cat_name, df_cat, output_dir)
            
    print(f"\nI grafici lineari e le nuove metriche sono stati generati in {output_dir}/")

if __name__ == "__main__":
    main()
