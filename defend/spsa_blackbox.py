#!/usr/bin/env python3
"""
SPSA black-box optimizer skeleton
- You must implement evaluate_image(path) -> float (lower is better/worse depending on definition)
- The code performs SPSA updates on an image (or patch) to minimize the evaluation score.
"""
import numpy as np, cv2, argparse, os, subprocess, tempfile

def evaluate_image(path):
    """
    User-provided: run external deepfake pipeline or face-recognition and return a scalar score.
    Example: run a command-line face-swap, then compute face-similarity vs expected.
    Here we raise to force user to implement.
    """
    raise NotImplementedError("Please implement evaluate_image(path) to run your pipeline and return metric")

def spsa_optimize(img, iters=200, a=0.1, c=0.01, alpha=0.602, gamma=0.101):
    """
    img: HxWx3 float [0,1]
    return: adv image
    """
    x = img.copy()
    baseline = None
    for k in range(1, iters+1):
        ak = a / (k**alpha)
        ck = c / (k**gamma)
        # random perturbation vector (binary +1/-1)
        delta = np.random.choice([1,-1], size=x.shape).astype(np.float32)
        x_plus = np.clip(x + ck*delta, 0.0, 1.0)
        x_minus = np.clip(x - ck*delta, 0.0, 1.0)
        # save temp files and evaluate
        pfile = lambda arr, idx: f"/tmp/spsa_{k}_{idx}.png"
        cv2.imwrite(pfile(x_plus, 'p'), (x_plus*255).astype('uint8')[:,:,::-1])
        cv2.imwrite(pfile(x_minus, 'm'), (x_minus*255).astype('uint8')[:,:,::-1])
        y_plus = evaluate_image(pfile(x_plus,'p'))
        y_minus = evaluate_image(pfile(x_minus,'m'))
        # approximate gradient
        g_hat = (y_plus - y_minus) / (2.0 * ck * delta)
        # update
        x = x - ak * g_hat  # minimize metric
        x = np.clip(x, 0.0, 1.0)
        print(f"Iter {k}: y+={y_plus:.4f} y-={y_minus:.4f}")
    return x

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("--outfile", default=None)
    parser.add_argument("--iters", type=int, default=200)
    args = parser.parse_args()

    im = cv2.imread(args.infile)[:,:,::-1].astype(np.float32)/255.0
    # NOTE: user must implement evaluate_image above to integrate with their pipeline
    try:
        adv = spsa_optimize(im, iters=args.iters)
        outp = args.outfile or args.infile.replace(".png","_spsa.png")
        cv2.imwrite(outp, (adv*255).astype('uint8')[:,:,::-1])
        print("Saved", outp)
    except NotImplementedError as e:
        print(e)
