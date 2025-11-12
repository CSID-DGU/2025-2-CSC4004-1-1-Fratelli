#!/usr/bin/env python3
"""
LEAT-style normalized gradient ensemble PGD:
- You must supply a list of encoder functions that accept torch image and return latent (requires_grad True)
- Example encoders are wrappers around pretrained model encoders (StyleCLIP encoder, SimSwap encoder, DiffAE, etc.)
"""
import torch, numpy as np, cv2, argparse

def normalized_gradients(encoders, x):
    """
    encoders: list of callables enc_i(x) -> latent tensor (batch x D)
    returns: averaged normalized gradient w.r.t x
    """
    grads = []
    for enc in encoders:
        # forward
        z = enc(x)
        # define loss: we want to maximize difference from original latent -> use L2 between z and z0 stored externally
        # for demo, use negative L2 norm (to get gradient)
        loss = -torch.norm(z, p=2)
        loss.backward(retain_graph=True)
        g = x.grad.detach().clone()
        # normalize gradient
        g_norm = g / (g.norm() + 1e-10)
        grads.append(g_norm)
        x.grad.zero_()
    avg = torch.stack(grads, dim=0).mean(dim=0)
    return avg

def pgd_leat(x0, encoders, eps=0.05, steps=30, alpha=0.01, device='cpu'):
    x = x0.clone().detach().to(device).requires_grad_(True)
    for t in range(steps):
        g = normalized_gradients(encoders, x)
        x.data = x.data + alpha * torch.sign(g)
        x.data = torch.max(torch.min(x.data, x0 + eps), x0 - eps)
        x.grad.zero_()
    return x.detach()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("--outfile", default=None)
    args = parser.parse_args()

    # --- user must implement/plug encoder wrappers: enc(x) -> torch tensor latent
    def dummy_encoder(x):
        # placeholder: returns a linear embedding (NOT a real encoder). Replace with real model.
        # expect x shape [1,3,H,W]
        return torch.nn.functional.adaptive_avg_pool2d(x,1).view(1,-1)

    encs = [dummy_encoder, dummy_encoder]  # replace with real encoders
    im = cv2.imread(args.infile)[:,:,::-1].astype(np.float32)/255.0
    x0 = torch.tensor(im.transpose(2,0,1)[None]).float()
    adv = pgd_leat(x0, encs, eps=0.05, steps=30, alpha=0.01)
    out = adv.cpu().numpy()[0].transpose(1,2,0)
    out = np.clip(out,0,1)
    outp = args.outfile or args.infile.replace(".png","_leat.png")
    cv2.imwrite(outp, (out*255).astype('uint8')[:,:,::-1])
    print("Saved", outp)
