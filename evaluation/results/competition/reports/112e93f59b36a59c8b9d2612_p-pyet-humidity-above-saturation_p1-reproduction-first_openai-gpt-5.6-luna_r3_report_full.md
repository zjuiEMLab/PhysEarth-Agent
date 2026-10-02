# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

Stopped after 20 unsuccessful research_plan calls in this turn. Last error: Reproduction plan incomplete: 3 evidence issue(s), 1 target coverage issue(s), and 0 parameter mapping issue(s). Structured repair gaps: [{"field": "literature_evidence", "source": "session.sections_read", "expected": "at least one opened paper section", "repair": "Call read_literature for the relevant paper section before proposing the plan."}, {"field": "literature_evidence", "source": "research_plan", "expected": "opened section/figure references", "repair": "Add the paper section references and explain their role in the reproduction."}, {"field": "reproduction_targets[0].evidence_refs", "source": "pyet@1.0, research-planning#00", "expected": "opened evidence reference", "repair": "Use the citation returned by read_literature or read_paper_figure."}]
