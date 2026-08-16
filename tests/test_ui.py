import re
from pathlib import Path

from physearth import agent, prompt
from physearth.corpus import knowledge
from physearth.harness import budget

from frontend import theme
from frontend import views as render


def test_optimistic_ui_never_replaces_gradio_managed_html():
    """Direct innerHTML writes detach streamed answer slots from Gradio updates."""
    source = (Path(__file__).parents[1] / "frontend" / "static" / "ui.js").read_text()
    assert ".innerHTML =" not in source


def test_trace_cards_do_not_replay_an_entry_animation_on_every_gradio_frame():
    """The entire trace subtree is replaced; :last-child animation would keep restarting."""
    source = (Path(__file__).parents[1] / "frontend" / "static" / "ui.css").read_text()
    assert ".step-card:last-child {\n  animation:" not in source


def test_unchanged_conversation_is_not_replaced_for_a_trace_only_frame(monkeypatch):
    """A tool lifecycle event must not remount the unchanged streamed transcript."""
    from physearth import session as session_state

    from frontend import studio as app

    box = session_state.new_session(agent.default_model())
    state = session_state.new_state(box)
    state["phase"] = "calling_model"
    first_events = []
    second_events = [{"kind": "model_call", "at": "00:00:00", "index": 1}]

    def fake_stream(*_args, **_kwargs):
        yield "stable answer", first_events, state
        yield "stable answer", second_events, state

    monkeypatch.setattr(app.agent, "stream", fake_stream)
    frames = list(app.respond("question", [], box, agent.default_model()))

    # Frame 1 is the initial pending layout; frame 2 adds the transcript.  Frame 3 only
    # adds a trace event, so its Conversation output must be Gradio's no-op update.
    assert "stable answer" in frames[1][3]
    assert frames[2][3].get("__type__") == "update"
    assert "MODEL CALL" in frames[2][4]


def test_execution_continuation_preserves_conversation_and_only_removes_plan_card(monkeypatch):
    from physearth import session as session_state

    from frontend import studio as app

    box = session_state.new_session("m")
    turns = [{
        "index": 1,
        "question": "run the approved research plan",
        "answer": "The plan is approved for execution.",
        "events": [],
        "faulted": False,
        "state": {},
    }]
    state = session_state.new_state(box)
    state["phase"] = "done"

    def fake_stream(*_args, **_kwargs):
        yield "The physical run completed.", [{"kind": "model_call", "index": 1}], state

    monkeypatch.setattr(app.agent, "stream", fake_stream)
    frames = list(app.resume_after_review("continue execution", turns, box, "m"))

    # Neither the initial continuation frame nor the final result replaces the existing
    # history subtree. The final answer is shown in the live result and merged into state.
    assert frames[0][2].get("__type__") == "update"
    assert frames[-1][2].get("__type__") == "update"
    assert "The physical run completed." in frames[-1][3]
    assert "The physical run completed." in frames[-1][8][-1]["answer"]


def test_plan_approval_chain_is_an_explicit_ui_noop(monkeypatch):
    """Approving a plan must not invoke the full-output continuation as a reset."""
    from frontend import studio as app

    called = []

    def fake_stream(*_args, **_kwargs):
        called.append(True)
        yield "unexpected continuation", [], {"phase": "done"}

    monkeypatch.setattr(app.agent, "stream", fake_stream)
    frames = list(app.resume_after_review("", [], {}, "m"))

    assert not called
    assert len(frames) == 1
    assert len(frames[0]) == 11
    assert all(item.get("__type__") == "update" for item in frames[0])


def test_basic_case_and_guided_approval_resume_keep_the_existing_conversation(monkeypatch):
    """All user-facing case starters share the same direct-tool approval route."""
    from frontend.views import evaluation as evals
    from physearth import session as session_state
    from physearth.harness import approval

    from frontend import studio as app

    state = session_state.new_state(None)
    state["phase"] = "done"

    def fake_stream(*_args, **_kwargs):
        yield "Approved run completed.", [{"kind": "model_call", "index": 1}], state

    monkeypatch.setattr(app.agent, "stream", fake_stream)
    turns = [{
        "index": 1,
        "question": "existing question",
        "answer": "existing answer",
        "events": [],
        "faulted": False,
        "state": {},
    }]

    sessions = []
    for case in evals.basic_cases()[1:2]:
        sessions.append(app.start_basic_case(case["question"], case["id"], "m")[9])
    sessions.append(app.start_guided_demo(evals.guided_demo()["question"], "m")[9])

    for box in sessions:
        approval.request(box, "run_model", {"model": "smrt", "parameters": {}})
        app.review_click(box, "primary")
        assert box.get("preserve_conversation_on_resume") is True
        frames = list(app.respond("approved continuation", turns, box, "m"))
        assert frames[-1][2].get("__type__") == "update"
        assert frames[-1][8][-1]["answer"].endswith("Approved run completed.")


def test_direct_approval_hides_the_stale_card_until_the_agent_clears_it():
    from physearth import session as session_state
    from physearth.harness import approval

    from frontend import studio as app
    from frontend import views as render

    box = session_state.new_session("m")
    approval.set_mode(box, approval.ASK)
    approval.request(box, "run_model", {"model": "smrt", "parameters": {}})

    app.review_click(box, "primary")

    assert box["approval_resuming"] is True
    assert "hidden" in render.research_context(box)


def test_answer_text_is_escaped_before_anything_else():
    out = render.answer_html("<script>alert(1)</script> and <img onerror=x>")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert "onerror" not in out or "&lt;img" in out


def test_equation_subscripts_and_superscripts_are_safe_allowlisted_markup():
    out = render.answer_html("T<sub>B</sub> and k<sup>2</sup>")
    assert "T<sub>B</sub>" in out
    assert "k<sup>2</sup>" in out
    unsafe = render.answer_html("<sub class='bad'>x</sub><script>alert(1)</script>")
    assert "&lt;sub class=&#x27;bad&#x27;&gt;" in unsafe
    assert "&lt;script&gt;" in unsafe


def test_long_pasted_revision_text_preserves_lines_and_escapes_markup():
    from physearth import session

    pasted = "format: phys-earth/research-protocol\nplan_version: 2\nruns:\n  - id: density\n    label: <script>alert(1)</script>\ncharts:\n  - id: trend\nassumptions:\n  - dry snow"
    out = render.history([{
        "question": pasted,
        "answer": "I will review the requested changes.",
        "faulted": False,
    }], session=session.new_session("m"))

    assert "Pasted revision text · 9 lines" in out
    assert "format: phys-earth/research-protocol\nplan_version: 2" in out
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in out
    assert "<script>" not in out


def test_research_plan_preview_is_structured_and_keeps_yaml_in_a_disclosure():
    from physearth import session

    box = session.new_session("m")
    box["research"] = {
        "phase": "plan_review",
        "plan_version": 2,
        "selected_charts": [],
        "plan": {
            "question": "How does density affect the output?",
            "hypothesis": "The output changes with density.",
            "runs": [{"id": "density", "label": "Density sweep", "model": "smrt", "parameters": {"sweep_start": 10, "sweep_stop": 100}}],
            "charts": [{"id": "density_chart", "label": "Density", "x": "density", "y": "ks_per_m"}],
            "literature_evidence": [{"evidence_ref": "paper#01", "purpose": "method"}],
            "reproduction_targets": [{"id": "target", "source_type": "result", "source_id": "section-1", "target_quantity": "ks_per_m", "status": "partial", "run_ids": ["density"], "chart_ids": ["density_chart"]}],
            "selected_models": [{"model": "smrt", "version": "1.0", "purpose": "test"}],
            "parameter_mapping": [{"paper_concept": "density", "paper_value": 100, "model_input": "density_kg_m3", "mapped_value": 100, "provenance_class": "paper_explicit"}],
            "paper_conditions": {"frequency_ghz": 37},
            "condition_provenance": {"frequency_ghz": "paper#01"},
            "validation_warnings": [{
                "code": "paper_context_difference",
                "field": "runs[density].parameters.sweep_start",
                "expected": 10,
                "actual": 1,
                "blocking": False,
            }],
            "assumptions": ["homogeneous layer"],
            "limitations": ["single model"],
            "success_criteria": ["finite output"],
            "outputs": ["ks_per_m"],
            "steps": ["read", "run", "review"],
            "revision_summary": {"from_version": 1, "to_version": 2, "changed": [{"field": "assumptions", "from": ["old"], "to": ["homogeneous layer"]}], "invalidated": ["pseudo_preview"], "preserved": ["runs", "charts"]},
        },
    }
    out = render.approval_bar(box)

    assert "Question and hypothesis" in out
    assert "Literature evidence" in out
    assert "Reproduction targets" in out
    assert "Paper concept" in out and "Model input" in out
    assert "Planned runs" in out and "Resolved parameters" in out
    assert "Validation sources and warnings" in out
    assert "paper_context_difference" in out
    assert "non-blocking" in out
    assert "REVISION SUMMARY · v001 → v002" in out
    assert "Raw generated protocol YAML" in out
    assert "research-plan-yaml" in out
    assert "Pasted revision text" not in out


def test_revised_plan_card_is_collapsed_while_revision_summary_remains_visible():
    from physearth import research, session

    box = session.new_session("m")
    result = research.propose(
        box,
        question="How does density affect the registered model output?",
        objective="Quantify the density response",
        hypothesis="The response changes across the density range",
        steps=["read declarations", "run the model", "review the figure"],
        parameters={"sweep_start": 10, "sweep_stop": 100},
        runs=[{
            "id": "density",
            "label": "Density sweep",
            "model": "smrt",
            "parameters": {
                "output": "coefficients",
                "sweep_parameter": "density_kg_m3",
                "sweep_start": 10,
                "sweep_stop": 100,
                "sweep_points": 5,
            },
        }],
        charts=[{"id": "density", "label": "Density", "kind": "line", "x": "density_kg_m3", "y": "ks_per_m"}],
        quantities=["ks_per_m"],
        controls=["frequency fixed"],
        metrics=["trend"],
        diagnostics=["finite outputs"],
        success_criteria=["finite outputs"],
        stop_conditions=["model failure"],
        assumptions=["homogeneous layer"],
        limitations=["registered model scope"],
        baseline_run_id="density",
    )
    assert result["status"] == "needs_input"
    assert "data-collapsed='false'" in render.approval_bar(box)

    revised = research.revise(box, {"assumptions": ["revised layer assumption"]})
    assert revised["status"] == "needs_input"
    out = render.approval_bar(box)
    assert "data-collapsed='true'" in out
    assert "REVISION SUMMARY" in out


def test_plan_review_exposes_only_the_two_review_controls():
    from pathlib import Path

    app_source = (Path(__file__).parents[1] / "frontend" / "studio.py").read_text(encoding="utf-8")
    js_source = (Path(__file__).parents[1] / "frontend" / "static" / "ui.js").read_text(encoding="utf-8")
    assert "Revise / Regenerate" not in app_source
    assert 'gr.Button("Pause"' not in app_source
    assert "pe-approve-no" not in app_source and "pe-approve-no" not in js_source
    assert "Approve plan" in app_source and "Satisfied with figures" in app_source
    assert 'document.querySelector(".research-plan-details[open]")' in js_source


def test_guided_research_context_shows_live_capability_and_agent_paper_session():
    from physearth import session

    box = session.new_session("m")
    box["research_context"]["reproduction_case"] = "q1"
    box["research_context"]["paper_session"] = {
        "paper": "smrt-v1",
        "source_section": "smrt-v1#08",
        "paper_section": "3.1.1",
        "doi": "10.5194/gmd-11-2763-2018",
    }
    box["research_context"]["capabilities"]["smrt"] = {
        "name": "smrt",
        "version": "1.5.1",
        "runnable_here": True,
        "outputs": ["ks_per_m", "ka_per_m"],
        "parameter_options": {
            "electromagnetic_model": ["rayleigh", "iba", "dmrt_qcacp_shortrange"],
            "microstructure_model": ["independent_sphere", "sticky_hard_spheres"],
        },
    }
    out = render.research_context(box)
    status = render.conversation_head(0, box)
    brief = render.guided_brief(box)

    assert "PAPER BRIEF" not in out
    assert "LIVE RESEARCH STATUS" not in out
    assert "MODEL SUPPORT CHECK" not in status
    assert "PAPER SESSION" in brief
    assert status.count("LIVE RESEARCH STATUS") == 1
    assert "Idle" in status
    assert "FROM PAPER SECTIONS" in brief.upper()
    assert "Open DOI / paper source" in brief
    assert "rayleigh" not in status and "sticky_hard_spheres" not in status


def test_guided_demo_does_not_inject_evaluation_data_before_agent_discovery():
    from frontend.views import evaluation as evals

    from frontend import studio as app

    question = evals.guided_demo()["question"]
    result = app.start_guided_demo(question, agent.default_model())
    context_html = result[7]
    brief_html = result[2]
    guided_session = result[9]

    assert result[10] == question
    assert guided_session["research_required"] is True
    assert "demo" not in guided_session["research_context"]
    assert "FIXED REPRODUCTION BRIEF" not in context_html
    assert "research-context' hidden" in context_html
    assert "PAPER SESSION" not in brief_html

    # The Evaluation card supplies the user-facing question only.  Its paper brief,
    # fixed conditions, and run matrix must not be copied into the model prompt.
    model_prompt = prompt.build(agent.new_state(guided_session))
    assert "smrt-q1-guided" not in model_prompt
    assert "Reproduce the SMRT sparse-medium comparison" not in model_prompt
    assert "radius_m=0.0001" not in model_prompt
    assert "q1_rayleigh_independent" not in model_prompt

    guided_session["research"] = {
        "reproduction_case": "q1",
        "phase": "plan_review",
        "plan_version": 1,
        "plan": {
            "question": question,
            "reproduction_case": "q1",
        "parameters": {"angle_deg": 55.0},
        "paper_conditions": {"frequency_ghz": 37.0, "radius_m": 0.0001},
        "condition_provenance": {
            "frequency_ghz": "paper:smrt-v1#08",
            "radius_m": "paper:smrt-v1#08",
        },
            "assumptions": ["dry snow"],
            "quantities": ["ks_per_m"],
            "runs": [{
                "id": "q1_iba_sticky",
                "label": "IBA with sticky hard spheres",
                "parameters": {
                    "electromagnetic_model": "iba",
                    "microstructure_model": "sticky_hard_spheres",
                    "output": "coefficients",
                    "sweep_parameter": "density_kg_m3",
                },
            }],
        },
    }
    guided_session["research_context"]["paper_session"] = {
        "paper": "smrt-v1",
        "source_section": "smrt-v1#08",
        "paper_section": "3.1.1",
        "doi": "10.5194/gmd-11-2763-2018",
    }
    updated = render.research_context(guided_session)
    assert "FIXED REPRODUCTION BRIEF" not in updated
    assert "LIVE RESEARCH STATUS" not in updated
    assert "LIVE RESEARCH STATUS" in render.conversation_head(1, guided_session)
    assert "3.1.1" in render.guided_brief(guided_session)
    assert "AGENT PLAN: RUNS" in render.guided_brief(guided_session)
    assert "AGENT PLAN: EXPECTED OUTPUTS" in render.guided_brief(guided_session)
    assert "From paper sections" in render.guided_brief(guided_session)
    assert "dry snow" in render.guided_brief(guided_session)
    assert "q1_iba_sticky" in render.guided_brief(guided_session)
    assert "q1_rayleigh_independent" not in render.guided_brief(guided_session)


def test_conversation_renders_markdown_headings_inside_the_message_body():
    out = render.answer_html("## Convergence Range\n\nAll theories converge here.")
    assert "<h2>Convergence Range</h2>" in out
    assert "## Convergence Range" not in out


def test_markers_become_chips_that_name_their_evidence():
    out = render.answer_html("a [smrt-v1#12] b [model:smrt@1.5.1] c [data:tvc-backscatter]")
    assert "data-jump='sec-smrt-v1#12'" in out
    assert "data-jump='model-smrt'" in out
    assert "data-jump='data-tvc-backscatter'" in out
    assert out.count("class='cite") == 3


def test_a_blocked_call_names_the_rule_and_the_offending_value():
    event = {
        "kind": "harness_block",
        "at": "00:00:00",
        "rule": "physical_domain",
        "tool": "run_model",
        "detail": "density_kg_m3 = 2000.0 is outside the physical range",
        "problems": ["density_kg_m3 = 2000.0 is outside the physical range 50.0 to 917.0"],
        "intervention": 1,
    }
    out = render.trace([event], agent.new_state())
    assert "step-card--block" in out
    assert "physical_domain" in out
    assert "2000.0" in out
    assert "BLOCKED" in out


def test_the_trace_shows_a_running_card_only_while_the_turn_is_live():
    state = agent.new_state()
    state["phase"] = "calling_model"
    assert "step-card--thinking" in render.trace([], state, running=True)
    assert "step-card--thinking" not in render.trace([], state, running=False)


def test_a_figure_declares_where_its_numbers_came_from():
    figure = {
        "png": "data:image/png;base64,AAAA",
        "title": "t",
        "kind": "line",
        "provenance": ["measured", "model_run"],
        "series": [
            {"label": "a", "source": "measured", "origin": "tvc", "n_points": 3, "handle": "h"},
            {"label": "b", "source": "model_run", "origin": "smrt@1", "n_points": 3, "handle": "h"},
        ],
    }
    out = render.evidence({}, [figure], set(), set())
    assert "fig-ribbon--measured" in out
    assert "measured" in out and "model run" in out


def test_every_bundled_paper_is_browsable_with_its_licence_and_doi():
    out = render.evidence({}, [], set(), set())
    for entry in knowledge.catalogue():
        assert entry["slug"] in out
        assert entry["license"] in out
    assert out.count("doi.org/10.5194") >= len(knowledge.slugs())


def test_the_session_shows_every_turn_until_it_is_cleared():
    turns = [
        {"index": 1, "question": "q one", "answer": "a one", "events": [], "state": {}},
        {"index": 2, "question": "q two", "answer": "a two", "events": [], "state": {}},
    ]
    out = render.history(turns)
    assert out.count("msg--user") == 2
    assert out.count("msg--agent") == 2
    assert "q one" in out and "a two" in out
    assert render.history([]).count("msg--") == 0


def test_the_model_switcher_marks_the_running_model():
    second = agent.CATALOGUE[1]["id"]
    out = render.hero(second)
    assert "data-model='%s'" % second in out
    assert re.search(r"data-model='%s' class='is-active'" % re.escape(second), out)
    assert out.count("data-model=") == len(agent.CATALOGUE)


def test_an_unknown_model_falls_back_to_the_default():
    assert agent.resolve_model("evil/model") == agent.default_model()
    for item in agent.CATALOGUE:
        assert agent.resolve_model(item["id"]) == item["id"]


def test_the_stylesheet_carries_the_fonts_and_neutralises_gradio():
    css = theme.css()
    assert "@font-face" in css
    assert "Anthropic Serif" in css
    assert "display: contents !important" in css
    assert "#pe-app" in css
    assert theme.js().strip().endswith("peBoot();")


def test_the_layout_has_resizable_and_hideable_panel_controls():
    css = theme.css()
    js = theme.js()
    assert "pe-layout-handle" in css
    assert "pe-layout-tools" not in css
    assert "data-layout-panel" not in js
    assert "pointerdown" in js
    assert "localStorage" in js
    assert "grid-template-columns" in js
    assert 'grid-template-areas: "chat trace" "chat evid"' not in css
    assert "pe-panel-chat" in js
    assert "rightRect" in js
    assert "col-resize" in css
    assert "document.addEventListener(\"pointermove\"" in js
    assert "document.addEventListener(\"mousemove\"" in js
    assert 'minmax(180px, " + layout.ratios[index] + "fr)' in js


def test_upload_workbench_is_separate_and_the_chat_context_has_one_scroll_surface():
    source = (Path(__file__).parents[1] / "frontend" / "studio.py").read_text(encoding="utf-8")
    css = theme.css()
    js = theme.js()

    assert 'gr.Tab("Upload & Test"' in source
    assert 'label="Upload paper PDF"' not in source
    assert "scrollbar-gutter: stable" in css
    assert "var forceLatest = !!context" not in js
    assert "scrollToEnd(document.getElementById(\"pe-chat-scroll\"), true);" in js
    assert "#pe-chat-scroll > #pe-approve" in css


def test_the_quota_message_names_the_model_and_the_alternatives():
    event = {
        "kind": "harness_stop",
        "at": "00:00:00",
        "rule": "quota",
        "reason": "rate limited (HTTP 429)",
        "model": "Qwen/Qwen3.5-122B-A10B",
        "upstream": "You have exceeded today's quota for model Qwen/Qwen3.5-122B-A10B",
    }
    out = render.trace([event], agent.new_state())
    assert "what the endpoint said" in out
    assert "exceeded today" in out
    assert "Qwen/Qwen3.5-122B-A10B" in out


def test_a_spent_daily_quota_is_not_retried():
    class Spent(Exception):
        status_code = 429
        body = {"message": "You have exceeded today's quota for model X, try again tomorrow"}

    class Busy(Exception):
        status_code = 429
        body = {"message": "Too many requests, slow down"}

    class EmptyBalance(Exception):
        status_code = 429
        body = {"message": "insufficient balance"}

    assert agent._dead_for_today(Spent()) == "quota"
    assert agent._dead_for_today(Busy()) == ""
    assert agent._fault(Spent()) == "model quota or balance exhausted (HTTP 429)"
    assert agent._dead_for_today(EmptyBalance()) == "quota"
    assert agent._fault(EmptyBalance()) == "model quota or balance exhausted (HTTP 429)"


def test_clearing_the_session_resets_the_panels_but_not_the_shared_quota():
    from frontend import studio as app

    used_before = budget.used()
    hero, head, history, live, trace, metrics, evidence, approve, turns, session, box = app.reset(
        agent.default_model()
    )
    assert turns == [] and box == ""
    assert "hidden" in approve
    assert session["turns"] == 0 and not session["sections_read"]
    assert "msg--" not in history and "msg--" not in live
    assert "Nothing has run yet" in trace
    assert "No chart yet" in evidence
    expected_cap = used_before[1] if used_before[1] else "∞"
    assert "%d / %s" % (used_before[0], expected_cap) in metrics


def test_the_opening_hint_belongs_to_the_empty_session_only():
    assert "pane-empty" in render.history([])
    assert "pane-empty" not in render.live("", "")
    turns = [{"index": 1, "question": "q", "answer": "a", "events": [], "state": {}}]
    assert "pane-empty" not in render.history(turns)
    assert "pane-empty" not in render.live("", "")


def test_a_withdrawn_model_is_not_retried_either():
    class Gone(Exception):
        status_code = 400
        body = {"message": "Model id : x/y , has no provider supported"}

    class Other(Exception):
        status_code = 400
        body = {"message": "unsupported parameter"}

    assert agent._dead_for_today(Gone()) == "withdrawn"
    assert agent._dead_for_today(Other()) == ""


def test_a_turn_that_died_upstream_is_marked_and_kept_out_of_the_context():
    from frontend import studio as app

    fault = [{"kind": "harness_stop", "rule": "quota", "reason": "rate limited"}]
    good = [{"kind": "harness_pass", "rule": "citation_integrity", "markers": []}]
    assert app._faulted(fault) and not app._faulted(good)

    turns = [
        app._archive(1, {}, fault, "q one", "The free daily quota is used up."),
        app._archive(2, {}, good, "q two", "A real answer."),
    ]
    seen = [
        {"role": role, "content": content}
        for t in turns
        if not t.get("faulted")
        for role, content in (("user", t["question"]), ("assistant", t["answer"]))
    ]
    assert [m["content"] for m in seen] == ["q two", "A real answer."]

    out = render.history(turns)
    assert out.count("msg--fault") == 1
    assert "not an answer" in out


def test_clearing_the_session_starts_in_normal_q_and_a_mode():
    """Research is selected by the agent, while ordinary model calls retain approval."""
    from physearth.harness import approval

    from frontend import studio as app

    first = app._session(None, agent.default_model())
    assert approval.required(first)
    assert first["research_required"] is False

    session = app.reset(agent.default_model())[9]
    assert approval.required(session)
    assert session["research_required"] is False
    assert app._session(session, agent.default_model()) is session
    assert approval.required(session)


def test_the_evidence_panel_is_cheap_enough_to_redraw():
    """It is rendered on every stream yield, so a linear scan of a 23658-row table inside
    it once cost thirty seconds a chunk."""
    import time

    from physearth.corpus import reference

    started = time.perf_counter()
    render._dataset_card("tvc-backscatter")
    assert time.perf_counter() - started < 2.0

    indices, _ = reference.query("tvc-backscatter")
    summary = reference.summarise("tvc-backscatter", indices)
    assert summary["band"]["values"] == ["C", "Ku", "X"]
    assert summary["sigma0_db"]["min"] < summary["sigma0_db"]["max"]
    assert len(reference.columns("tvc-backscatter", indices)["sigma0_db"]) == len(indices)


def test_a_marker_is_escaped_once_and_only_once():
    out = render.answer_html("see [abs:10.1175/1520-0442(2003)016<0100:X>2.0.CO;2] for that")
    assert "&amp;amp;" not in out
    assert "&amp;lt;" not in out
    assert "&lt;0100:X&gt;" in out


def test_the_switcher_never_shows_nothing_selected():
    out = render.hero("someone/else")
    assert out.count("is-active") == 1
    assert "data-model='%s' class='is-active'" % agent.default_model() in out


def test_provider_neutral_llm_config_falls_back_to_modelscope(monkeypatch):
    from physearth import config

    monkeypatch.setenv("PHYSEARTH_LLM_API_KEY", "generic-key")
    monkeypatch.setenv("PHYSEARTH_LLM_API_BASE", "https://generic.example/v1")
    monkeypatch.setenv("PHYSEARTH_LLM_MODEL", "generic-model")
    monkeypatch.setenv("PHYSEARTH_LLM_MODELS", "generic-model,second-model")
    assert config.llm_api_key() == "generic-key"
    assert config.llm_api_base() == "https://generic.example/v1"
    assert config.llm_model() == "generic-model"
    assert config.llm_models() == ["generic-model", "second-model"]


def test_only_one_route_reaches_the_agent():
    """Two bindings would let a stray submit start a second run against one session."""
    from frontend import studio as app

    handlers = [
        dep for dep in app.demo.fns.values()
        if getattr(dep, "name", None) == "respond" or getattr(getattr(dep, "fn", None), "__name__", "") == "respond"
    ]
    assert len(handlers) == 1


def test_chart_click_records_the_human_choice_without_an_llm_turn():
    from physearth import research, session

    from frontend import studio as app

    box = session.new_session("m")
    research.propose(
        box,
        question="q",
        objective="compare model outputs",
        hypothesis="the curves differ",
        steps=["inspect", "run", "plot"],
        parameters={"sweep_start": 1, "sweep_stop": 10},
        runs=[
            {
                "id": "run_1",
                "label": "SMRT run",
                "model": "smrt",
                "parameters": {
                    "output": "tb",
                    "sweep_parameter": "density_kg_m3",
                    "sweep_start": 1,
                    "sweep_stop": 10,
                    "sweep_points": 5,
                },
            }
        ],
        charts=[{"id": "curve", "label": "Curve", "kind": "line", "x": "density_kg_m3", "y": "tb_v"}],
        quantities=["tb_v (K)"], controls=["frequency fixed"], metrics=["trend"],
        diagnostics=["finite values"], success_criteria=["valid curve"],
        stop_conditions=["baseline failure"], assumptions=["dry snow"],
        limitations=["single model"], baseline_run_id="run_1",
    )
    research.approve_plan(box)
    research.pseudo_preview(box)

    card, evidence, updated, cleared = app.select_chart_click(box, "curve")
    assert updated["research"]["phase"] == "chart_selected"
    assert updated["research"]["selected_chart"]["id"] == "curve"
    assert "data-research-phase='chart_selected'" in card
    assert "PSEUDO-DATA" not in evidence
    assert cleared == ""


def test_a_windowed_rate_limit_is_waited_out_not_reported_as_a_fault():
    """Three fault classes that look alike and must not be treated alike: a limit that
    clears by waiting, a quota that will not clear until tomorrow, and a model the
    endpoint no longer serves."""

    class Rpm(Exception):
        status_code = 429
        body = {"message": "request limited RPM reached, current: 11, limit: 10"}

    class Spent(Exception):
        status_code = 429
        body = {"message": "You have exceeded today's quota for model X"}

    class Gone(Exception):
        status_code = 400
        body = {"message": "Model id : x/y , has no provider supported"}

    assert agent._rate_limited(Rpm()) and agent._dead_for_today(Rpm()) == ""
    assert not agent._rate_limited(Spent()) and agent._dead_for_today(Spent()) == "quota"
    assert not agent._rate_limited(Gone()) and agent._dead_for_today(Gone()) == "withdrawn"

    # The wait has to outlast the window it is counted over, or retrying cannot help.
    span = sum(agent.RATE_LIMIT_BACKOFF_S * i for i in range(1, agent.RATE_LIMIT_RETRIES + 1))
    assert span >= 60.0


def test_the_client_script_actually_parses():
    """A brace-count is not a parser. An unterminated regex literal once shipped a script
    that died on load, taking the model switcher and the background with it, while every
    balance check still passed."""
    import shutil
    import subprocess

    from frontend import theme

    node = shutil.which("node")
    if not node:
        import pytest

        pytest.skip("node is not available to parse the script")
    result = subprocess.run(
        [node, "--check", str(theme.STATIC / "ui.js")],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr


def test_the_evidence_panel_no_longer_carries_the_environment_report():
    from physearth import session

    out = render.evidence(session.new_session("m"))
    assert "outbound host" not in out
    assert "What this instance actually is" not in out
    assert "Whole corpus" in out


def test_a_turn_can_speak_in_more_than_one_block():
    from physearth import agent as agent_module

    text = agent_module.transcript(["first thought", "second thought"], "third")
    out = render.answer_html(text, running=True)
    assert out.count("class='seg") == 3
    assert out.count("seg--later") == 2
    assert out.index("first thought") < out.index("second thought") < out.index("third")


def test_the_opening_hint_steps_aside_for_a_question_in_flight():
    assert "pane-empty" in render.history([])
    assert "pane-empty" not in render.history([], pending=True)


def test_the_optimistic_acknowledgement_leaves_output_slots_to_gradio():
    """Client feedback must not detach streamed HTML components from Gradio."""
    from frontend import theme

    js = theme.js()
    assert "optimisticSend" in js and "optimisticClear" in js

    # Sending clears the composer, but only after Gradio has read it.
    assert "setTimeout(function () {" in js
    assert 'box.value = ""' in js

    # Transcript, trace and approval content are authoritative server outputs. Mutating
    # their roots by hand makes later streamed frames invisible even though the run ends.
    assert ".innerHTML =" not in js
    assert "TRACE_EMPTY" not in js


def test_clear_is_wired_as_a_cancellation_boundary_for_streaming_send():
    """A reset must cancel the active generator before its next frame repaints the UI."""
    source = Path(__file__).resolve().parents[1].joinpath("frontend", "studio.py").read_text(encoding="utf-8")
    assert "send_event = send.click(respond, inputs, outputs)" in source
    assert "active_stream_events = [send_event]" in source
    assert "active_stream_events.append(resume_event)" in source
    assert "cancels=active_stream_events" in source
    assert "clear.click(" in source and "queue=False" in source


def test_the_run_trace_is_rebuilt_per_checkpoint_not_per_token(monkeypatch):
    """The trace changes on a checkpoint, not on a token.

    It used to be rebuilt and string-compared on every streamed chunk -- a few hundred
    milliseconds a turn, growing with the length of the trace, to produce HTML that was
    then thrown away because it had not changed. What the browser receives is the same;
    the work behind it is not.

    The assertion is about scaling rather than an absolute count, because a turn also
    renders the trace a fixed number of times outside the streaming loop: once for the
    pending layout, once to seed the comparison, once for the final frame.
    """
    from physearth import session as session_state

    from frontend import studio as app

    def renders_for(content_chunks):
        box = session_state.new_session(agent.default_model())
        state = session_state.new_state(box)
        state["phase"] = "calling_model"
        events = [{"kind": "model_call", "at": "00:00:00", "index": 1}]

        def fake_stream(*_args, **_kwargs):
            answer = ""
            for i in range(content_chunks):
                answer += "word%d " % i
                yield answer, events, state
            yield answer, events + [
                {"kind": "harness_pass", "at": "00:00:01", "index": 2}
            ], state

        rendered = []
        original = app.render.trace

        def counting_trace(*args, **kwargs):
            rendered.append(1)
            return original(*args, **kwargs)

        monkeypatch.setattr(app.agent, "stream", fake_stream)
        monkeypatch.setattr(app.render, "trace", counting_trace)
        list(app.respond("question", [], box, agent.default_model()))
        monkeypatch.undo()
        return len(rendered)

    few, many = renders_for(3), renders_for(60)
    assert few == many, (
        "the trace was rebuilt %d times for 3 tokens and %d times for 60: it still "
        "scales with content rather than with checkpoints" % (few, many)
    )
