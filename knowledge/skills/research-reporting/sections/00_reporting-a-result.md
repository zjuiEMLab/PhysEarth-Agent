# Reporting a result so it can be checked

A result that cannot be checked is not a result. This note is what to put around a number
before it goes into an answer.

## Say what kind of thing each number is

Every number in an answer is one of four things, and the reader must be able to tell which
without asking.

| Kind | Where it came from | Marker |
| --- | --- | --- |
| Computed | A run_model call in this conversation | [model:name@version] |
| Measured | A reference dataset queried in this conversation | [data:slug] |
| Reported | A section of a paper you read | [slug#id] |
| Yours | Arithmetic you did on the above | no marker, and say so |

Never let a computed number and a measured one sit in the same sentence without saying
which is which. A simulation agreeing with an observation is a claim about the model; the
same sentence with the two swapped is a claim about the world.

## Report the configuration with the number

A brightness temperature without a frequency is not an answer. State, at minimum, the
observable, the sensor configuration, and the parameters the question was about. If a value
came from a sweep, give the range swept and the number of points, not only the endpoints.

## Say what the model cannot tell you

Three limits are worth stating whenever they apply.

- **Validity**: a run near the edge of a declared range is weaker evidence than one in the
  middle, and the declaration says where the edges are.
- **Idealisation**: every bundled model here is a single homogeneous layer. Real snow is
  stratified, real soil has a roughness spectrum, and a single-layer answer is a first-order
  answer.
- **What was assumed**: the parameters you chose rather than were given, from the planning
  step, belong in the answer, not only in your reasoning.

## Report a null result as a result

"The corpus does not cover this", "the model declares this outside its range", and "the two
runs are not comparable" are answers. They are more useful than a number produced by
quietly relaxing the question, because the reader can act on them. Lead with the null result
rather than burying it after a paragraph of what you could do instead.

## Reproduction reports use an auditable layout

When a research task produces a formal figure, write a concise reader-facing report rather
than an evaluation transcript. Begin with **Research result and conclusion**: answer the
original question from the generated image in one or two paragraphs, including the visible
convergence, divergence, ordering, or comparison. Only then add supporting result values,
assumed parameters, figure-versus-result comparison, and limitations. If no generated image
exists, say so in the opening answer and do not invent a visual conclusion.

Apply validation requirements silently. Do not expose internal headings or phrases such as
`Language Compliance`, rubric, gate, workflow, prompt, QA, or evaluator in the article. The
numbered notes below define what evidence must be covered; they do not require those internal
labels to appear in the reader-facing output. Use `Not available` or `Not scoreable` rather
than silently omitting a missing result.

### Non-negotiable final-report checks

- The approved parameter-mapping ledger is authoritative. Copy its provenance class exactly;
  do not promote a `paper_inferred`, `model_assumption`, `backend_default`, `unknown`, or
  null-paper-value input to `paper_explicit`.
- Manual or LLM visual review is the primary figure validation. A deterministic title, caption,
  legend, recipe, or numeric check may fail because the paper did not specify an execution
  parameter; record that difference and its likely effect instead of treating it as automatic
  reproduction failure. If visual review confirms the same scientific curves and patterns, the
  report may call the qualitative reproduction successful.
- Reserve `failed` for an unrenderable figure, missing required curves, failed visual review, or
  contradiction of a parameter that the paper explicitly required. Use `partial` or
  `not scoreable` when the limitation is only quantitative comparability. Visual agreement does
  not waive a failed model run, missing evidence, an unsupported model/output, or a numeric or
  parameter constraint explicitly required by the user.
- Never invent correlation, RMSE, bias, ratio, percent error, or other agreement statistics.
  If an actual tool result did not provide or calculate the quantity, write `N/A`.
- A successful render or post-render quality review proves that a chart is usable; it does not
  prove that it agrees with the published figure.
- Answer the original research question directly in the final conclusion. If the requested
  range or threshold is not supported by opened evidence or recorded results, say so.
- Do not write "matches exactly" or "no visual discrepancy" unless an explicit comparison
  check supports that wording; name visible differences and their consequences.

### 1. Scope and outcome

State the research question, the figure or result target, the model and version actually run,
and the outcome: reproduced, partial, unavailable, or not comparable. Base figure success on
the manual/visual review and explain any deterministic check differences as parameter or
metadata diagnostics.

### 2. Parameter provenance: list every guessed value

Include a compact table with one row for every input that affects the result:

| Input | Value used | Provenance | Evidence or reason |
| --- | --- | --- | --- |

Use the exact provenance classes from the plan: `paper_explicit`, `paper_inferred`,
`user_specified`, `model_assumption`, and `backend_default`. Put every
`paper_inferred`, `model_assumption`, and `backend_default` row in a clearly labelled
**Guessed/assumed parameters** subsection as well. “Guessed” means selected without direct
paper or user evidence; it does not mean the value was invalid. Do not describe a guessed
frequency, temperature, sweep range, angle, thickness, stickiness, resolution, or default as
paper-explicit. If a value differs from the paper or is not specified by it, state the
difference and its likely effect instead of hiding it in a footnote.

### 3. Conclusion from the source and generated figures

For each formal figure, first report only what the image supports: title, x/y axes and units,
legend and curve count, grouping/order, qualitative shape, convergence/divergence, and visible
crossings or separation. This is the **figure-based conclusion**. Do not digitize a bitmap or
invent point values from visual distance. Say when the figure is compressed, cropped, missing
metadata, or otherwise insufficient for a claim.

### 4. Conclusion from actual model results

Separately report what the executed result arrays and quality checks support: the output handle,
the exact conditions, trends computed from the arrays, and any numerical comparison that was
actually calculated. This is the **result-backed conclusion**. A chart title or a planned run is
not evidence that a model ran, and a visual similarity judgement is not an RMSE or a physical
measurement.

### 5. Figure-versus-results comparison and final conclusion

For each figure, include a short comparison with four fields:

| Question | Figure-based reading | Result-backed reading | Agreement and qualification |
| --- | --- | --- | --- |

Explain which visible patterns agree with the actual arrays, which do not, and why a mismatch
could arise (parameter assumption, model/version difference, rendering/aspect ratio, or a
failed/insufficient check). If the figure says one curve is higher but the recorded values say
otherwise, report the contradiction and do not resolve it by assertion. End with a calibrated
conclusion that distinguishes what was reproduced, what was only qualitatively similar, and
what remains unverified or unavailable.

Every claim in these sections still needs the appropriate paper, figure, model, dataset, or
method marker. Keep the paper's reported result, the generated figure, and the actual model
output visibly separate.

## Do not restate what is already on screen

A chart is already showing its values. Repeating the series point by point in prose adds
nothing a reader can use and invites transcription errors. Describe the shape, name the
turning points that matter, and let the figure carry the numbers.
