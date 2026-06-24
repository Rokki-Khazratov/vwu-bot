from app.content.seed import seed_all
from app.modules.tasks.generation import generate_tasks
from tests._fakes import VALID_GENERATION, FakeProvider


async def test_generate_creates_task(db):
    await seed_all(db)
    provider = FakeProvider(VALID_GENERATION)

    tasks = await generate_tasks(
        db, provider, blueprint_code="epe_b1_plus_blog_comment_v1", count=1
    )
    assert len(tasks) == 1
    task = tasks[0]
    assert task.status == "generated"
    assert len(task.content_points) == 3
    assert task.content["source_post"]["author"] == "Tom"


async def test_generate_skips_exact_duplicate(db):
    await seed_all(db)
    provider = FakeProvider(VALID_GENERATION)

    first = await generate_tasks(db, provider, blueprint_code="epe_b1_plus_blog_comment_v1")
    assert len(first) == 1
    # Same canned draft -> same checksum -> skipped.
    second = await generate_tasks(db, provider, blueprint_code="epe_b1_plus_blog_comment_v1")
    assert second == []
