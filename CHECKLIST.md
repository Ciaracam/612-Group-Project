# Remaining work before Wednesday 19 August

Status as of Saturday 16 August. Items 1–3 are **done**; the numbers below are
from the final verified run. What remains is rehearsal and submission logistics.

## 1. Train the final model — DONE

    python -m src.train --run-name transformer_h1
    python -m src.evaluate --run-name transformer_h1

Final run (early stop at epoch 19, best epoch 11):
**MAE 0.3062 / RMSE 0.4494 / R² 0.589 / 21.8% RMSE reduction vs. persistence.**

Two things to know about these numbers:

- A leakage bug was fixed first: hourly gap interpolation ran *before* the
  chronological split, letting adjacent splits inform each other (the same
  defect PR #1 found in the notebook). The number is clean now.
- The Hyperopt configuration from PR #1 was retrained as a control
  (`transformer_h1_tuned`: MAE 0.3136 / RMSE 0.4604). It loses to the defaults
  here because it was tuned against the old pipeline without calendar features.

## 2. Update the reported numbers — DONE

README, report (abstract, Table 3, Section 7, discussion, conclusion), and deck
(slides 7 and 9) all rebuilt from the run above. Figure 2 is now the final run's
loss curve (`figures/transformer_h1_loss_curve.png`). The report and deck are
generated — edit `scripts/build_report.js` / `scripts/build_deck.js` and run
`npm run build`; never hand-edit the .docx/.pptx.

## 3. Run the ablations — DONE

    python -m src.ablation --group all --epochs 40

Results are in `results/ablation_results.md`, pasted into Table 4 and slide 12.

## 4. Demo rehearsal — still to do

    streamlit run demo/app.py

Verified working live (forecasts from the new checkpoint; Performance tab now
follows the selected run). For the presentation:

- Have it already running before you present; do not launch it live.
- Show two forecasts: one calm overnight hour, one evening peak. Owning the peak
  weakness is stronger than hoping nobody notices it.
- Record a 60-second screen capture as a fallback.
- Time the full run-through. 15 minutes is a hard cap and the demo always runs long.

## Also worth doing

- [x] Confirm the repo is public and push everything.
- [x] Delete the four `ACTION REQUIRED` callouts in the report once addressed.
- [ ] Proofread pass by whoever did not write it.
- [ ] Export the report AND deck to PDF on a machine with Office (the stale
      deck PDF was removed — this machine has no PowerPoint to re-export;
      open the rebuilt .pptx/.docx and Save As PDF after the final rebuild).
- [ ] Assign speaking parts (suggested: intro+data / solution+architecture / results+demo).

## Speaker notes

Every slide has timed notes in the .pptx. Open the notes pane to see them —
they include anticipated questions and how to answer them on the final slide.
