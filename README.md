---
domain:
tags:
- geoai
- remote-sensing
- radiative-transfer
- agent
- physics
datasets:
models:
deployspec:
  entry_file: app.py
license: Apache License 2.0
---

# PhysEarth-Agent

An open-source GeoAI agent that turns physical Earth models into a conversational,
verifiable, and reproducible research tool.

Most GeoAI systems are data-driven. PhysEarth runs physics instead, and its contribution
is not that it can run a physical model but that it can be trusted to configure one.
A misconfigured forward model returns numbers that look perfectly reasonable and are
physically meaningless. PhysEarth therefore enforces correctness in the harness rather
than in prompts: parameter ranges and legal option combinations are checked before any
run, results are quality-controlled automatically, and every citation in an answer must
resolve to a passage the agent actually read.

Register an Earth model with a model card and a single run function, and it immediately
inherits the same validation, quality control, and visible execution trace.

## Status

Under active development for the AP-GARSS 2026 Open Source GeoAI Practice Challenge.

## Bundled models

| Model | Medium | Output |
|---|---|---|
| SMRT | snow and ice, optional soil substrate | brightness temperature and backscatter |
| tau-omega | soil and vegetation | brightness temperature |
| Water Cloud Model | soil and vegetation | backscatter |

## Repositories

- Development: https://github.com/zjuiEMLab/PhysEarth-Agent
- Studio: https://modelscope.cn/studios/Lin5412/PhysEarth-Agent

## License

Apache-2.0. Third-party components retain their own licenses; see NOTICE.
