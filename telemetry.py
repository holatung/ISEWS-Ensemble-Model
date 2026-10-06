"""
Network-telemetry simulator.

Live feeds (Cloudflare Radar, IODA, OONI, NetBlocks) are not called in this
prototype. Instead, each interference modality is written as a *signature*:
a set of channel effects taken from the documented cases in data.py. For example,
the Iran June 2025 signature has BGP intact, traffic down about 97%, QUIC/UDP gone and
DNS poisoned. The simulator layers these signatures on a realistic baseline
(diurnal cycle plus noise). It is used to train the deep-learning models and to replay
scenarios. Every series it produces is SIMULATED.
"""
import numpy as np
from .data import MODALITY_KEYS

CHANNELS = [
    ("traffic",    "Traffic volume",                 "Cloudflare Radar (per-ASN)"),
    ("bgp",        "BGP-visible prefixes",           "IODA / RouteViews"),
    ("probe",      "Active-probe response",          "IODA"),
    ("darknet",    "Darknet (telescope) sources",    "IODA"),
    ("latency",    "Latency (relative)",             "RIPE Atlas / M-Lab"),
    ("throughput", "Throughput (relative)",          "M-Lab NDT"),
    ("dns_anom",   "DNS anomaly rate",               "OONI"),
    ("tls_reset",  "TLS/SNI and HTTP reset rate",    "OONI"),
    ("tcp_fail",   "TCP/IP connect-failure rate",    "OONI"),
    ("quic",       "QUIC/UDP share of traffic",      "Cloudflare Radar"),
    ("vpn",        "VPN handshake success",          "Circumvention-tool telemetry"),
    ("plat_reach", "Social-platform reachability",   "OONI (web connectivity)"),
    ("plat_tput",  "Social-platform throughput",     "M-Lab / client probes"),
    ("tls_mitm",   "Certificate-mismatch rate",      "OONI / TLS fingerprinting"),
]
CH = {c[0]: i for i, c in enumerate(CHANNELS)}
N_CH = len(CHANNELS)

BASE = dict(traffic=1.0, bgp=1.0, probe=1.0, darknet=1.0, latency=1.0, throughput=1.0,
            dns_anom=0.02, tls_reset=0.02, tcp_fail=0.02, quic=0.30, vpn=0.95,
            plat_reach=0.97, plat_tput=1.0, tls_mitm=0.005)


def baseline(T, rng, phase=None):
    """T hours of normal telemetry. Returns (T, N_CH)."""
    phase = rng.uniform(0, 24) if phase is None else phase
    t = np.arange(T) + phase
    diurnal = np.sin(2 * np.pi * (t - 8) / 24)
    X = np.zeros((T, N_CH))
    X[:, CH["traffic"]] = 1.0 + 0.30 * diurnal
    X[:, CH["darknet"]] = 1.0 + 0.10 * diurnal
    X[:, CH["latency"]] = 1.0 + 0.08 * diurnal
    X[:, CH["throughput"]] = 1.0 - 0.10 * diurnal
    for k in ["bgp", "probe", "dns_anom", "tls_reset", "tcp_fail", "quic", "vpn", "plat_reach", "plat_tput", "tls_mitm"]:
        X[:, CH[k]] = BASE[k]
    noise = rng.normal(0, 1, (T, N_CH))
    scale = np.array([0.04, 0.005, 0.02, 0.06, 0.05, 0.05, 0.008, 0.008, 0.008, 0.02, 0.02, 0.01, 0.05, 0.002])
    X += noise * scale
    return X


def apply(X, key, a, t_idx=None, bgp_withdrawal=False):
    """Apply modality `key` with intensity vector a (T,) in [0,1]."""
    c = CH
    if key == "full_shutdown":
        for k, f in [("traffic", .97), ("probe", .95), ("darknet", .80), ("throughput", .90),
                     ("plat_reach", .90), ("vpn", .90), ("plat_tput", .90)]:
            X[:, c[k]] *= (1 - f * a)
        X[:, c["bgp"]] *= (1 - (0.90 if bgp_withdrawal else 0.03) * a)
        X[:, c["latency"]] += 0.6 * a
    elif key == "platform_block":
        X[:, c["plat_reach"]] *= (1 - 0.85 * a)
        X[:, c["tls_reset"]] += 0.35 * a
        X[:, c["dns_anom"]] += 0.15 * a
        X[:, c["traffic"]] *= (1 - 0.06 * a)
    elif key == "ip_blocking":
        X[:, c["tcp_fail"]] += 0.40 * a
        X[:, c["plat_reach"]] *= (1 - 0.30 * a)
        X[:, c["vpn"]] *= (1 - 0.20 * a)
    elif key == "dns_http_censorship":
        X[:, c["dns_anom"]] += 0.50 * a
        X[:, c["tls_reset"]] += 0.30 * a
    elif key == "vpn_targeting":
        X[:, c["vpn"]] *= (1 - 0.80 * a)
        X[:, c["tcp_fail"]] += 0.12 * a
    elif key == "throttling":
        T = X.shape[0]
        tt = np.arange(T) if t_idx is None else t_idx
        rhythm = 1.5 + 0.8 * np.sin(2 * np.pi * tt / 3.0)       # "rhythmic instability"
        X[:, c["throughput"]] *= (1 - 0.70 * a)
        X[:, c["latency"]] *= (1 + rhythm * a)
        X[:, c["traffic"]] *= (1 - 0.30 * a)
        X[:, c["plat_tput"]] *= (1 - 0.50 * a)
    elif key == "protocol_downgrade":
        X[:, c["quic"]] *= (1 - 0.95 * a)
        X[:, c["vpn"]] *= (1 - 0.35 * a)
    elif key == "targeted_slowdown":
        X[:, c["plat_tput"]] *= (1 - 0.80 * a)
    elif key == "tls_interception":
        X[:, c["tls_mitm"]] += 0.25 * a
    elif key == "_benign_outage":       # power cut / cable fault: correlated drop, no censorship signals
        for k, f in [("traffic", .35), ("probe", .35), ("bgp", .25), ("darknet", .30), ("throughput", .25),
                     ("plat_reach", .30), ("vpn", .30)]:
            X[:, c[k]] *= (1 - f * a)
        X[:, c["latency"]] += 0.3 * a
    return X


def ramp(T, start, end, amax, rise=2.0):
    """Intensity profile: 0 before start, ramps to amax over `rise` h, holds, drops after end."""
    t = np.arange(T, dtype=float)
    up = np.clip((t - start + 1) / max(rise, 1e-6), 0, 1)
    down = np.clip((end - t) / 1.0, 0, 1) if end is not None else 1.0
    return amax * up * down


# ---------------------------------------------------------------------------
# Training-window generator (for the deep models)
# ---------------------------------------------------------------------------
CO_OCCUR = [  # documented combinations, drawn more often than random combos
    ["full_shutdown", "protocol_downgrade", "dns_http_censorship", "vpn_targeting"],   # Iran 2025 whitelisting
    ["throttling", "targeted_slowdown"],                                                # Kenya 2024 / Togo 2025
    ["platform_block", "dns_http_censorship", "ip_blocking"],                           # Togo 2025
    ["platform_block", "vpn_targeting"],                                                # Pakistan 2024, Nigeria 2021
    ["targeted_slowdown", "vpn_targeting"],                                             # Russia 2024-26
    ["full_shutdown", "platform_block"],                                                # Tanzania 2025, Bangladesh 2024
]


def make_windows(n, T=24, seed=0, p_normal=0.35, p_benign=0.08):
    rng = np.random.default_rng(seed)
    K = len(MODALITY_KEYS)
    Xs = np.zeros((n, N_CH, T), dtype=np.float32)
    Y = np.zeros((n, K), dtype=np.float32)
    kind = np.empty(n, dtype=object)
    for i in range(n):
        X = baseline(T, rng)
        r = rng.random()
        if r < p_normal:
            kind[i] = "normal"
        elif r < p_normal + p_benign:
            s = rng.integers(0, T - 6)
            X = apply(X, "_benign_outage", ramp(T, s, None, rng.uniform(0.3, 1.0), rng.uniform(1, 3)))
            kind[i] = "benign"
        else:
            if rng.random() < 0.45:
                keys = list(CO_OCCUR[rng.integers(len(CO_OCCUR))])
                keys = [k for k in keys if rng.random() > 0.15] or keys[:1]
            else:
                m = rng.choice([1, 1, 1, 2, 2, 3])
                keys = list(rng.choice(MODALITY_KEYS, size=m, replace=False))
            bgp_w = rng.random() < 0.4
            for k in keys:
                s = rng.integers(-6, T - 6)
                amax = rng.uniform(0.45, 1.0)
                X = apply(X, k, ramp(T, s, None, amax, rng.uniform(1, 4)), t_idx=np.arange(T) + rng.integers(0, 3),
                          bgp_withdrawal=bgp_w)
                Y[i, MODALITY_KEYS.index(k)] = 1.0 if amax >= 0.5 else 0.0
            kind[i] = "event"
        Xs[i] = X.T
    return Xs, Y, kind


# ---------------------------------------------------------------------------
# Scenario replay (168 h). All SIMULATED, modelled on the cited cases.
# ---------------------------------------------------------------------------
def scenario_series(sc, seed=0, T=168):
    rng = np.random.default_rng(seed)
    X = baseline(T, rng, phase=0.0)
    for m in sc.get("schedule", []):
        key, s, e, amax = m["key"], m["start"], m.get("end"), m.get("amax", 0.95)
        X = apply(X, key, ramp(T, s, e, amax, m.get("rise", 2.0)), t_idx=np.arange(T),
                  bgp_withdrawal=m.get("bgp_withdrawal", False))
    t = np.arange(T, dtype=float)
    E = np.interp(t, [p[0] for p in sc["escalation"]], [p[1] for p in sc["escalation"]])
    return X, E
