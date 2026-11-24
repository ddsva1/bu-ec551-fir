"""Generate a test stimulus, run the Verilog for all 4 sets, compare bit-exact
against a Python fixed-point model, and report tone attenuation."""
import subprocess, numpy as np
FS, N = 48_000, 1200
t = np.arange(N) / FS
x = 0.3*np.sin(2*np.pi*500*t) + 0.3*np.sin(2*np.pi*3000*t) + 0.3*np.sin(2*np.pi*10000*t)
x = np.round(x * 32767).astype(int)
x[900:1000] = np.where((np.arange(100) // 12) % 2, 32767, -32768)   # full-scale square: tests saturation
with open("stim.mem", "w") as f:
    f.writelines(f"{v & 0xFFFF:04x}\n" for v in x)

img = [int(l, 16) for l in open("fir_coeffs.mem")]
img = [v - 65536 if v >= 32768 else v for v in img]
TAPS = 371

def model(h):
    y = []
    for n in range(N):
        acc = sum(h[k] * x[n - k] for k in range(TAPS) if n - k >= 0)
        r = (acc + (1 << 14)) >> 15
        y.append(max(-32768, min(32767, r)))
    return np.array(y)

subprocess.run(["iverilog", "-g2005", "-o", "sim", "fir_serial.v", "tb_fir_serial.v"], check=True)
for s in range(4):
    subprocess.run(["vvp", "-n", "sim", f"+SET={s}", f"+OUT=out_set{s}.txt"], check=True,
                   stdout=subprocess.DEVNULL)
    hw = np.array([int(l) for l in open(f"out_set{s}.txt")])
    ref = model(img[s*512: s*512 + TAPS])
    mism = int(np.sum(hw != ref)) if len(hw) == len(ref) else -1
    sat = int(np.sum(np.abs(ref) >= 32767))
    # tone levels, steady state: after the 371-tap fill, before the square burst
    seg = hw[400:880] / 32768   # 480 samples = 100 Hz bins: every test tone sits on a bin
    def lvl(f):
        c = np.exp(-2j*np.pi*f*np.arange(400, 880)/FS)
        return 20*np.log10(2*abs(np.dot(seg, c))/len(seg)/0.3 + 1e-12)
    print(f"set {s}: {len(hw)} outputs, mismatches vs model = {mism}, saturated samples = {sat}, "
          f"500 Hz {lvl(500):+.1f} dB, 3 kHz {lvl(3000):+.1f} dB, 10 kHz {lvl(10000):+.1f} dB")
