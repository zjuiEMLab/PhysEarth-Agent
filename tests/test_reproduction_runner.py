"""The reproduction runner separates a broken configuration from a failed cell."""

import importlib.util
import json
from pathlib import Path

import pytest

RUNNER = Path(__file__).parents[1] / "evaluation" / "runners" / "reproduction_eval.py"


def _runner():
    spec = importlib.util.spec_from_file_location("reproduction_eval_under_test", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _Config:
    """A stub provider configuration: no .env, no network, no credentials on disk."""

    def __init__(self, token=True, base="https://dashscope.aliyuncs.com/compatible-mode/v1"):
        self._token = token
        self._base = base

    def load_dotenv(self, path=".env"):
        return None

    def llm_models(self):
        return ["m"]

    def llm_api_base(self):
        return self._base

    def has_token(self):
        return self._token


def _workspace(module, tmp_path, monkeypatch, tasks=("q1", "q2"), config=None):
    task_dir = tmp_path / "tasks"
    task_dir.mkdir()
    for task_id in tasks:
        (task_dir / ("%s.yaml" % task_id)).write_text(
            "id: %s\nquestion: a research question\npaper_figures: []\n" % task_id,
            encoding="utf-8",
        )
    monkeypatch.setattr(module, "TASK_DIR", task_dir)
    monkeypatch.setattr(module, "RESULT_DIR", tmp_path / "results")
    monkeypatch.setattr(module, "config", config or _Config())
    return tmp_path / "results"


def _record(module, task_id, model="m"):
    from physearth import agent

    session = agent.new_session(model)
    return {
        "task": task_id,
        "question": "a research question",
        "llm": model,
        "build": "test",
        "phase": "completed",
        "completed": True,
        "stop_reason": None,
        "answer": "It completed.",
        "answers": ["It completed."],
        "events": [],
        "event_kinds": {},
        "figure_count": 0,
        "figures": [],
        "paper_figures": [],
        "model_calls": 1,
        "tool_calls": 1,
        "review_actions": [],
        "sections_read": [],
        "successful_runs": [],
        "protocol": {
            "planned_run_coverage": 1.0,
            "selected_figure_coverage": 1.0,
            "figure_qa_pass_rate": 1.0,
            "paper_protocol_similarity": 1.0,
            "planned_runs": 0,
            "successful_planned_runs": 0,
        },
        "tokens": {"total": 10},
        "elapsed_s": 0.1,
        "visual_similarity": {"method": "none", "per_figure": [], "mean_best_match": None},
        "_session": session,
    }


def test_an_unknown_task_id_is_a_configuration_error(tmp_path, monkeypatch):
    module = _runner()
    _workspace(module, tmp_path, monkeypatch)

    with pytest.raises(module.FatalWorkflowError) as failure:
        module.main(["--tasks", "q9", "--models", "m"])

    assert "unknown task id" in str(failure.value)
    assert "q1" in str(failure.value)


def test_missing_credentials_stop_the_matrix_before_any_cell(tmp_path, monkeypatch):
    module = _runner()
    _workspace(
        module,
        tmp_path,
        monkeypatch,
        config=_Config(token=False, base="https://api-inference.modelscope.cn/v1"),
    )

    with pytest.raises(module.FatalWorkflowError) as failure:
        module.main(["--tasks", "q1", "--models", "m"])

    assert "no inference credentials" in str(failure.value)


def test_a_broken_cell_is_recorded_and_the_matrix_continues(tmp_path, monkeypatch):
    module = _runner()
    results = _workspace(module, tmp_path, monkeypatch)

    def fake_run_cell(task, model, max_turns=8):
        if task["id"] == "q1":
            raise RuntimeError("adapter exploded")
        return _record(module, task["id"], model)

    monkeypatch.setattr(module, "run_cell", fake_run_cell)

    module.main(["--tasks", "q1", "q2", "--models", "m"])

    broken = json.loads((results / "m" / "q1" / "record.json").read_text(encoding="utf-8"))
    assert broken["stop_reason"] == "runner_error"
    assert broken["completed"] is False
    assert broken["runner_error"] == {"type": "RuntimeError", "message": "adapter exploded"}
    healthy = json.loads((results / "m" / "q2" / "record.json").read_text(encoding="utf-8"))
    assert healthy["completed"] is True


def test_a_configuration_error_inside_a_cell_aborts_the_matrix(tmp_path, monkeypatch):
    module = _runner()
    _workspace(module, tmp_path, monkeypatch)

    def fake_run_cell(task, model, max_turns=8):
        raise module.FatalWorkflowError("registry is not importable in this deployment")

    monkeypatch.setattr(module, "run_cell", fake_run_cell)

    with pytest.raises(module.FatalWorkflowError):
        module.main(["--tasks", "q1", "--models", "m"])
