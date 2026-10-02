# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

Stopped after 20 unsuccessful research_plan calls in this turn. Last error: Reproduction plan incomplete: 3 evidence issue(s), 1 target coverage issue(s), and 0 parameter mapping issue(s). Structured repair gaps: [{"field": "literature_evidence", "source": "session.sections_read", "expected": "at least one opened paper section", "repair": "Call read_literature for the relevant paper section before proposing the plan."}, {"field": "literature_evidence[0].evidence_ref", "source": "smrt-v1#01", "expected": "a section or source figure opened in this session", "repair": "Read the cited section or figure, then use its returned citation reference."}, {"field": "reproduction_targets[0].evidence_refs", "source": "smrt-v1#01", "expected": "opened evidence reference", "repair": "Use the citation returned by read_literature or read_paper_figure."}]
