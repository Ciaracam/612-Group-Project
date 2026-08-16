# Remaining work before Wednesday 19 August

Everything not listed here is done. These four items need your machine and the raw
dataset, which is why they are not already complete.

## 1. Train the final model  (Monday — do this first, everything else waits on it)

    python -m src.train --run-name transformer_h1
    python -m src.evaluate --run-name transformer_h1

The training code adds early stopping, an LR schedule, and 7 calendar features
that the interim run did not have, so **the numbers will change** — very likely
for the better. Runtime is roughly 8-12 min on CPU.

## 2. Update the reported numbers

Every number currently in the report and deck comes from the verified interim run
(MAE 0.3208 / RMSE 0.4643 / R² 0.561 / 19.2% skill). After step 1, replace them in:

- `report/final_report.docx` — abstract, Table 3, Section 7 prose, conclusion
- `presentation/MSML612_final_presentation.pptx` — slides 7 and 9
- `README.md` — the results table

`src/evaluate.py` prints the full comparison table and writes
`results/transformer_h1_metrics.json`, so this is copy-paste, not recomputation.
Also swap in the regenerated `figures/transformer_h1_loss_curve.png`.

## 3. Run the ablations

    python -m src.ablation --group all --epochs 40

Paste `results/ablation_results.md` into Table 4 of the report and slide 12, then
write 1-2 sentences interpreting it. **If time is short, run `--group features`
and `--group architecture` first** — those two produce the most quotable
comparisons (calendar features on/off, and Transformer vs. LSTM control).

If the runs are not finished by Wednesday, delete slide 12 rather than presenting
a table of dashes.

## 4. Demo rehearsal

    streamlit run demo/app.py

- Have it already running before you present; do not launch it live.
- Show two forecasts: one calm overnight hour, one evening peak. Owning the peak
  weakness is stronger than hoping nobody notices it.
- Record a 60-second screen capture as a fallback.
- Time the full run-through. 15 minutes is a hard cap and the demo always runs long.

## Also worth doing

- [ ] Confirm the repo is public and push everything.
- [ ] Delete the four `ACTION REQUIRED` callouts in the report once addressed.
- [ ] Proofread pass by whoever did not write it.
- [ ] Export the report to PDF alongside the .docx.
- [ ] Assign speaking parts (suggested: intro+data / solution+architecture / results+demo).

## Speaker notes

Every slide has timed notes in the .pptx. Open the notes pane to see them —
they include anticipated questions and how to answer them on the final slide.
