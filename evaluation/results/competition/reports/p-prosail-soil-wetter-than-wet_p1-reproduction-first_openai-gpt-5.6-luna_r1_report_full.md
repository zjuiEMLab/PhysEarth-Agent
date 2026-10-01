# Reproduction report

<!-- Generated artifact; this file is human-editable. -->

Stopped after 5 consecutive failed research_plan calls with no state progress. Last error: The proposed execution plan is invalid: planned run 1: soil_moisture_fraction = 1.5 is outside the physical range 0.0 to 1.0 none Structured repair gaps: [{"field": "runs[0].parameters.soil_moisture_fraction", "source": "registered_model_declaration", "actual": 1.5, "expected": "0.0 to 1.0 none", "repair": "Use a value accepted by the registered model declaration; do not infer a limit from paper text.", "blocking": true}]
