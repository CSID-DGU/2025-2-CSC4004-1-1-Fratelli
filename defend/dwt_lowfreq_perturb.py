#!/usr/bin/env python3
"""
DWT low-frequency perturbation (per-frame)
- Depend: pywt, numpy, opencv-python
"""
import argparse, cv2, numpy as np, pywt

def perturb_dwt_lowfreq(img, alpha=0.02, wave='haar'):
    # img: HxWx3 float [0,1]
    out = img.copy()
    for c in range(3):
        coeffs2 = pywt.dwt2(out[:,:,c], wave)
        cA, (cH, cV, cD) = coeffs2
        # add smooth noise to approx coefficients
        noise = np.random.normal(scale=alpha * np.std(cA), size=cA.shape)
        cA_p = cA + noise
        out[:,:,c] = pywt.idwt2((cA_p, (cH,cV,cD)), wave)
    out = np.clip(out, 0.0, 1.0)
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("--outfile", default=None)
    parser.add_argument("--alpha", type=float, default=0.02)
    args = parser.parse_args()

    im = cv2.imread(args.infile)[:,:,::-1].astype(np.float32)/255.0
    adv = perturb_dwt_lowfreq(im, alpha=args.alpha)
    outp = args.outfile or args.infile.replace(".png","_dwt.png").replace(".jpg","_dwt.png")
    cv2.imwrite(outp, (adv*255).astype('uint8')[:,:,::-1])
    print("Saved", outp)
