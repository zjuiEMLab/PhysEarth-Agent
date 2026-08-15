# Turning a question into a run

A question is not yet a configuration. This note is the step between them. Work through it
before the first run_model call, and say in the answer which choices the question fixed and
which you had to make.

## Decide what the question is actually asking for

| The question asks for | The run that answers it |
| --- | --- |
| A value | One point, with every parameter stated |
| A trend or a sensitivity | A sweep over the one parameter in question, not a value at each end |
| A comparison between configurations | Two runs differing in exactly one thing |
| A comparison with reality | A measurement read first, then a run at the configuration the measurement was taken at |

A sweep answers a trend question and a single point does not. Two points are not a trend:
they cannot show a turning point, and a monotonic reading of them may be wrong. Use enough
points to see the shape and no more, because every point costs a model evaluation.

## Fix the observable before anything else

Passive and active are different sensors, different outputs and usually different questions.
The word in the question that decides it is often a single one: brightness temperature,
emission and radiometer mean passive; backscatter, sigma nought, SAR and radar mean active.
If the question does not say, ask rather than guess: a run in the wrong mode answers a
question nobody asked, and it is not obvious from the number that it did.

## Separate what is given from what you chose

Every model parameter ends up with a value, whether or not the question mentioned it. Sort
them into three groups and keep the groups distinct in your head and in the answer.

- **Given**: stated in the question or in the source you are reproducing.
- **Chosen**: not stated, and the answer depends on it. Say so explicitly. Snow depth over a
  vacuum background, correlation length, and the incidence angle are the usual ones.
- **Inherited**: not stated and taken from the model's declared default. Say which defaults
  you took if a reader might reasonably have expected a different one.

A number reported without saying which group its configuration came from cannot be checked
by anyone, including you.

## When reproducing a paper figure or result

Read the paper section and the target figure before fixing the run. The caption and surrounding
paragraphs identify the observable, axes, units, legend series, panels, annotations, plotted range,
and the conditions used by the authors. Record those observations as evidence, not as silently
resolved model inputs. If the source image is unavailable, mark the target partial or unavailable
and explain what cannot be checked. Never infer numeric curve values from pixels without a separate
user-reviewed digitization step and a named reference-data artifact.

Keep the paper result, the model-generated figure, and any measured or digitized reference data as
separate provenance classes. A visual trend can support a qualitative comparison, but it cannot by
itself establish numeric agreement or a correct parameter value.

## Check the run is inside the model before running it

Read the declaration with list_models rather than assuming a range. Two questions to settle:
does every value sit inside its declared range, and is the combination legal. A combination
can be illegal while every individual value is fine, and that is the failure the declaration
exists to catch.

If the question asks for something the model declares to be outside its validity, the answer
is that it is outside, with the bound and the reason, before any number. Running at the
nearest legal value instead is acceptable only if you say plainly that is what you did and
that it is not what was asked.

## When the question is under-specified

State the assumption and proceed, or ask. Both are honest. What is not honest is picking a
default silently and reporting the resulting number as though the question determined it.
Prefer asking when the answer changes qualitatively with the missing parameter, and prefer
stating an assumption when it only shifts a value.
