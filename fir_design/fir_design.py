"""FIR low-pass design for the FPGA audio demo.

Four switchable low-pass sets (SW1-2), all the same length so the
hardware is identical: only the BRAM address offset changes.
"""
import numpy as np
from scipy.signal import kaiserord, firwin, freqz

FS = 48_000            # audio sample rate (Hz)
ATTEN_DB = 60          # stopband attenuation spec (after quantization)
DESIGN_MARGIN_DB = 3   # designed 3 dB deeper so rounding to Q1.15 still meets spec
TRANSITION = 500       # transition width (Hz), same for every set
CUTOFFS = [1000, 2000, 4000, 8000]   # -6 dB cutoff per set (SW1-2 = 0..3)
COEF_BITS = 16         # Q1.15
SET_STRIDE = 512       # BRAM words per set (power of 2 >= taps)

numtaps, beta = kaiserord(ATTEN_DB + DESIGN_MARGIN_DB, TRANSITION / (FS / 2))
numtaps |= 1           # odd -> Type I, integer group delay

def design(fc):
    h = firwin(numtaps, fc, window=("kaiser", beta), fs=FS)
    q = np.round(h * 2**(COEF_BITS - 1)).astype(int)
    return h, q

def measure(hq, fc):
    w, H = freqz(hq / 2**(COEF_BITS - 1), worN=1 << 15, fs=FS)
    mag = 20 * np.log10(np.maximum(np.abs(H), 1e-12))
    fp, fst = fc - TRANSITION / 2, fc + TRANSITION / 2
    ripple = mag[w <= fp].max() - mag[w <= fp].min()
    stop = -mag[w >= fst].max()
    f3 = w[np.argmax(mag < -3)]
    return dict(fp=fp, fstop=fst, ripple_db=ripple, stop_db=stop, f3=f3,
                dc_gain=hq.sum() / 2**(COEF_BITS - 1), max_coef=int(np.abs(hq).max()),
                abs_sum=np.abs(hq).sum() / 2**(COEF_BITS - 1)), w, mag

if __name__ == "__main__":
    sets, rows = [], []
    print(f"taps={numtaps} beta={beta:.3f} delay={(numtaps-1)//2} samples "
          f"({(numtaps-1)/2/FS*1e3:.2f} ms)")
    curves = {}
    for i, fc in enumerate(CUTOFFS):
        h, q = design(fc)
        m, w, mag = measure(q, fc)
        sets.append(q)
        curves[fc] = (w, mag)
        print(f"set {i}: fc={fc} fp={m['fp']:.0f} fstop={m['fstop']:.0f} "
              f"ripple={m['ripple_db']:.4f} dB stop={m['stop_db']:.1f} dB "
              f"f-3dB={m['f3']:.0f} dc={m['dc_gain']:.5f} max|h|={m['max_coef']} "
              f"sum|h|={m['abs_sum']:.3f}")
    # BRAM image: 4 sets x 512 words, zero padded
    img = np.zeros(4 * SET_STRIDE, dtype=int)
    for i, q in enumerate(sets):
        img[i * SET_STRIDE: i * SET_STRIDE + numtaps] = q
    with open("fir_coeffs.mem", "w") as f:
        for v in img:
            f.write(f"{v & 0xFFFF:04x}\n")
    with open("fir_coeffs.coe", "w") as f:
        f.write("; FIR demo coefficients, Q1.15, 4 sets x 512 words\n")
        f.write("memory_initialization_radix=16;\nmemory_initialization_vector=\n")
        f.write(",\n".join(f"{v & 0xFFFF:04x}" for v in img) + ";\n")
    with open("fir_coeffs.csv", "w") as f:
        f.write("tap," + ",".join(f"set{i}_{fc}Hz" for i, fc in enumerate(CUTOFFS)) + "\n")
        for n in range(numtaps):
            f.write(f"{n}," + ",".join(str(q[n]) for q in sets) + "\n")
    # response rows for the doc chart: 0..12 kHz, 100 Hz steps
    with open("response.csv", "w") as f:
        f.write("freq_hz," + ",".join(f"{fc}" for fc in CUTOFFS) + "\n")
        for fr in range(0, 12001, 100):
            vals = []
            for fc in CUTOFFS:
                w, mag = curves[fc]
                vals.append(f"{max(np.interp(fr, w, mag), -100):.1f}")
            f.write(f"{fr}," + ",".join(vals) + "\n")
