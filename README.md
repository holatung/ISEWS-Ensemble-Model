# ISEWS prototype (Internet Shutdown Early Warning System)

ChatVE, Research, Development and Innovation. Prototype v0.1.

ISEWS scores the risk of internet interference and identifies which kind is under way. It covers full and regional
shutdowns, social media and app bans, IP/ASN blocking, DNS/HTTP censorship, VPN targeting, bandwidth throttling,
protocol downgrades and whitelisting, targeted platform slowdowns, and surveillance (TLS interception plus
policy indicators). Each run writes a self-contained HTML report.

## Run

```bash
pip install -r requirements.txt          # numpy, pandas, scikit-learn
python run_isews.py                      # about 30 s; writes output/isews_report.html and output/isews_results.json
python run_isews.py --fast               # smaller training sets, for testing
python run_isews.py --from-pickle output/isews_results.pkl   # re-render without retraining
```

## Architecture

| Layer | Model | Type | Input |
|---|---|---|---|
| 1. Structural risk | Logistic Regression, Random Forest, Histogram Gradient Boosting (ensemble mean = S) | ML | Country-month indicators: regime, conflict, election window, protests, exams, gateway centralisation, mobile share, shutdown history |
| 2. Modality detection | Dilated Temporal CNN, multi-label (NumPy, hand-derived gradients) | DL | 24 h × 14 telemetry channels |
| 2. Modality baseline | Gradient Boosting on 84 engineered window features | ML | Same windows |
| 2. Anomaly | Deep autoencoder 336-128-32-128-336 | DL | Normal traffic only |
| 2. Anomaly baseline | Isolation Forest | ML | Window features |
| 3. Fusion | score = 100 × [1 − (1 − 0.35·S)(1 − 0.55·E)(1 − 0.80·D)] | Rule | S, escalation E, detection D |

## Files

- `isews/data.py`: historical records (Access Now, Internet Society Pulse, Project Ainita, IODA and others) with provenance flags, the modality taxonomy and surveillance indicators
- `isews/panel.py`: the simulated country-month panel and the `load_events_csv()` hook for the real Access Now STOP dataset
- `isews/telemetry.py`: the channel definitions and signature-based telemetry simulator
- `isews/nn.py`: the NumPy temporal CNN
- `isews/scenarios.py`: nine replay scenarios modelled on documented cases
- `isews/pipeline.py`: training, evaluation and scoring
- `isews/report.py`: the HTML report

## What is real and what is simulated

- **Real:** event records, dates, mechanisms and global aggregates. Each one carries a status: VERIFIED, EXTRACTED (machine-extracted from a PDF, so spot-check it before citing), REPORTED, BRIEF (from the ChatVE Tigray brief) or CODED.
- **Simulated:** all telemetry, the training panel, escalation curves and every score and metric. These show how the system works and are not estimates of accuracy.

## Moving to production

1. Request the Access Now STOP dataset and load it with `panel.load_events_csv()`. Replace the approximate regime and conflict codes with V-Dem and ACLED data.
2. Replace `telemetry.scenario_series` with live per-ASN pulls from the Cloudflare Radar API, IODA signals, OONI measurements and M-Lab NDT.
3. Backtest against held-out shutdowns, then fit the fusion weights and calibrate them (isotonic regression).
4. Port `nn.TemporalCNN` to PyTorch, then add an LSTM or TFT forecaster and a multilingual NLP trigger extractor.
5. Keep human review before any alert at Warning or above is released.
