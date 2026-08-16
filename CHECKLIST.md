# Remaining work before the presentation

Presentation: **Thursday 20 August, 6:00 PM ET.** Status as of Sunday 16 August.

The model, report, deck, notebook and demo are done and verified. What is left is
rehearsal and two recordings.

## Final numbers

Run `transformer_h1`, seed 42, early stop at epoch 19 (best epoch 11):
**MAE 0.3062 / RMSE 0.4494 / R² 0.589 / 21.8% RMSE reduction vs. persistence**,
on 5,165 held-out hourly predictions.

    python -m src.train --run-name transformer_h1
    python -m src.evaluate --run-name transformer_h1
    python -m src.ablation --group all --epochs 40

The report, deck and notebook are **generated**. Edit `scripts/build_report.js`,
`scripts/build_deck.js` or `scripts/build_notebook.py` and run `npm run build`
(plus `python scripts/build_notebook.py`). Never hand-edit the .docx/.pptx/.ipynb.

## Speaking parts — assigned

| Who | Slides | Window | Owns |
|---|---|---|---|
| **William** | 1–3 | 0:00–3:15 | Intro, the problem, data preparation |
| **Ciara** | 4–7 | 3:15–8:15 | Proposed solution, tools, architecture, training |
| **Chris** | 8–14 | 8:15–15:00 | Evaluation, results, demo, ablations, limitations |

Every slide's notes now carry the speaker's name and time window. In Q&A whoever
owns the slide takes the question; Chris backstops anything methodological.

William's one thing to rehearse cold is the split-and-scaling box on slide 3 —
that is where a grader probes.

## Demo — slider origins are chosen

Do **not** hunt for examples live. Both origins are verified against
`results/transformer_h1_predictions.csv`:

| Purpose | Slider index | Timestamp | Actual | Predicted |
|---|---|---|---|---|
| Calm overnight | **2556** | 10 Aug 2010, 05:00 | 0.314 kW | 0.314 kW (error 0.0002) |
| Evening peak | **5017** | 20 Nov 2010, 18:00 | 5.627 kW | 2.294 kW (short by 3.33) |

Index 5017 is the single largest peak in the test set — the same 5.63 kW maximum
quoted on slide 10 and in the report, so you can point at it and tie the demo
straight back to the results. If that miss feels too brutal to open with, index
**3843** (2 Oct 2010, 20:00) is 3.94 vs 1.94.

Have the app already running before the talk starts; never launch it live.

    streamlit run demo/app.py

## Timing — you are at exactly 15:00 with no buffer

The notes sum to 15:00 against a 15-minute hard cap. The demo always overruns.
Two safe cuts if you are behind at slide 11:

- Skip the Performance-tab detour in the demo (already marked optional) — ~30 s
- Compress slide 5 (Tools) to a single sentence — ~15 s

## Still to do

- [ ] **Record the 60-second demo fallback video.** If the live demo fails,
      this is what saves the three rubric points.
- [ ] **Timed full run-through**, ideally Tuesday so Wednesday stays free as
      buffer. Time each speaker separately against the table above.
- [ ] **Eyeball the two PDFs.** They were exported with LibreOffice rather than
      Office; fonts resolved correctly (Calibri/Cambria, no substitution) and
      page counts are right (report 14, deck 15), but give them a scroll.

## Done

- [x] Final training run, evaluation, and full ablation grid.
- [x] Report, deck, notebook and README all carrying the final numbers.
- [x] Repo public, history clean, everything pushed.
- [x] PDF exports — `report/final_report.pdf`, `presentation/MSML612_final_presentation.pdf`.
- [x] Notebook generator fixed (cells were fusing into one line and would not run).
- [x] Slide 10 figure overlap fixed.
- [x] Demo no longer substitutes the superseded interim run silently, labels the
      comparison row from the run's own model type, and draws the horizon=1
      forecast visibly.

## Known limitations to own, not hide

If a grader probes, these are true and worth answering straight:

- The mean-predictor baseline uses the test-period mean, so its R² is 0.000 by
  construction; the report describes it as the training mean.
- Baselines are scored on slightly fewer samples than the model (persistence
  5,164 and seasonal naive 5,141 against 5,165) because each drops its first
  lag hours.
- Gap imputation runs within each split but interpolates in both directions, so
  a gap can be filled partly from later hours in the same split.
