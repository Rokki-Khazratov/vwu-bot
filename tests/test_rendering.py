from bot.rendering.escaping import escape
from bot.rendering.renderer import (
    render_blocks,
    render_diagnosis_examples,
    render_history,
    render_profile,
    render_statistics,
    render_task,
    render_writing_feedback,
)
from bot.rendering.splitter import split_html

# Shape mirrors what the backend's writing engine actually emits.
FEEDBACK_BLOCKS = [
    {"type": "heading", "level": 1, "text": "Writing Result"},
    {"type": "status", "text": "Final score: 12 / 20"},
    {"type": "score_table", "headers": ["Criterion", "Score"],
     "rows": [["Task Achievement", "4/5"], ["Raw total", "14/20"]]},
    {"type": "paragraph", "role": "penalty_notice", "text": "Word-count penalty: 198 words → -2."},
    {"type": "criteria_table", "rows": [
        {"criterion": "Task Achievement", "score": 4, "explanation": "Все пункты раскрыты."},
    ]},
    {"type": "content_point_list", "items": [
        {"id": "cp_1", "status": "developed", "comment": "ок"},
    ]},
    {"type": "recommendation_list", "role": "recommendations", "items": ["Повторить времена."]},
    {"type": "error_list", "items": [
        {"category": "grammar", "severity": "minor", "before": "he go",
         "after": "he goes", "explanation": "3-е лицо."},
    ]},
]


def test_escape_neutralizes_html():
    assert escape("<b> & </b>") == "&lt;b&gt; &amp; &lt;/b&gt;"
    assert escape(None) == ""


def test_render_maps_each_block_type():
    html = render_blocks(FEEDBACK_BLOCKS)
    assert "<h1>Writing Result</h1>" in html
    assert "<table>" in html and "<th>Criterion</th>" in html
    assert "Word-count penalty" in html
    assert "<details><summary>Ошибки и исправления</summary>" in html
    assert "<s>he go</s> → <b>he goes</b>" in html
    assert "🟢" in html  # developed content point


def test_error_text_is_escaped():
    html = render_blocks([{"type": "error_list", "items": [
        {"category": "x", "severity": "minor", "before": "a<b", "after": "c&d",
         "explanation": "ok"},
    ]}])
    assert "a&lt;b" in html and "c&amp;d" in html
    assert "a<b" not in html


def test_feedback_fallback_without_blocks():
    html = render_writing_feedback({"score": {"final": 12, "max": 20}})
    assert "Результат" in html and "12" in html


def test_splitter_respects_limit():
    blocks = "\n\n".join(f"<p>block {i}</p>" for i in range(100))
    chunks = split_html(blocks, max_chars=50)
    assert len(chunks) > 1
    assert all(len(c) <= 50 for c in chunks)
    # nothing lost
    assert sum(c.count("<p>") for c in chunks) == 100


def test_splitter_single_message_when_small():
    assert split_html("<p>hi</p>", max_chars=100) == ["<p>hi</p>"]


def test_render_task_outputs_prompt_and_constraints():
    html = render_task({
        "title": "Living with parents",
        "content": {
            "source_post": {"author": "Jason", "body": "What should I do?"},
            "instruction": "Write a blog comment.",
            "target_words": 250,
        },
        "content_points": [{"instruction": "Give advice."}],
        "recommended_minutes": 40,
    })
    assert "<h1>Living with parents</h1>" in html
    assert "Jason" in html
    assert "Give advice." in html
    assert "250" in html and "40" in html


def test_render_history_includes_task_scores():
    html = render_history([
        {
            "task_title": "Task A",
            "status": "completed",
            "score_earned": 12,
            "score_max": 20,
            "top_errors": [{"category": "grammar", "count": 2}],
            "weakest_criterion": {
                "criterion_code": "accuracy",
                "score": 3,
                "max_score": 5,
            },
        }
    ])
    assert "Task A" in html
    assert "12 / 20" in html
    assert "grammar" in html
    assert "accuracy" in html


def test_render_profile_and_expanded_statistics():
    profile = render_profile({
        "me": {"telegram_id": 1, "status": "active", "display_name": "Rokki"},
        "overview": {"sessions_completed": 2, "average_percent": 70},
        "diagnosis": {
            "focus_items": [
                {"title": "Критерий: accuracy", "severity": "high"}
            ]
        },
        "weaknesses": [{"criterion_code": "accuracy", "weakness_score": 44}],
        "history": [{"task_title": "Blog", "score_earned": 14, "score_max": 20}],
    })
    assert "Профиль" in profile
    assert "Rokki" in profile
    assert "accuracy" in profile

    stats = render_statistics({
        "sessions_completed": 2,
        "tasks_evaluated": 2,
        "average_percent": 70,
        "criteria": [{"criterion_code": "accuracy", "avg_score": 3, "max_score": 5}],
        "repeated_errors": [{"category": "grammar", "count": 2}],
        "weaknesses": [{"criterion_code": "accuracy", "weakness_score": 44}],
        "diagnosis": {
            "focus_items": [
                {
                    "title": "Критерий: accuracy",
                    "severity": "high",
                    "recommended_action": {"label": "Тренировать этот критерий"},
                }
            ]
        },
    })
    assert "Проверено заданий" in stats
    assert "grammar" in stats
    assert "Что тренировать сейчас" in stats

    examples = render_diagnosis_examples(
        {
            "focus_items": [
                {
                    "title": "Повторяется ошибка: grammar",
                    "filters": {"error_category": "grammar"},
                    "sample_errors": [
                        {
                            "source_fragment": "he go",
                            "corrected_fragment": "he goes",
                            "criterion_code": "accuracy",
                        }
                    ],
                }
            ]
        },
        kind="error",
        value="grammar",
    )
    assert "he goes" in examples
