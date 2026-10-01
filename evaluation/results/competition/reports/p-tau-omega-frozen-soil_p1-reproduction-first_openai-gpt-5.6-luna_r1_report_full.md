# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

Stopped after 5 consecutive failed research_plan calls with no state progress. Last error: Reproduction plan incomplete: 0 evidence issue(s), 2 target coverage issue(s), and 0 parameter mapping issue(s). Structured repair gaps: [{"field": "reproduction_targets.coverage", "source": "runs/charts", "expected": "known run_ids or chart_ids", "repair": "target frozen_260K_tb has no run_ids or chart_ids coverage", "blocking": true}, {"field": "reproduction_targets[0].run_ids", "source": "registered_model_declaration", "actual": [], "expected": "run.model must match the paper reference_models", "allowed_values": ["tau-omega / CMEM emission chain"], "repair": "Replace only the target coverage with runs using the exact reference model identity, or mark the target partial/unavailable.", "blocking": true}]
