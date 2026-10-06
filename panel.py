"""
Structural (country-month) panel for the shutdown-risk models.

The event-level Access Now STOP dataset is shared on request, and it is not bundled here.
This module therefore builds a SIMULATED country-month panel for 2016-2025:
  * each country's latent propensity is anchored to its 2025 Access Now
    shutdown count where the report gives one (data.AGGREGATES)
  * drivers follow the ISEWS indicator set: regime type, elections,
    protests, armed conflict, national exams, gateway centralisation, mobile
    dependence and recent shutdown history
  * labels come from a known logistic process, so models can be benchmarked
To use real data, pass a STOP-style CSV to `load_events_csv` and join the result on
(iso, year, month). The modelling code needs no other change.
"""
import numpy as np
import pandas as pd

# name, iso, region, regime (0 liberal dem, 1 electoral dem, 2 electoral autocracy, 3 closed autocracy),
# baseline conflict (0-1), exam-shutdown country, gateway centralised (0/1), 2025 Access Now count (None = not listed)
# Regime and conflict codes are APPROXIMATE analyst codes (V-Dem RoW-style); replace with V-Dem v15 / ACLED.
COUNTRIES = [
    ("Myanmar", "MMR", "Asia-Pacific", 3, .90, 0, 1, 95), ("India", "IND", "Asia-Pacific", 2, .30, 1, 0, 65),
    ("Pakistan", "PAK", "Asia-Pacific", 2, .50, 0, 1, 20), ("Russia", "RUS", "Europe-C.Asia", 3, .70, 0, 1, 19),
    ("Iran", "IRN", "MENA", 3, .45, 0, 1, 11), ("Tanzania", "TZA", "Africa", 2, .10, 0, 1, 8),
    ("Cameroon", "CMR", "Africa", 2, .50, 0, 1, 4), ("Kenya", "KEN", "Africa", 1, .20, 1, 0, 3),
    ("Sudan", "SDN", "Africa", 3, .95, 1, 1, 3), ("Nigeria", "NGA", "Africa", 2, .50, 0, 0, 2),
    ("Ethiopia", "ETH", "Africa", 2, .75, 1, 1, 2), ("Guinea", "GIN", "Africa", 3, .20, 0, 1, 2),
    ("DR Congo", "COD", "Africa", 2, .80, 0, 0, 2), ("Angola", "AGO", "Africa", 2, .10, 0, 1, 1),
    ("Central African Republic", "CAF", "Africa", 2, .70, 0, 1, 1), ("Chad", "TCD", "Africa", 3, .50, 0, 1, 1),
    ("Equatorial Guinea", "GNQ", "Africa", 3, .05, 0, 1, 1), ("Guinea-Bissau", "GNB", "Africa", 2, .10, 0, 1, 1),
    ("Libya", "LBY", "MENA", 3, .60, 0, 1, 1), ("Togo", "TGO", "Africa", 2, .20, 0, 1, 1),
    ("Syria", "SYR", "MENA", 3, .85, 1, 1, None), ("Yemen", "YEM", "MENA", 3, .90, 0, 1, None),
    ("Iraq", "IRQ", "MENA", 2, .50, 1, 1, None), ("Algeria", "DZA", "MENA", 2, .10, 1, 1, None),
    ("Jordan", "JOR", "MENA", 3, .10, 1, 0, None), ("Bangladesh", "BGD", "Asia-Pacific", 2, .30, 0, 1, None),
    ("Venezuela", "VEN", "Americas", 2, .20, 0, 1, None), ("Cuba", "CUB", "Americas", 3, .00, 0, 1, None),
    ("Turkey", "TUR", "Europe-C.Asia", 2, .25, 0, 0, None), ("Azerbaijan", "AZE", "Europe-C.Asia", 2, .30, 1, 1, None),
    ("Kazakhstan", "KAZ", "Europe-C.Asia", 2, .10, 0, 1, None), ("Uganda", "UGA", "Africa", 2, .20, 0, 0, None),
    ("Zimbabwe", "ZWE", "Africa", 2, .10, 0, 1, None), ("Senegal", "SEN", "Africa", 1, .10, 0, 0, None),
    ("Gabon", "GAB", "Africa", 3, .05, 0, 1, None), ("Mali", "MLI", "Africa", 3, .65, 0, 1, None),
    ("Burkina Faso", "BFA", "Africa", 3, .70, 0, 1, None), ("Mozambique", "MOZ", "Africa", 2, .40, 0, 0, None),
    ("Somalia", "SOM", "Africa", 3, .80, 0, 0, None), ("Egypt", "EGY", "MENA", 2, .20, 0, 1, None),
    ("Rwanda", "RWA", "Africa", 2, .10, 0, 1, None), ("Ghana", "GHA", "Africa", 1, .05, 0, 0, None),
    ("South Africa", "ZAF", "Africa", 1, .05, 0, 0, None), ("Brazil", "BRA", "Americas", 1, .05, 0, 0, None),
    ("Indonesia", "IDN", "Asia-Pacific", 1, .15, 0, 0, None), ("Philippines", "PHL", "Asia-Pacific", 1, .25, 0, 0, None),
    ("Germany", "DEU", "Europe-C.Asia", 0, .00, 0, 0, None), ("United Kingdom", "GBR", "Europe-C.Asia", 0, .00, 0, 0, None),
    ("United States", "USA", "Americas", 0, .00, 0, 0, None), ("Tunisia", "TUN", "MENA", 2, .05, 0, 1, None),
]

INTERCEPT = -5.6   # calibrated: roughly 100 shutdown country-months a year across 50 countries

FEATURES = ["regime", "conflict", "election_window", "protest", "exam_month", "gateway_centralised",
            "mobile_share", "prior_12m", "months_since_last", "year_trend"]
FEATURE_LABELS = {
    "regime": "Regime type (closed autocracy high)", "conflict": "Armed-conflict intensity",
    "election_window": "Election within the next 3 months", "protest": "Protest intensity",
    "exam_month": "National exam month", "gateway_centralised": "Centralised international gateway",
    "mobile_share": "Mobile share of traffic", "prior_12m": "Shutdown months in the past 12",
    "months_since_last": "Months since last shutdown", "year_trend": "Year (secular trend)",
}


def build_panel(seed=7, years=range(2016, 2026)):
    rng = np.random.default_rng(seed)
    rows = []
    for name, iso, region, regime, conflict0, exam_c, gw, cnt in COUNTRIES:
        # latent propensity: anchored on the 2025 count when the report lists one
        latent = (1.0 * np.log1p(cnt) - 1.2) if cnt else (-1.6 + 0.45 * regime + rng.normal(0, 0.4))
        el_month = rng.integers(0, 60)              # elections roughly every 5 years
        protest = 0.0
        conf = conflict0
        mobile = np.clip(rng.normal(0.65 if region == "Africa" else 0.5, 0.1), 0.2, 0.95)
        hist = []
        for yi, y in enumerate(years):
            for m in range(1, 13):
                k = yi * 12 + (m - 1)
                election_window = int(((k - el_month) % 60) in (57, 58, 59, 0))
                protest = 0.75 * protest + 0.25 * rng.random() * (1 + regime / 3) + \
                    (0.6 if rng.random() < 0.04 + 0.25 * election_window else 0)
                protest = float(np.clip(protest, 0, 1))
                conf = float(np.clip(conf + rng.normal(0, 0.05) + (0.3 if rng.random() < 0.01 else 0) - 0.02 * (conf - conflict0), 0, 1))
                exam = int(exam_c and m in (6,) if iso != "KEN" else exam_c and m == 11)
                prior = sum(hist[-12:])
                since = next((i for i, v in enumerate(reversed(hist)) if v), 36) if hist else 36
                logit = (INTERCEPT + latent + 0.35 * regime + 1.6 * conf + 1.4 * election_window + 1.1 * protest
                         + 1.6 * exam + 0.5 * gw + 0.6 * (mobile - 0.5) + 0.10 * (y - 2016)
                         + 0.07 * prior + rng.normal(0, 0.35))
                yv = int(rng.random() < 1 / (1 + np.exp(-logit)))
                rows.append(dict(country=name, iso=iso, region=region, year=y, month=m,
                                 regime=regime, conflict=conf, election_window=election_window,
                                 protest=protest, exam_month=exam, gateway_centralised=gw,
                                 mobile_share=mobile, prior_12m=prior, months_since_last=min(since, 36),
                                 year_trend=y - 2016, shutdown=yv))
                hist.append(yv)
    return pd.DataFrame(rows)


def load_events_csv(path):
    """Load a real STOP-style CSV (columns: country, iso, start_date, end_date, shutdown_type, trigger)
    and return a (iso, year, month) label frame for joining onto the panel."""
    ev = pd.read_csv(path, parse_dates=["start_date"])
    ev["year"], ev["month"] = ev.start_date.dt.year, ev.start_date.dt.month
    return ev.groupby(["iso", "year", "month"]).size().clip(upper=1).rename("shutdown").reset_index()
