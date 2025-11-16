#!/usr/bin/env python3
"""
NullSwap-style: PGD to perturb ArcFace embeddings (ensemble optional)
- Depend: torch, facenet-pytorch (or an ArcFace model wrapper), opencv-python
- You need an ArcFace model (onnx/pytorch). Example uses facenet-pytorch's InceptionResnetV1 as surrogate,
  but for real-world transferability, use ArcFace models (insightface).
"""
import argparse, cv2, numpy as np, torch
from facenet_pytorch import InceptionResnetV1

def preprocess(img, size=160):
    im = cv2.resize(img, (size,size)).astype(np.float32)/255.0
    im = (im - 0.5) / 0.5  # normalize approx for facenet
    return torch.tensor(im.transpose(2,0,1)[None]).float()

def deprocess(tensor):
    x = tensor.detach().cpu().numpy()[0].transpose(1,2,0)
    x = (x * 0.5) + 0.5
    return np.clip(x,0,1)

def ensemble_embeddings(models, x):
    es = []
    for m in models:
        with torch.no_grad():
            e = m(x).detach()
            es.append(e)
    return torch.cat(es, dim=1)  # concat embeddings

def pgd_cloak(img, models, eps=8/255.0, steps=30, alpha=1.0/255.0):
    x0 = preprocess(img).to('cpu')
    target_e = ensemble_embeddings(models, x0).detach()
    x = x0.clone().requires_grad_(True)
    for i in range(steps):
        e = ensemble_embeddings(models, x)
        # maximize distance from original embedding (or minimize cos sim)
        loss = -torch.nn.functional.cosine_similarity(e, target_e, dim=1).mean()
        loss.backward()
        x.data = x.data + alpha * torch.sign(x.grad.data)
        x.data = torch.clamp(x.data, x0 - eps, x0 + eps)
        x.grad.zero_()
    return deprocess(x)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("--outfile", default=None)
    parser.add_argument("--eps", type=float, default=8.0)
    parser.add_argument("--steps", type=int, default=30)
    args = parser.parse_args()

    img = cv2.imread(args.infile)[:,:,::-1].astype(np.float32)
    # load surrogate models (example uses 1 facenet model; replace with ArcFace models if available)
    m1 = InceptionResnetV1(pretrained='vggface2').eval()
    models = [m1]
    adv = pgd_cloak(img, models, eps=args.eps/255.0, steps=args.steps, alpha=(args.eps/args.steps)/255.0)
    outp = args.outfile or args.infile.replace(".png","_nullswap.png")
    cv2.imwrite(outp, (adv*255).astype('uint8')[:,:,::-1])
    print("Saved", outp)
