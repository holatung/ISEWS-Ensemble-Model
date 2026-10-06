"""
Dependency-light deep learning written in pure NumPy, so the prototype runs anywhere.

TemporalCNN
    A dilated temporal convolutional network (TCN) for multi-label classification
    of interference modalities from a 24-hour, 14-channel telemetry window.
    Architecture:
        Conv1D(14->32, k=3, d=1) - ReLU
        Conv1D(32->32, k=3, d=2) - ReLU
        Conv1D(32->32, k=3, d=4) - ReLU          receptive field 15 h
        [global mean pool || global max pool]  -> 64
        Dense(64->9) - sigmoid  (one output per modality)
    Loss: binary cross-entropy. Optimiser: Adam. All gradients are hand-derived.

The production path is to port this to PyTorch and add an LSTM or Temporal
Fusion Transformer forecaster (see the report's roadmap).
"""
import numpy as np


class Conv1D:
    def __init__(self, cin, cout, k, d, rng):
        self.k, self.d = k, d
        self.W = rng.normal(0, np.sqrt(2.0 / (cin * k)), (cout, cin * k)).astype(np.float32)
        self.b = np.zeros(cout, dtype=np.float32)

    def forward(self, x):
        N, C, T = x.shape
        To = T - self.d * (self.k - 1)
        cols = np.stack([x[:, :, self.d * j: self.d * j + To] for j in range(self.k)], axis=-1)  # N,C,To,K
        cols = cols.transpose(0, 2, 1, 3).reshape(N * To, C * self.k)
        self.cache = (x.shape, cols, To)
        out = cols @ self.W.T + self.b
        return out.reshape(N, To, -1).transpose(0, 2, 1)

    def backward(self, g):
        (N, C, T), cols, To = self.cache
        g2 = g.transpose(0, 2, 1).reshape(N * To, -1)
        self.dW = g2.T @ cols
        self.db = g2.sum(0)
        dcols = (g2 @ self.W).reshape(N, To, C, self.k)
        dx = np.zeros((N, C, T), dtype=np.float32)
        for j in range(self.k):
            dx[:, :, self.d * j: self.d * j + To] += dcols[:, :, :, j].transpose(0, 2, 1)
        return dx

    def params(self):
        return [("W", self.W, "dW"), ("b", self.b, "db")]


class Dense:
    def __init__(self, cin, cout, rng):
        self.W = rng.normal(0, np.sqrt(1.0 / cin), (cin, cout)).astype(np.float32)
        self.b = np.zeros(cout, dtype=np.float32)

    def forward(self, x):
        self.x = x
        return x @ self.W + self.b

    def backward(self, g):
        self.dW = self.x.T @ g
        self.db = g.sum(0)
        return g @ self.W.T

    def params(self):
        return [("W", self.W, "dW"), ("b", self.b, "db")]


def _sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


class TemporalCNN:
    def __init__(self, n_ch, n_out, width=32, seed=0):
        rng = np.random.default_rng(seed)
        self.convs = [Conv1D(n_ch, width, 3, 1, rng), Conv1D(width, width, 3, 2, rng), Conv1D(width, width, 3, 4, rng)]
        self.head = Dense(2 * width, n_out, rng)
        self.layers = self.convs + [self.head]
        self.mu = None
        self.history = []

    # --- forward/backward -------------------------------------------------
    def _forward(self, x):
        self.relu_masks = []
        h = x
        for c in self.convs:
            h = c.forward(h)
            m = h > 0
            self.relu_masks.append(m)
            h = h * m
        self.h_last = h
        mean = h.mean(2)
        self.amax = h.argmax(2)
        mx = h.max(2)
        z = np.concatenate([mean, mx], 1)
        return self.head.forward(z)

    def _backward(self, glogits):
        gz = self.head.backward(glogits)
        N, F, T = self.h_last.shape
        gmean, gmax = gz[:, :F], gz[:, F:]
        gh = np.repeat(gmean[:, :, None] / T, T, axis=2).astype(np.float32)
        n_idx, f_idx = np.meshgrid(np.arange(N), np.arange(F), indexing="ij")
        gh[n_idx, f_idx, self.amax] += gmax
        for c, m in zip(reversed(self.convs), reversed(self.relu_masks)):
            gh = c.backward(gh * m)

    # --- public API -----------------------------------------------------
    def _norm(self, X):
        return ((X - self.mu) / self.sd).astype(np.float32)

    def fit(self, X, Y, epochs=25, lr=3e-3, batch=128, seed=0, X_val=None, Y_val=None, verbose=True):
        rng = np.random.default_rng(seed)
        self.mu = X.mean(axis=(0, 2), keepdims=True)
        self.sd = X.std(axis=(0, 2), keepdims=True) + 1e-6
        Xn = self._norm(X)
        state = {}
        b1, b2, eps, step = 0.9, 0.999, 1e-8, 0
        pos = Y.mean(0).clip(0.05, 0.95)
        w_pos = (1 - pos) / pos                      # class-balance weight per label
        for ep in range(epochs):
            idx = rng.permutation(len(Xn))
            tot = 0.0
            for s in range(0, len(idx), batch):
                bi = idx[s:s + batch]
                xb, yb = Xn[bi], Y[bi]
                logits = self._forward(xb)
                p = _sigmoid(logits)
                w = np.where(yb > 0, w_pos, 1.0)
                tot += float(-(w * (yb * np.log(p + 1e-7) + (1 - yb) * np.log(1 - p + 1e-7))).mean()) * len(bi)
                g = (w * (p - yb) / len(bi)).astype(np.float32)
                self._backward(g)
                step += 1
                lr_t = lr * (0.5 * (1 + np.cos(np.pi * ep / epochs)))      # cosine decay
                for li, L in enumerate(self.layers):
                    for name, P, gname in L.params():
                        G = getattr(L, gname) + (1e-4 * P if name == "W" else 0)
                        key = (li, name)
                        m, v = state.get(key, (np.zeros_like(P), np.zeros_like(P)))
                        m = b1 * m + (1 - b1) * G
                        v = b2 * v + (1 - b2) * G * G
                        state[key] = (m, v)
                        P -= lr_t * (m / (1 - b1 ** step)) / (np.sqrt(v / (1 - b2 ** step)) + eps)
            rec = {"epoch": ep + 1, "train_loss": tot / len(idx)}
            if X_val is not None:
                pv = self.predict_proba(X_val)
                rec["val_loss"] = float(-(Y_val * np.log(pv + 1e-7) + (1 - Y_val) * np.log(1 - pv + 1e-7)).mean())
            self.history.append(rec)
            if verbose and (ep + 1) % 5 == 0:
                print(f"    TCN epoch {ep+1:>2}: train {rec['train_loss']:.4f}" +
                      (f"  val {rec['val_loss']:.4f}" if 'val_loss' in rec else ""))
        return self

    def predict_proba(self, X, batch=1024):
        out = []
        for s in range(0, len(X), batch):
            out.append(_sigmoid(self._forward(self._norm(X[s:s + batch]))))
        return np.concatenate(out)

    def n_params(self):
        return int(sum(P.size for L in self.layers for _, P, _ in L.params()))
