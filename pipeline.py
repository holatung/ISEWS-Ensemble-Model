"""
ISEWS pipeline: train -> evaluate -> score scenarios -> results dict for the report.

Machine learning (scikit-learn)
  * Structural shutdown-risk models on the country-month panel:
      Logistic Regression (L2, standardised)    interpretable baseline
      Random Forest (300 trees)                 non-linear interactions
      Histogram Gradient Boosting               production structural model
  * Isolation Forest on window summary features: unsupervised anomaly baseline
  * Gradient Boosting on engineered window features: modality classification baseline

Deep learning
  * Temporal CNN (dilated, NumPy): multi-label modality classifier on raw 24-h, 14-channel telemetry
  * Deep autoencoder (MLP 336-128-32-128-336, scikit-learn): trained only on normal
    traffic; reconstruction error is the anomaly score for new or unseen tactics

Fusion
  ISEWS score = 100 * [1 - (1 - 0.35 S)(1 - 0.55 E)(1 - 0.80 D)]
    S = structural 30-day risk, E = trigger escalation (event feed), D = detection strength
    D = max( max_k p_k * severity_k , 0.6 * A ), where A rises from 0 at the autoencoder's 99th-percentile
    normal error to 1 at three times that error
    S = equal-weight mean of the three structural models
"""
import time
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier, IsolationForest
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss, f1_score
from sklearn.inspection import permutation_importance

from .data import MODALITIES, MODALITY_KEYS
from .panel import build_panel, FEATURES, FEATURE_LABELS
from .telemetry import make_windows, scenario_series, N_CH, CHANNELS
from .nn import TemporalCNN
from .scenarios import SCENARIOS

SEV = np.array([m[2] for m in MODALITIES])
TIERS = [(75, "Critical"), (50, "Warning"), (25, "Watch"), (0, "Low")]


def tier(score):
    return next(name for th, name in TIERS if score >= th)


def window_features(X):
    """Engineered features for the ML baselines. X: (N, C, T)."""
    first, last = X[:, :, :12].mean(2), X[:, :, -6:].mean(2)
    return np.concatenate([last, first, last - first, X.min(2), X.max(2), X.std(2)], 1)


def run(seed=42, n_train=9000, n_test=3000, epochs=25, verbose=True):
    t0 = time.time()
    R = {"meta": {"seed": seed}}
    log = (lambda *a: print(*a)) if verbose else (lambda *a: None)

    # ---------------------------------------------------------------- structural ML
    log("[1/5] Structural panel + ML models")
    panel = build_panel(seed=seed)
    tr, te = panel[panel.year <= 2022], panel[panel.year >= 2023]
    Xtr, ytr, Xte, yte = tr[FEATURES].values, tr.shutdown.values, te[FEATURES].values, te.shutdown.values
    models = {
        "Logistic Regression": make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=2000)),
        "Random Forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=seed, n_jobs=-1),
        "Gradient Boosting": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                                            l2_regularization=1.0, random_state=seed),
    }
    struct = []
    for name, m in models.items():
        m.fit(Xtr, ytr)
        p = m.predict_proba(Xte)[:, 1]
        struct.append(dict(model=name, auc=roc_auc_score(yte, p), ap=average_precision_score(yte, p),
                           brier=brier_score_loss(yte, p), base_rate=float(yte.mean())))
        log(f"    {name:<20} AUC {struct[-1]['auc']:.3f}  PR-AUC {struct[-1]['ap']:.3f}  Brier {struct[-1]['brier']:.4f}")
    gbm = models["Gradient Boosting"]
    pi = permutation_importance(gbm, Xte, yte, scoring="roc_auc", n_repeats=8, random_state=seed)
    R["structural"] = dict(results=struct, n_train=len(tr), n_test=len(te), n_countries=panel.country.nunique(),
                           pos_rate=float(panel.shutdown.mean()),
                           importance=sorted([(FEATURE_LABELS[f], float(v)) for f, v in zip(FEATURES, pi.importances_mean)],
                                             key=lambda x: -x[1]),
                           yearly=panel.groupby("year").shutdown.sum().to_dict())

    # ---------------------------------------------------------------- telemetry data
    log("[2/5] Simulated telemetry windows")
    Xw, Yw, kind = make_windows(n_train, seed=seed)
    Xv, Yv, kv = make_windows(n_test, seed=seed + 1)
    R["telemetry"] = dict(n_train=n_train, n_test=n_test, channels=[c[1] for c in CHANNELS], sources=[c[2] for c in CHANNELS],
                          label_rate={k: float(Yw[:, i].mean()) for i, k in enumerate(MODALITY_KEYS)})

    # ---------------------------------------------------------------- DL: TCN
    log("[3/5] Temporal CNN (deep learning)")
    tcn = TemporalCNN(N_CH, len(MODALITY_KEYS), width=32, seed=seed)
    tcn.fit(Xw, Yw, epochs=epochs, X_val=Xv, Y_val=Yv, verbose=verbose)
    Pt = tcn.predict_proba(Xv)

    # ---------------------------------------------------------------- ML baseline for modalities
    Fw, Fv = window_features(Xw), window_features(Xv)
    Pg = np.zeros_like(Pt)
    for i in range(len(MODALITY_KEYS)):
        clf = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.08, random_state=seed)
        clf.fit(Fw, Yw[:, i])
        Pg[:, i] = clf.predict_proba(Fv)[:, 1]
    per = []
    for i, (k, lab, sev, *_r) in enumerate(MODALITIES):
        per.append(dict(key=k, label=lab, severity=sev, support=int(Yv[:, i].sum()),
                        tcn_auc=roc_auc_score(Yv[:, i], Pt[:, i]), tcn_f1=f1_score(Yv[:, i], Pt[:, i] > .5),
                        gbm_auc=roc_auc_score(Yv[:, i], Pg[:, i]), gbm_f1=f1_score(Yv[:, i], Pg[:, i] > .5)))
    R["modality"] = dict(per_label=per, tcn_params=tcn.n_params(), history=tcn.history,
                         tcn_macro_f1=float(np.mean([p["tcn_f1"] for p in per])),
                         gbm_macro_f1=float(np.mean([p["gbm_f1"] for p in per])),
                         tcn_macro_auc=float(np.mean([p["tcn_auc"] for p in per])),
                         gbm_macro_auc=float(np.mean([p["gbm_auc"] for p in per])))
    log(f"    TCN macro-F1 {R['modality']['tcn_macro_f1']:.3f}  vs GBM baseline {R['modality']['gbm_macro_f1']:.3f}")

    # ---------------------------------------------------------------- anomaly detectors
    log("[4/5] Autoencoder + Isolation Forest")
    flat = lambda X: ((X - tcn.mu) / tcn.sd).reshape(len(X), -1)
    normal_tr = flat(Xw[kind == "normal"])
    ae = MLPRegressor(hidden_layer_sizes=(128, 32, 128), activation="relu", max_iter=80, learning_rate_init=1e-3,
                      early_stopping=True, random_state=seed)
    ae.fit(normal_tr, normal_tr)
    err = lambda X: ((ae.predict(flat(X)) - flat(X)) ** 2).mean(1)
    e_v = err(Xv)
    normal_ref = np.sort(e_v[kv == "normal"])
    thr99 = float(np.quantile(normal_ref, 0.99))
    iso = IsolationForest(n_estimators=300, contamination="auto", random_state=seed).fit(Fw[kind == "normal"])
    s_iso = -iso.score_samples(Fv)
    thr_iso = float(np.quantile(s_iso[kv == "normal"], 0.99))
    ev_mask = (kv == "event") & (Yv.sum(1) > 0)
    R["anomaly"] = dict(
        ae_detect=float((e_v[ev_mask] > thr99).mean()), ae_far=float((e_v[kv == "normal"] > thr99).mean()),
        ae_benign=float((e_v[kv == "benign"] > thr99).mean()),
        iso_detect=float((s_iso[ev_mask] > thr_iso).mean()), iso_far=float((s_iso[kv == "normal"] > thr_iso).mean()),
        iso_benign=float((s_iso[kv == "benign"] > thr_iso).mean()),
        ae_auc=roc_auc_score(ev_mask[(kv != "benign")], e_v[(kv != "benign")]),
        iso_auc=roc_auc_score(ev_mask[(kv != "benign")], s_iso[(kv != "benign")]),
        ae_layers="336-128-32-128-336", n_normal=int((kind == "normal").sum()))
    a = R["anomaly"]
    log(f"    AE detect {a['ae_detect']:.2%} @ FAR {a['ae_far']:.2%} | IsoForest detect {a['iso_detect']:.2%}")

    # ---------------------------------------------------------------- scenarios
    log("[5/5] Scoring scenarios")
    out = []
    for i, sc in enumerate(SCENARIOS):
        X, E = scenario_series(sc, seed=seed + 100 + i)
        xs = np.array([[sc["structural"][f] for f in FEATURES]])
        S_each = {n: float(m.predict_proba(xs)[0, 1]) for n, m in models.items()}
        S = float(np.mean(list(S_each.values())))          # equal-weight ensemble of the three ML models
        T = X.shape[0]
        W = np.stack([X[t - 24:t].T for t in range(24, T + 1)]).astype(np.float32)   # windows ending at t-1
        P = tcn.predict_proba(W)
        A = np.clip((err(W) / thr99 - 1.0) / 2.0, 0, 1)     # 0 below the 99th pct of normal; 1 at 3x that error
        M = (P * SEV).max(1)
        D = np.maximum(M, 0.6 * A)
        Et = E[23:]
        score = 100 * (1 - (1 - 0.35 * S) * (1 - 0.55 * Et) * (1 - 0.80 * D))
        hours = np.arange(23, T)
        onset = sc["onset"]
        lead = {}
        for th in (25, 50):
            idx = np.where(score >= th)[0]
            lead[th] = (int(onset - hours[idx[0]]) if (onset is not None and len(idx)) else None)
        last = P[-1]
        # debounce: a modality counts only after 3 consecutive hours with p >= 0.5
        on = P >= 0.5
        run3 = on[2:] & on[1:-1] & on[:-2]
        P3 = np.minimum(np.minimum(P[2:], P[1:-1]), P[:-2])
        Pmax = np.where(run3.any(0), P3.max(0), np.minimum(P.max(0), 0.49))
        detected = [dict(key=k, label=MODALITIES[j][1], p=float(Pmax[j]), active=bool(last[j] >= 0.5),
                         first_h=int(hours[2:][np.argmax(run3[:, j])]))
                    for j, k in enumerate(MODALITY_KEYS) if Pmax[j] >= 0.5]
        detected.sort(key=lambda d: d["first_h"])
        fs = MODALITY_KEYS.index("full_shutdown")
        mech = None
        if Pmax[fs] >= 0.5:
            hs = int(np.argmax(P[:, fs])) + 23
            bgp = X[max(hs - 5, 0):hs + 1, 1].mean()
            mech = "Routing withdrawal (BGP)" if bgp < 0.5 else "Middlebox / stealth (BGP still visible)"
            if sc.get("mech_note"):
                mech += " - " + sc["mech_note"]
        first_detect = min([d["first_h"] for d in detected], default=None)
        out.append(dict(key=sc["key"], country=sc["country"], title=sc["title"], basis=sc["basis"], onset=onset,
                        S=S, S_each=S_each, score=score.tolist(), hours=hours.tolist(), E=Et.tolist(), A=A.tolist(),
                        P_last=last.tolist(), P=P.tolist(), detected=detected, mechanism=mech,
                        final=float(score[-1]), peak=float(score.max()), tier=tier(float(score.max())), lead=lead,
                        first_detect=first_detect, P_max=Pmax.tolist(),
                        channels_last={CHANNELS[c][1]: float(X[-6:, c].mean()) for c in range(N_CH)}))
        log(f"    {sc['country']:<26} peak {score.max():5.1f} ({tier(score.max())})  S={S:.2f}  "
            f"lead@Warning={lead[50]}h  detected={[d['key'] for d in detected]}  mech={mech}")
    R["scenarios"] = out
    R["meta"]["runtime_s"] = round(time.time() - t0, 1)
    return R
