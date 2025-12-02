#!/usr/bin/env python3
"""
LandmarkBreaker-style PGD:
- 입력: PNG/JPG 이미지 (RGB)
- 출력: perturbed image saved as *_adv.png
- Depend: face_alignment (pip install face-alignment), pytorch, numpy, opencv-python
"""
import os, sys, argparse, cv2, numpy as np, torch
import face_alignment
from tqdm import tqdm

def load_image(path, size=None):
    im = cv2.imread(path)[:,:,::-1]  # BGR->RGB
    if size is not None:
        im = cv2.resize(im, size, interpolation=cv2.INTER_LINEAR)
    return im.astype(np.float32)/255.0

def save_image(rgb, path):
    bgr = (rgb*255.0).astype(np.uint8)[:,:,::-1]
    cv2.imwrite(path, bgr)

def landmarks_of(np_img, fa):
    # face_alignment returns list of (68,2) arrays (float)
    preds = fa.get_landmarks_from_image((np_img*255).astype(np.uint8))
    if preds is None or len(preds)==0:
        return None
    return preds[0]  # first face

def pgd_maximize_landmark(img, fa, eps=16/255.0, steps=20, alpha=1.0/255.0, mask_face=True):
    """
    Simple PGD: maximize L2 distance between original landmarks and perturbed landmarks
    - mask_face: only perturb outside face hull (as LandmarkBreaker++ suggests)
    """
    h,w,_ = img.shape
    orig_lm = landmarks_of(img, fa)
    if orig_lm is None:
        raise RuntimeError("No face detected")
    # build face mask hull (1=face area)
    hull = cv2.convexHull(orig_lm.astype(np.int32))
    mask = np.zeros((h,w), dtype=np.uint8)
    cv2.fillConvexPoly(mask, hull, 1)
    mask = mask.astype(np.float32)  # 1 face, 0 background
    mask_inv = 1.0 - mask  # perturb only outside if mask_face True

    x0 = torch.tensor(img.transpose(2,0,1)[None], dtype=torch.float32)  # 1x3xHxW
    x = x0.clone().detach().requires_grad_(True)
    orig_lm_t = torch.tensor(orig_lm, dtype=torch.float32)

    for t in range(steps):
        # convert current x to numpy for face_alignment
        x_np = x.detach().cpu().numpy()[0].transpose(1,2,0)
        cur_lm = landmarks_of(x_np, fa)
        if cur_lm is None:
            # if detector fails, then attack succeeded - stop
            break
        cur_lm_t = torch.tensor(cur_lm, dtype=torch.float32)
        # loss = negative L2 between orig and cur (we maximize L2 -> minimize negative)
        loss = -torch.mean((orig_lm_t - cur_lm_t).pow(2))
        loss.backward()
        grad = x.grad.data
        # gradient ascent step (sign)
        x.data = x.data + alpha * torch.sign(grad)
        # project onto L_inf ball
        x.data = torch.max(torch.min(x.data, x0 + eps), x0 - eps)
        # optionally mask inside face to avoid visible distortion (LandmarkBreaker++)
        if mask_face:
            m = torch.tensor(mask_inv[None,None,:,:], dtype=torch.float32)
            x.data = x0 * (1.0 - m) + x.data * m
        x.grad.zero_()
    out = x.detach().cpu().numpy()[0].transpose(1,2,0)
    out = np.clip(out, 0.0, 1.0)
    return out

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("--outfile", default=None)
    parser.add_argument("--eps", type=float, default=16.0, help="max pixel L_inf (px)") 
    parser.add_argument("--steps", type=int, default=20)
    parser.add_argument("--alpha_px", type=float, default=1.0, help="step size in pixel")
    args = parser.parse_args()

    img = load_image(args.infile)
    fa = face_alignment.FaceAlignment(face_alignment.LandmarksType._2D, flip_input=False)
    adv = pgd_maximize_landmark(img, fa, eps=args.eps/255.0, steps=args.steps, alpha=args.alpha_px/255.0)
    outp = args.outfile or args.infile.replace(".png","_adv.png").replace(".jpg","_adv.png")
    save_image(adv, outp)
    print("Saved", outp)
