# Q1–Q4 paper-reproduction evaluation

This evaluation runs the four Section 3 scientific questions with the three LLMs configured
for the deployed application (`qwen-plus`, `qwen-turbo`, and `qwen-max`). Each cell uses a
fresh session and the production research state machine:

1. read the bundled paper section and model capability declaration;
2. author a research plan;
3. approve the plan, generate pseudo-data layouts, select the required chart package, and
   approve formal execution;
4. run only registered physical models through `run_planned_model`;
5. render and review formal figures through `plot_planned_chart`;
6. publish a cited conclusion only after the workflow reaches `completed`.

Run or resume the matrix with:

```bash
python evaluation/runners/reproduction_eval.py
```

Every cell is checkpointed under `evaluation/results/reproduction/<llm>/<question>/` with
its full trace, final answer, figures, token accounting, stop reason, and SHA-256 digest.
Completed cells are reused unless `--force` is supplied.

## Metrics

- **Success:** the research phase is `completed`, at least one formal figure exists, and a
  final report was produced.
- **Protocol similarity:** 50% planned-run coverage, 30% selected-figure coverage, and 20%
  figure-QA pass rate.
- **Visual similarity:** a coarse edge-layout correlation and average-hash agreement between
  each generated PNG and its best matching paper figure. It measures presentation structure,
  not numeric curve RMSE.
- **Tokens:** the sum of provider-reported prompt and completion tokens across all calls;
  peak prompt tokens are reported separately as the largest single request context.

The external DMRT-ML, DMRT-QMS, and MEMLS programs are not registered locally. Their missing
curves are never synthesized and no cross-model numeric agreement is claimed. A cell may be a
valid partial reproduction of the executable SMRT portion while explicitly documenting this
capability gap.
