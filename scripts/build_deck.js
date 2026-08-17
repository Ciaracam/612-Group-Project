/**
 * Build presentation/MSML612_final_presentation.pptx
 *
 *   node scripts/build_deck.js
 */

const path = require("path");
const pptxgen = require("pptxgenjs");

const ROOT = path.resolve(__dirname, "..");
const FIG = path.join(ROOT, "figures");

const INK = "0F2B46";
const INK_SOFT = "1B3F60";
const AMBER = "E8871E";
const TEAL = "2A9D8F";
const PALE = "EEF3F7";
const GRAY = "6B7C8C";
const WHITE = "FFFFFF";

const HEAD = "Cambria";
const BODY = "Calibri";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5
pres.author = "Peng, Cameron, Pedretti";
pres.title = "Transformer-Based Electricity Consumption Forecasting";

const W = 13.3;
const M = 0.6; // margin

// ---------------------------------------------------------------- helpers

function titleOf(slide, text, sub) {
  slide.addText(text, {
    x: M, y: 0.38, w: W - 2 * M, h: 0.62,
    fontSize: 32, bold: true, color: INK, fontFace: HEAD, margin: 0,
  });
  if (sub) {
    slide.addText(sub, {
      x: M, y: 1.02, w: W - 2 * M, h: 0.36,
      fontSize: 14, color: GRAY, fontFace: BODY, margin: 0, italic: true,
    });
  }
}

function card(slide, { x, y, w, h, fill = PALE, line = null }) {
  slide.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.08,
    fill: { color: fill },
    line: line ? { color: line, width: 1 } : { color: fill, width: 0 },
    shadow: { type: "outer", color: "8899A6", blur: 6, offset: 1, angle: 90, opacity: 0.18 },
  });
}

function statCard(slide, { x, y, w, value, label, color = INK, fill = PALE }) {
  card(slide, { x, y, w, h: 1.55, fill });
  slide.addText(value, {
    x: x + 0.15, y: y + 0.18, w: w - 0.3, h: 0.72,
    fontSize: 34, bold: true, color, fontFace: HEAD, align: "center", margin: 0,
  });
  slide.addText(label, {
    x: x + 0.12, y: y + 0.92, w: w - 0.24, h: 0.5,
    fontSize: 11.5, color: GRAY, fontFace: BODY, align: "center", margin: 0,
  });
}

function bullets(slide, items, opts) {
  slide.addText(
    items.map((t, i) => ({
      text: t,
      options: { bullet: true, breakLine: i !== items.length - 1 },
    })),
    {
      fontSize: opts.fontSize ?? 15, color: opts.color ?? INK, fontFace: BODY,
      paraSpaceAfter: opts.spaceAfter ?? 10, margin: 0,
      x: opts.x, y: opts.y, w: opts.w, h: opts.h, valign: "top",
    },
  );
}

function numberedCard(slide, { x, y, w, h, n, title, body }) {
  card(slide, { x, y, w, h });
  slide.addShape(pres.ShapeType.ellipse, {
    x: x + 0.16, y: y + 0.16, w: 0.42, h: 0.42,
    fill: { color: TEAL }, line: { color: TEAL, width: 0 },
  });
  slide.addText(String(n), {
    x: x + 0.16, y: y + 0.16, w: 0.42, h: 0.42,
    fontSize: 14, bold: true, color: WHITE, fontFace: BODY,
    align: "center", valign: "middle", margin: 0,
  });
  slide.addText(title, {
    x: x + 0.68, y: y + 0.17, w: w - 0.82, h: 0.42,
    fontSize: 13.5, bold: true, color: INK, fontFace: BODY, valign: "middle", margin: 0,
  });
  slide.addText(body, {
    x: x + 0.18, y: y + 0.66, w: w - 0.36, h: h - 0.8,
    fontSize: 11, color: GRAY, fontFace: BODY, margin: 0, valign: "top",
  });
}

// ---------------------------------------------------------------- 1  Title

let s = pres.addSlide();
s.background = { color: INK };
s.addText("Transformer-Based Electricity", {
  x: 1.0, y: 2.05, w: 11.3, h: 0.75,
  fontSize: 42, bold: true, color: WHITE, fontFace: HEAD, margin: 0,
});
s.addText("Consumption Forecasting", {
  x: 1.0, y: 2.78, w: 11.3, h: 0.75,
  fontSize: 42, bold: true, color: AMBER, fontFace: HEAD, margin: 0,
});
s.addText("Multivariate time-series forecasting of household electricity demand", {
  x: 1.0, y: 3.68, w: 11.3, h: 0.4,
  fontSize: 16, color: "AFC2D2", fontFace: BODY, margin: 0, italic: true,
});
s.addText("William Peng   ·   Ciara Cameron   ·   Christopher Pedretti", {
  x: 1.0, y: 4.6, w: 11.3, h: 0.35,
  fontSize: 17, color: WHITE, fontFace: BODY, margin: 0,
});
s.addText("MSML612 — Deep Learning   |   Final Project   |   August 2026", {
  x: 1.0, y: 5.02, w: 11.3, h: 0.35,
  fontSize: 13, color: "8FA6BA", fontFace: BODY, margin: 0,
});
s.addNotes(
  "0:00–0:30 · SPEAKER 1 (suggested: intro + data)\n" +
  "CUE: Introduce team and topic in one line.\n\n" +
  "SCRIPT:\n" +
  "Good evening — we're William, Ciara, and Chris, and our project is forecasting " +
  "household electricity demand one hour ahead with a Transformer. The one-line " +
  "version: deep models in forecasting are often never compared to the forecast " +
  "you get for free — so we built that comparison in from the start, and we'll " +
  "show you a live demo of the model beating it."
);

// ---------------------------------------------------------------- 2  Problem

s = pres.addSlide();
titleOf(s, "Introduction — The Problem", "Why household-level load forecasting is hard");

bullets(s, [
  "Electricity cannot be stored cheaply at grid scale — supply must match demand continuously.",
  "Short-term load forecasting drives generation scheduling, demand-response, and home battery dispatch.",
  "Aggregate demand is smooth: thousands of appliance events average out.",
  "A single household is spiky and heavy-tailed — a few discrete, high-draw events dominate.",
  "The variance that matters operationally lives in the peaks, not the daily rhythm.",
], { x: M, y: 1.72, w: 7.1, h: 5.0, fontSize: 16.5, spaceAfter: 26 });

card(s, { x: 8.1, y: 1.72, w: 4.6, h: 2.55, fill: PALE });
s.addText("Our question", {
  x: 8.35, y: 1.98, w: 4.1, h: 0.35,
  fontSize: 14, bold: true, color: TEAL, fontFace: BODY, margin: 0,
});
s.addText(
  "Does self-attention capture enough structure in single-household demand to beat " +
  "the forecasts available for free?",
  { x: 8.35, y: 2.42, w: 4.1, h: 1.7, fontSize: 15, color: INK, fontFace: BODY, margin: 0 },
);

statCard(s, { x: 8.1, y: 4.62, w: 2.2, value: "2.08M", label: "raw minute-level readings" });
statCard(s, { x: 10.5, y: 4.62, w: 2.2, value: "4 yrs", label: "of continuous metering" });

s.addNotes(
  "0:30–1:45 · SPEAKER 1\n" +
  "CUE: Aggregate-vs-household is why this is hard and why R² is not 0.95. Land " +
  "the framing question: the bar is 'better than free', not 'low error'.\n\n" +
  "SCRIPT:\n" +
  "Why is this hard? Electricity can't be stored cheaply at grid scale, so " +
  "supply has to match demand continuously — that's why short-term load " +
  "forecasting drives generation scheduling, demand response, and battery " +
  "dispatch. But there's a scale problem. National demand curves are smooth, " +
  "because millions of appliance events average out. One household is the " +
  "opposite: the series is spiky and heavy-tailed, dominated by a handful of " +
  "discrete events — an oven, a washing machine, a water heater. The variance " +
  "that matters operationally lives in those peaks, not in the daily rhythm.\n" +
  "So our question is deliberately narrow: does self-attention capture enough " +
  "structure in a single household's demand to beat the forecasts available for " +
  "free? Four years of minute-level data, two million readings — and the bar is " +
  "not 'low error'. The bar is 'better than free', because a model that can't " +
  "clear that bar has no reason to exist."
);

// ---------------------------------------------------------------- 3  Data

s = pres.addSlide();
titleOf(s, "Data Preparation", "UCI Individual Household Electric Power Consumption");

const steps = [
  ["Clean & index", "Combine date/time into a timestamp index, coerce to numeric, and drop duplicate timestamps."],
  ["Resample hourly", "Convert minute-level readings to hourly means: 2.08M rows → 34,589 hours."],
  ["Calendar features", "Add sine/cosine encodings of hour, day, and month plus a weekend flag. 7 measured + 7 derived = 14."],
  ["Split & interpolate", "Split 70/15/15 chronologically, then time-interpolate missing hours independently within each split."],
  ["Scale", "Fit StandardScaler on training data only; transform validation and test using the training statistics."],
];
steps.forEach((st, i) => {
  numberedCard(s, {
    x: M + i * 2.46, y: 1.72, w: 2.28, h: 3.05,
    n: i + 1, title: st[0], body: st[1],
  });
});

card(s, { x: M, y: 5.1, w: W - 2 * M, h: 1.75, fill: "FDF0E1" });
s.addText("Why chronological splitting matters", {
  x: M + 0.28, y: 5.32, w: 11.6, h: 0.34,
  fontSize: 14, bold: true, color: "B35F0A", fontFace: BODY, margin: 0,
});
s.addText(
  "Neighbouring hours are highly correlated. A shuffled test set would mostly contain hours whose immediate " +
  "neighbours the model has already seen — reported performance would measure interpolation, not forecasting.",
  { x: M + 0.28, y: 5.74, w: 11.6, h: 0.9, fontSize: 14, color: INK, fontFace: BODY, margin: 0 },
);

s.addNotes(
  "1:45–3:15 · SPEAKER 1\n" +
  "CUE: Walk the pipeline quickly; spend the time on the split/scaling box — " +
  "that is what a grader will probe. Expect a question here.\n\n" +
  "SCRIPT:\n" +
  "The data is the UCI Individual Household Electric Power Consumption set: one " +
  "house near Paris, December 2006 to November 2010, seven electrical " +
  "measurements every minute. About one and a quarter percent of rows have " +
  "missing values, marked with question marks.\n" +
  "The pipeline: parse timestamps, resample to hourly means — which absorbs " +
  "most minute-level gaps and cuts two million rows to thirty-five thousand " +
  "hours — then add seven calendar features: sine-cosine encodings of hour, " +
  "day-of-week, and month, plus a weekend flag. Sine-cosine because hour 23 and " +
  "hour 0 are neighbours in reality, and an integer encoding would put them at " +
  "opposite ends.\n" +
  "Three methodology points we were strict about. The split is chronological — " +
  "never shuffled — because neighbouring hours are nearly identical, and a " +
  "shuffled split grades interpolation, not forecasting. Scalers are fit on the " +
  "training split only. And gap interpolation runs after the split, separately " +
  "per split — run it before, and hours next to the boundary get filled using " +
  "data from the other side. We actually caught that one in our own pipeline " +
  "and fixed it; the numbers you'll see are from the clean run."
);

// ---------------------------------------------------------------- 4  Solution

s = pres.addSlide();
titleOf(s, "Proposed Solution", "An encoder-only Transformer, and an evaluation designed to be falsifiable");

const solutions = [
  ["Attention over recurrence", "In an LSTM, hour 1 of the window reaches the prediction through 23 sequential state updates. Self-attention connects any two positions in one operation — constant dependency length regardless of separation."],
  ["Built for daily patterns", "Electricity use usually follows some type of daily pattern, so the previous hour is not always the most helpful for predicting what comes next. With a 24-hour window, the model can look back across the full day, including the same hour yesterday."],
  ["Pre-norm encoder layers", "LayerNorm before each sublayer rather than after: better-conditioned gradients at initialisation, no warmup schedule required."],
  ["Falsifiable evaluation", "We report skill against naive persistence, not metrics in isolation. If the model cannot beat repeating the last hour, it is not worth its complexity."],
];
solutions.forEach((sol, i) => {
  const x = i % 2 === 0 ? M : 6.95;
  const y = i < 2 ? 1.62 : 3.85;
  card(s, { x, y, w: 5.75, h: 2.0 });
  s.addShape(pres.ShapeType.ellipse, {
    x: x + 0.22, y: y + 0.24, w: 0.34, h: 0.34,
    fill: { color: i === 3 ? AMBER : TEAL }, line: { color: WHITE, width: 0 },
  });
  s.addText(sol[0], {
    x: x + 0.72, y: y + 0.2, w: 4.85, h: 0.42,
    fontSize: 15, bold: true, color: INK, fontFace: BODY, valign: "middle", margin: 0,
  });
  s.addText(sol[1], {
    x: x + 0.24, y: y + 0.72, w: 5.3, h: 1.14,
    fontSize: 11.5, color: GRAY, fontFace: BODY, margin: 0, valign: "top",
  });
});

s.addNotes(
  "3:15–4:45 · SPEAKER 2 (suggested: solution + architecture)\n" +
  "CUE: The novelty slide — 3 rubric points. Not 'we used a Transformer'; the " +
  "argument is attention fits this data for a specific reason, and the " +
  "evaluation could have proven us wrong.\n\n" +
  "SCRIPT:\n" +
  "Our solution has two halves, and the second is as deliberate as the first.\n" +
  "The model is an encoder-only Transformer. Why attention for this data? In a " +
  "recurrent model, information from the far end of the input window reaches " +
  "the prediction only after passing through twenty-three sequential state " +
  "updates, decaying at each step. Attention connects any two hours in one " +
  "step. That matters here because the most informative context is often not " +
  "the last hour. Within our 24-hour window, the model can look back " +
  "across the full day, including the same hour yesterday.\n" +
  "The second half is the evaluation. We committed upfront to three reference " +
  "forecasters — persistence, seasonal naive, and the mean, plus a comparably " +
  "sized LSTM control, and ablations over the main design choices " +
  "you'll see on the architecture slide. The literature is full of Transformer " +
  "results that evaporate against simple baselines — Zeng et al. showed that " +
  "in 2023. So we designed the evaluation to be falsifiable: if attention " +
  "wasn't earning its complexity here, this setup would have said so."
);

// ---------------------------------------------------------------- 5  Tools

s = pres.addSlide();
titleOf(s, "Tools and Technologies");

const tools = [
  ["PyTorch 2.x", "nn.TransformerEncoder, custom positional encoding, Adam, ReduceLROnPlateau"],
  ["scikit-learn", "StandardScaler fit on training split, MAE / MSE metrics"],
  ["pandas + NumPy", "Resampling, time-weighted interpolation, cyclical feature engineering"],
  ["Matplotlib", "All figures generated from one shared styling module"],
  ["Streamlit", "Live inference demo running on CPU"],
  ["Git + GitHub", "Public repo, version-bounded requirements, per-run history JSON"],
];
tools.forEach((t, i) => {
  const x = M + (i % 3) * 4.09;
  const y = i < 3 ? 1.8 : 4.35;
  card(s, { x, y, w: 3.85, h: 2.3 });
  s.addText(t[0], {
    x: x + 0.24, y: y + 0.26, w: 3.4, h: 0.42,
    fontSize: 17, bold: true, color: TEAL, fontFace: HEAD, margin: 0,
  });
  s.addText(t[1], {
    x: x + 0.24, y: y + 0.82, w: 3.4, h: 1.3,
    fontSize: 12.5, color: GRAY, fontFace: BODY, margin: 0, valign: "top",
  });
});

s.addNotes(
  "4:45–5:15 · SPEAKER 2\n" +
  "CUE: Move fast. One rubric point; do not dwell.\n\n" +
  "SCRIPT:\n" +
  "Quickly on tooling: PyTorch for the model and training loop, pandas and " +
  "scikit-learn for the pipeline, matplotlib for figures, and Streamlit for " +
  "the live demo you'll see in a few minutes. Everything is seeded and version-controlled, " +
  "every training run writes a history file, and the whole repo reproduces " +
  "from two commands — train, evaluate."
);

// ---------------------------------------------------------------- 6  Architecture

s = pres.addSlide();
s.addText("Architecture Diagram", {
  x: M, y: 0.18, w: W - 2 * M, h: 0.55,
  fontSize: 28, bold: true, color: INK, fontFace: HEAD, margin: 0,
});
// Sized to the slide, not the source: 6.3" tall at the figure's 0.6483 ratio.
s.addImage({
  path: path.join(FIG, "architecture.png"),
  x: 1.79, y: 0.9, w: 9.72, h: 6.3,
});
s.addNotes(
  "5:15–7:00 · SPEAKER 2\n" +
  "CUE: Two rubric points — highest-value slide per second. Trace the path out " +
  "loud, call out tensor shapes: they show you understand the data flow, not " +
  "just the diagram.\n\n" +
  "SCRIPT:\n" +
  "Let me trace one batch through the diagram, with shapes.\n" +
  "Input: a window of 24 hours by 14 features — seven measured, seven " +
  "calendar. A linear projection lifts each hour to 64 dimensions, so the " +
  "tensor is batch by 24 by 64. Attention is permutation-invariant — it has no " +
  "idea hour one comes before hour two — so we add fixed sinusoidal positional " +
  "encodings; same shape.\n" +
  "Then two encoder layers. Each has four attention heads — sixteen dimensions " +
  "per head — a 128-unit feed-forward, and dropout of 0.1. One detail that " +
  "matters: layer norm goes before each sublayer, not after — pre-norm, from " +
  "Xiong et al. — which keeps gradients well-conditioned without a warmup " +
  "schedule.\n" +
  "Out of the encoder: still batch by 24 by 64. We pool by taking the final " +
  "time step — batch by 64 — then dropout and a linear head to a single " +
  "number: next hour's load in standardized units, inverted back to kilowatts " +
  "for every metric you'll see.\n" +
  "Total: sixty-eight thousand trainable parameters. That's small on purpose — " +
  "with about twenty-four thousand training hours, our larger model variants performed worse, " +
  "which the capacity ablation confirms."
);

// ---------------------------------------------------------------- 7  Training

s = pres.addSlide();
titleOf(s, "Training", "Required plot: training and validation loss vs. epoch");

s.addImage({
  path: path.join(FIG, "transformer_h1_loss_curve.png"),
  x: M, y: 1.55, w: 7.4, h: 7.4 * 0.56,
});

card(s, { x: 8.25, y: 1.55, w: 4.45, h: 2.35, fill: "FDF0E1" });
s.addText("What this curve told us", {
  x: 8.5, y: 1.75, w: 3.95, h: 0.35,
  fontSize: 14, bold: true, color: "B35F0A", fontFace: BODY, margin: 0,
});
s.addText(
  "Our interim run overfit from epoch 9 to 20 — validation rising while training " +
  "fell. The final run stops that: best validation 0.3161 at epoch 11, LR halved " +
  "as improvement stalls, training halted at epoch 19.",
  { x: 8.5, y: 2.12, w: 3.95, h: 1.6, fontSize: 12.5, color: INK, fontFace: BODY, margin: 0 },
);

bullets(s, [
  "Adam, learning rate 1e-3, MSE on standardized targets",
  "Gradient-norm clipping at 1.0",
  "ReduceLROnPlateau — halve LR after 3 stalled epochs",
  "Early stopping, patience 8; best checkpoint retained",
  "All seeds fixed at 42; every run writes a history JSON",
], { x: 8.4, y: 4.15, w: 4.3, h: 2.0, fontSize: 12.5, spaceAfter: 7 });

s.addNotes(
  "7:00–8:15 · SPEAKER 2\n" +
  "CUE: REQUIRED PLOT — say 'training and validation loss versus epoch' out " +
  "loud. The overfitting story is a strength: diagnosed on the interim curve, " +
  "fixed in the final run shown here.\n\n" +
  "SCRIPT:\n" +
  "This is our training and validation loss versus epoch — the required plot — " +
  "and it has a story. Our interim run trained a fixed twenty epochs. " +
  "Validation loss bottomed out at epoch nine and then climbed for eleven " +
  "epochs while training loss kept falling — textbook overfitting, visible " +
  "right there in the curve.\n" +
  "So the final training loop earns this slide: Adam with MSE on standardized " +
  "targets, gradient clipping, a scheduler that halves the learning rate after " +
  "three stalled epochs, and early stopping with patience eight. In the run " +
  "you're looking at, validation bottomed at epoch eleven at 0.316, the " +
  "learning-rate cuts are visible as steps in the curve, and training halted " +
  "at nineteen instead of wasting eight more epochs memorizing the training " +
  "set. The checkpoint we evaluate — and demo — is the epoch-eleven one."
);

// ---------------------------------------------------------------- 8  Evaluation

s = pres.addSlide();
titleOf(s, "Evaluation Methodology", "A deep model is only interesting if it beats the forecast you get for free");

const refs = [
  ["Naive persistence", "Predict the previous hour", "The standard benchmark for hourly load — and a strong one", TEAL],
  ["Seasonal naive", "Predict the same hour yesterday", "Tests whether the daily cycle alone is predictive", INK_SOFT],
  ["Mean predictor", "Always predict the series mean", "The R² = 0 reference point", GRAY],
];
refs.forEach((r, i) => {
  const x = M + i * 4.09;
  card(s, { x, y: 1.75, w: 3.85, h: 2.9 });
  s.addText(r[0], {
    x: x + 0.24, y: 1.92, w: 3.4, h: 0.4,
    fontSize: 17, bold: true, color: r[3], fontFace: HEAD, margin: 0,
  });
  s.addText(r[1], {
    x: x + 0.24, y: 2.4, w: 3.4, h: 0.4,
    fontSize: 13, color: INK, fontFace: BODY, margin: 0, italic: true,
  });
  s.addText(r[2], {
    x: x + 0.24, y: 3.0, w: 3.4, h: 1.5,
    fontSize: 11.5, color: GRAY, fontFace: BODY, margin: 0, valign: "top",
  });
});

card(s, { x: M, y: 5.0, w: W - 2 * M, h: 1.85, fill: PALE });
s.addText(
  "Metrics: MAE, RMSE, and R², all computed in kilowatts after inverse-transforming predictions. " +
  "MAE and RMSE together are informative — their ratio shows how much error is concentrated in a few large misses. " +
  "Headline measure: skill score, the percentage RMSE reduction against persistence.",
  { x: M + 0.28, y: 5.26, w: 11.5, h: 1.4, fontSize: 14.5, color: INK, fontFace: BODY, margin: 0 },
);

s.addNotes(
  "8:15–9:15 · SPEAKER 3 (suggested: results + demo)\n" +
  "CUE: Make the case that this is the honest way to evaluate. Zeng et al. " +
  "2023 if asked why we bothered.\n\n" +
  "SCRIPT:\n" +
  "Before the numbers, the rules. Every prediction is inverse-transformed back " +
  "to kilowatts, so every error you'll see is in physical units. We report " +
  "MAE, RMSE, and R² — MAE and RMSE together, because their gap tells you " +
  "whether the error is spread evenly or concentrated in a few big misses.\n" +
  "And we compare against three forecasters that cost nothing. Persistence: " +
  "predict the previous hour — for hourly load, that's a genuinely strong " +
  "baseline. Seasonal naive: predict the same hour yesterday. And the series " +
  "mean, which is the R-squared-equals-zero floor. Our headline metric is the " +
  "skill score — the percentage RMSE reduction against persistence. If a deep " +
  "model can't beat the previous hour repeated, it has no business being " +
  "deployed. That's the bar."
);

// ---------------------------------------------------------------- 9  Results

s = pres.addSlide();
titleOf(s, "Results", "5,165 held-out hourly predictions the model never saw in training");

const rows = [
  [
    { text: "Model", options: { bold: true, color: INK } },
    { text: "MAE (kW)", options: { bold: true, color: INK, align: "center" } },
    { text: "RMSE (kW)", options: { bold: true, color: INK, align: "center" } },
    { text: "R²", options: { bold: true, color: INK, align: "center" } },
  ],
  [
    { text: "Transformer (ours)", options: { bold: true } },
    { text: "0.3062", options: { bold: true, align: "center" } },
    { text: "0.4494", options: { bold: true, align: "center" } },
    { text: "0.589", options: { bold: true, align: "center" } },
  ],
  ["Naive persistence (t−1h)", { text: "0.3724", options: { align: "center" } },
    { text: "0.5745", options: { align: "center" } }, { text: "0.327", options: { align: "center" } }],
  ["Mean predictor", { text: "0.5711", options: { align: "center" } },
    { text: "0.7005", options: { align: "center" } }, { text: "0.000", options: { align: "center" } }],
  ["Seasonal naive (t−24h)", { text: "0.4976", options: { align: "center" } },
    { text: "0.7424", options: { align: "center" } }, { text: "−0.121", options: { align: "center" } }],
];

s.addTable(rows, {
  x: M, y: 1.65, w: 7.3,
  colW: [2.95, 1.45, 1.5, 1.4],
  rowH: 0.58,
  fontSize: 12.5, fontFace: BODY, color: INK,
  border: { type: "solid", color: "CFD8DF", pt: 0.75 },
  fill: { color: WHITE },
  valign: "middle",
});

statCard(s, {
  x: 8.25, y: 1.65, w: 4.45,
  value: "21.8%", label: "RMSE reduction vs. naive persistence",
  color: TEAL, fill: "E6F4F1",
});

card(s, { x: 8.25, y: 3.55, w: 4.45, h: 3.1, fill: PALE });
s.addText("Two things worth noticing", {
  x: 8.5, y: 3.78, w: 3.95, h: 0.35,
  fontSize: 14, bold: true, color: INK, fontFace: BODY, margin: 0,
});
s.addText(
  "Seasonal naive scores worse than the mean predictor — a negative R². Household " +
  "routines vary too much day to day for yesterday's 7pm to predict today's.\n\n" +
  "Our margin is larger in RMSE (21.8%) than MAE (17.8%): the gain is concentrated " +
  "exactly where persistence fails worst.",
  { x: 8.5, y: 4.2, w: 3.95, h: 2.3, fontSize: 12.5, color: GRAY, fontFace: BODY, margin: 0 },
);

// Fill the space beneath the table with the same comparison as a visual.
s.addImage({
  path: path.join(FIG, "transformer_h1_baseline_comparison.png"),
  x: 2.25, y: 4.78, w: 4.0, h: 4.0 * 0.6118,
});

s.addNotes(
  "9:15–10:30 · SPEAKER 3\n" +
  "CUE: Lead with 21.8%. The negative-R² observation for seasonal naive is " +
  "your best 'we actually looked at this' moment.\n\n" +
  "SCRIPT:\n" +
  "The headline: a 21.8 percent RMSE reduction over naive persistence, on five " +
  "thousand one hundred sixty-five held-out predictions the model never saw in " +
  "training. MAE 0.306 kilowatts, RMSE 0.449, R² 0.589 — better than every " +
  "reference forecaster on every metric.\n" +
  "Two things in this table are worth a second look. First, seasonal naive — " +
  "repeat yesterday's same hour — is worse than just predicting the mean. " +
  "Negative R². One household's routine varies too much day to day for " +
  "yesterday's 7 p.m. to predict tonight's. The daily cycle you can see by eye " +
  "is not, by itself, predictive at this scale.\n" +
  "Second, our margin over persistence is bigger in RMSE — 21.8 percent — than " +
  "in MAE — 17.8. RMSE weights big errors more, so the model's advantage is " +
  "concentrated exactly where persistence fails worst: the transitions into " +
  "and out of demand peaks, where the previous hour tells you least."
);

// ---------------------------------------------------------------- 10  Qualitative

s = pres.addSlide();
titleOf(s, "Where the Model Still Struggles");

s.addImage({
  path: path.join(FIG, "transformer_h1_actual_vs_predicted.png"),
  x: M, y: 1.5, w: 8.0, h: 8.0 * 0.4421,
});
s.addImage({
  path: path.join(FIG, "transformer_h1_error_distribution.png"),
  x: M, y: 4.15, w: 8.0, h: 8.0 * 0.40,
});

card(s, { x: 8.9, y: 1.5, w: 3.8, h: 4.5, fill: "FDF0E1" });
s.addText("Peak under-prediction", {
  x: 9.14, y: 1.72, w: 3.32, h: 0.38,
  fontSize: 15, bold: true, color: "B35F0A", fontFace: BODY, margin: 0,
});
s.addText(
  "The model tracks the daily cycle and event timing, but consistently under-shoots " +
  "peak magnitude — predicted maxima reach 4.3 kW against observed 5.6 kW.\n\n" +
  "Residuals are right-skewed; the scatter falls below the diagonal at high load.\n\n" +
  "This is rational under MSE. A confident spike that lands an hour off is punished " +
  "twice — missed peak plus false peak — so hedging toward the mean is optimal " +
  "wherever the data is most volatile.\n\n" +
  "This pattern may be related to the MSE objective, while our capacity ablations " +
  "suggest that simply making the model larger does not solve it.",
  { x: 9.14, y: 2.18, w: 3.32, h: 3.6, fontSize: 11.5, color: INK, fontFace: BODY, margin: 0 },
);

s.addNotes(
  "10:30–11:30 · SPEAKER 3\n" +
  "CUE: The defence against 'why is R² only 0.59?'. MSE makes hedging optimal; " +
  "the fix is a quantile loss, not a bigger model. Say that explicitly.\n\n" +
  "SCRIPT:\n" +
  "Now the honest part — where the model still struggles. Look at the traces: " +
  "it tracks the daily cycle and the timing of demand events well, but it " +
  "consistently under-shoots peak height — predicted maxima around 4.3 " +
  "kilowatts against observed peaks above 5.6. The residuals are right-skewed, " +
  "and the scatter falls below the diagonal at high load. Every diagnostic " +
  "points the same way: the model hedges toward the mean when demand is high.\n" +
  "Here's the key point: that is rational behaviour under squared error, not a " +
  "capacity failure. A confident peak prediction that lands an hour early gets " +
  "punished twice — once for the missed peak, once for the false one. Hedging " +
  "gets punished moderately either way. So MSE makes shrinking toward the mean " +
  "optimal exactly where the data is most volatile. The fix isn't a bigger " +
  "model — it's a quantile loss that can express uncertainty about peaks. " +
  "That's our top-listed future work, and you'll see the behaviour live in " +
  "the demo right now."
);

// ---------------------------------------------------------------- 11  Demo

s = pres.addSlide();
s.background = { color: INK };
s.addText("Live Demo", {
  x: 1.0, y: 2.35, w: 11.3, h: 0.9,
  fontSize: 46, bold: true, color: WHITE, fontFace: HEAD, margin: 0,
});
s.addText("Forecasting from any point in the held-out test period", {
  x: 1.0, y: 3.3, w: 11.3, h: 0.45,
  fontSize: 18, color: AMBER, fontFace: BODY, margin: 0, italic: true,
});
s.addText("streamlit run demo/app.py", {
  x: 1.0, y: 4.1, w: 11.3, h: 0.45,
  fontSize: 20, color: "AFC2D2", fontFace: "Courier New", margin: 0,
});
bullets(s, [
  "Pick a moment in the test period — the model forecasts the next hour from the previous 24",
  "Prediction, ground truth, and absolute error against the surrounding load curve",
  "Performance tab: live baseline comparison   ·   About tab: architecture and training curve",
], { x: 1.0, y: 4.85, w: 11.3, h: 1.5, fontSize: 14, color: "C9D8E4", spaceAfter: 8 });

s.addNotes(
  "11:30–14:00 · SPEAKER 3\n" +
  "CUE: REQUIRED — 3 rubric points. App already running before the talk starts; " +
  "never launch live. Two forecasts: calm overnight hour, then evening peak — " +
  "own the weakness. Fallback video ready.\n\n" +
  "SCRIPT (alt-tab to the browser):\n" +
  "This is the model you just saw evaluated, running live — the epoch-eleven " +
  "checkpoint, forecasting from the held-out test period. I pick any moment " +
  "with this slider; the model sees only the preceding 24 hours.\n" +
  "First, a quiet overnight hour. [Set slider to a pre-chosen 3 a.m. origin.] " +
  "Prediction, actual, absolute error — a few hundredths of a kilowatt. Routine " +
  "load, and the model nails it.\n" +
  "Now the hard case — an evening peak. [Set slider to the pre-chosen origin.] " +
  "You can see exactly what the error analysis predicted: timing right, " +
  "magnitude short. We're showing you the failure mode on purpose — it's " +
  "systematic, we understand why it happens, and we know what fixes it.\n" +
  "[Optional if time: Performance tab — the live-computed table matches slide " +
  "9.] [Alt-tab back to the deck.]\n" +
  "REHEARSAL NOTE: choose and write down both slider origins beforehand; do " +
  "not hunt for good examples live."
);

// ---------------------------------------------------------------- 12  Ablations

s = pres.addSlide();
titleOf(s, "Ablations", "Every row is an independent train-and-evaluate cycle");

const ablRows = [
  [
    { text: "Study", options: { bold: true, color: INK } },
    { text: "Final choice", options: { bold: true, color: INK } },
    { text: "RMSE", options: { bold: true, color: INK, align: "center" } },
    { text: "Alternatives", options: { bold: true, color: INK } },
    { text: "RMSE", options: { bold: true, color: INK, align: "center" } },
  ],
  ["Window", { text: "24 hours", options: { bold: true } },
    { text: "0.4494", options: { bold: true, align: "center" } },
    "48 h / 168 h", { text: "0.4543 / 0.4553", options: { align: "center" } }],
  ["Capacity", { text: "d=64, 2 layers", options: { bold: true } },
    { text: "0.4494", options: { bold: true, align: "center" } },
    "2× depth / 2× width", { text: "0.4539 / 0.4560", options: { align: "center" } }],
  ["Positional", { text: "Sinusoidal", options: { bold: true } },
    { text: "0.4494", options: { bold: true, align: "center" } },
    "Learnable / none", { text: "0.4573 / 0.4542", options: { align: "center" } }],
  ["Features", { text: "With calendar", options: { bold: true } },
    { text: "0.4494", options: { bold: true, align: "center" } },
    "Without calendar", { text: "0.4617", options: { align: "center" } }],
  ["Architecture", { text: "Transformer", options: { bold: true } },
    { text: "0.4494", options: { bold: true, align: "center" } },
    "LSTM control", { text: "0.4579", options: { align: "center" } }],
];

s.addTable(ablRows, {
  x: M, y: 1.7, w: 8.1,
  colW: [1.45, 1.95, 0.95, 2.3, 1.45],
  rowH: 0.64,
  fontSize: 12, fontFace: BODY, color: INK,
  border: { type: "solid", color: "CFD8DF", pt: 0.75 },
  fill: { color: WHITE },
  valign: "middle",
});

card(s, { x: 9.0, y: 1.7, w: 3.7, h: 4.3, fill: "E6F4F1" });
s.addText("What the grid says", {
  x: 9.24, y: 1.92, w: 3.22, h: 0.35,
  fontSize: 14, bold: true, color: TEAL, fontFace: BODY, margin: 0,
});
s.addText(
  "Calendar features are the biggest single factor — dropping them costs more " +
  "than any architecture change.\n\n" +
  "More capacity only hurts: the constraint is data, not expressiveness.\n\n" +
  "Transformer beats the LSTM control, 21.8% vs. 20.3% skill.\n\n" +
  "Every config still beats persistence by ≥ 19.6% — the conclusion is robust.",
  { x: 9.24, y: 2.36, w: 3.22, h: 3.5, fontSize: 12, color: INK, fontFace: BODY, margin: 0 },
);

s.addNotes(
  "14:00–14:30 · SPEAKER 3\n" +
  "CUE: The evidence the architecture was chosen rather than assumed — real " +
  "weight under 'difficulty of NN design'.\n\n" +
  "SCRIPT:\n" +
  "Every row here is an independent train-and-evaluate cycle — one design " +
  "decision changed at a time, everything else held fixed. Three takeaways. " +
  "The calendar features matter most: dropping them costs more RMSE than any " +
  "architecture change. More capacity only hurts — doubling depth or width " +
  "makes things worse, so the constraint is data, not expressiveness, which " +
  "is why our model is deliberately small. And the Transformer does beat a " +
  "comparably sized LSTM — 21.8 versus 20.3 percent skill. A real margin, " +
  "and an honest one: every configuration in this grid still beats " +
  "persistence by at least 19.6 percent, so the conclusion doesn't hinge on " +
  "any single design choice."
);

// ---------------------------------------------------------------- 13  Limitations

s = pres.addSlide();
titleOf(s, "Limitations and Future Scope");

card(s, { x: M, y: 1.65, w: 5.9, h: 4.95, fill: PALE });
s.addText("Limitations", {
  x: M + 0.28, y: 1.88, w: 5.3, h: 0.4,
  fontSize: 19, bold: true, color: INK, fontFace: HEAD, margin: 0,
});
bullets(s, [
  "Single household in a single location — no claim about aggregate or cross-household performance",
  "No exogenous variables; temperature is the strongest known driver of residential demand and is absent",
  "Point forecasts with no uncertainty bounds — the wrong output format for the peak problem",
  "One-hour horizon; operational scheduling needs 24 hours ahead",
  "Single seed — small differences between ablation rows should not be over-read",
], { x: M + 0.28, y: 2.42, w: 5.34, h: 4.0, fontSize: 12.5, spaceAfter: 13 });

card(s, { x: 6.9, y: 1.65, w: 5.8, h: 4.95, fill: "E6F4F1" });
s.addText("Future work", {
  x: 7.18, y: 1.88, w: 5.2, h: 0.4,
  fontSize: 19, bold: true, color: TEAL, fontFace: HEAD, margin: 0,
});
bullets(s, [
  "Quantile / pinball loss — let the model express uncertainty about peaks instead of hedging",
  "Join hourly weather for Sceaux over the collection period",
  "Multi-step forecasting to 24 hours; the code already supports the horizon parameter",
  "Visualize attention weights to see which parts of the previous 24 hours the model relies on most",
  "Evaluate on a multi-household dataset to test transfer",
], { x: 7.18, y: 2.42, w: 5.24, h: 4.0, fontSize: 12.5, spaceAfter: 13 });

s.addNotes(
  "14:30–14:50 · SPEAKER 3\n" +
  "CUE: Be brisk. The quantile-loss point is strongest — it follows directly " +
  "from the error analysis.\n\n" +
  "SCRIPT:\n" +
  "Limitations, briefly and honestly: one household, so no claims about " +
  "generalization. No weather data — temperature is the strongest known driver " +
  "of residential demand and it isn't in this dataset, which caps achievable " +
  "accuracy. And point forecasts only. That's why the top future-work item is " +
  "a quantile loss — it attacks the peak-hedging you just watched — followed " +
  "by weather features and multi-hour horizons, which the code already " +
  "supports."
);

// ---------------------------------------------------------------- 14  References

s = pres.addSlide();
titleOf(s, "References");

const refList = [
  "[1]  Vaswani et al. Attention is all you need. NeurIPS, 2017.",
  "[2]  Hochreiter & Schmidhuber. Long short-term memory. Neural Computation, 1997.",
  "[3]  Zhou et al. Informer: Beyond efficient transformer for long sequence time-series forecasting. AAAI, 2021.",
  "[4]  Wu et al. Autoformer: Decomposition transformers with auto-correlation. NeurIPS, 2021.",
  "[5]  Zeng et al. Are transformers effective for time series forecasting? AAAI, 2023.",
  "[6]  Lim et al. Temporal fusion transformers for interpretable multi-horizon forecasting. IJF, 2021.",
  "[7]  Kong et al. Short-term residential load forecasting based on LSTM RNN. IEEE Trans. Smart Grid, 2019.",
  "[8]  Hyndman & Athanasopoulos. Forecasting: Principles and Practice, 3rd ed. OTexts, 2021.",
  "[9]  Hébrail & Bérard. Individual Household Electric Power Consumption. UCI ML Repository, 2006.",
  "[10]  Kingma & Ba. Adam: A method for stochastic optimization. ICLR, 2015.",
  "[11]  Xiong et al. On layer normalization in the transformer architecture. ICML, 2020.",
  "[12]  Nie et al. A time series is worth 64 words. ICLR, 2023.",
];
s.addText(
  refList.map((t, i) => ({ text: t, options: { breakLine: i !== refList.length - 1 } })),
  { x: M, y: 1.6, w: W - 2 * M, h: 4.6, fontSize: 12.5, color: INK, fontFace: BODY,
    paraSpaceAfter: 6, margin: 0, valign: "top" },
);

s.addNotes(
  "14:50–15:00 · SPEAKER 3\n" +
  "CUE: Do not read these. Leave up while transitioning to questions.\n\n" +
  "SCRIPT:\n" +
  "These are the works that shaped the design — happy to point at any of them " +
  "in questions. Thank you — what would you like to ask?"
);

// ---------------------------------------------------------------- 15  Questions

s = pres.addSlide();
s.background = { color: INK };
s.addText("Questions", {
  x: 1.0, y: 2.5, w: 11.3, h: 0.95,
  fontSize: 48, bold: true, color: WHITE, fontFace: HEAD, margin: 0,
});
s.addText("github.com/Ciaracam/612-Group-Project", {
  x: 1.0, y: 3.6, w: 11.3, h: 0.45,
  fontSize: 18, color: AMBER, fontFace: "Courier New", margin: 0,
});
s.addText("William Peng   ·   Ciara Cameron   ·   Christopher Pedretti", {
  x: 1.0, y: 4.5, w: 11.3, h: 0.4,
  fontSize: 16, color: "8FA6BA", fontFace: BODY, margin: 0,
});

s.addNotes(
  "Anticipated questions:\n" +
  "· Why a Transformer over an LSTM? — constant dependency length; see the LSTM control in the ablation.\n" +
  "· Why only ~22% over persistence? — appliance events are driven by human decisions that leave no trace in prior meter readings.\n" +
  "· What does attention actually learn? — untested; attention-weight visualisation is named as future work. Do not overclaim.\n" +
  "· Why window length 24? — one full daily cycle; see the window ablation.\n" +
  "· Did you try a linear baseline? — no, and Zeng et al. 2023 says we should. Concede it."
);

// ----------------------------------------------------------------

const out = path.join(ROOT, "presentation", "MSML612_final_presentation.pptx");
pres.writeFile({ fileName: out }).then(() => console.log("Wrote", out));
