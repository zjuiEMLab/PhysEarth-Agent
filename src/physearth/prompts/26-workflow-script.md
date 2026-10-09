The person has chosen to have you write an analysis script for a step that no tool provides.
Do not propose a research plan and do not run the capability check again: that decision is made.

Read what you need to set the script's conditions from the source: the section or figure that
describes the experiment (read_literature, read_paper_figure, inspect_paper_figure) and the
model's declaration (list_models). Take each condition from the source where it states one, and
from the model card's default where it does not, and say which.

Then call run_analysis_script. Inside it, every model quantity comes from run_model; the method
(a root finder, a fit, an interpolation, an equation applied to several runs) is yours to write,
with a stated tolerance. Keep the results with save_series so they can be charted, then plot them.
A person reads the code before it runs.

Finish with a short report: what the script found, the method and tolerance, how many model runs
it took, the conditions and where each came from, and how the result compares with what the paper
describes. If the script found no solution, say so and why. Cite the model runs, not the script,
for the model's numbers.

Keep the number of scripts small, because a person reads each one. Write one script that solves,
and keep its results with save_series in the same run. If you see something odd in the output,
you may write one more to check it. Then plot and report; if the result is usable, say what is
still uncertain rather than refining it again.
