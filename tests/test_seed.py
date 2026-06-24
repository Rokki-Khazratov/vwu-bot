from sqlalchemy import func, select

from app.content.seed import seed_all
from app.modules.catalog.models import TaskBlueprint
from app.modules.evaluation.models import PerformanceBand, RubricCriterion
from app.modules.tasks.models import TaskInstance


async def test_seed_is_idempotent_and_complete(db):
    await seed_all(db)
    await seed_all(db)  # second run must not duplicate
    await db.commit()

    criteria = (await db.execute(select(func.count()).select_from(RubricCriterion))).scalar()
    assert criteria == 4

    bands = (await db.execute(select(func.count()).select_from(PerformanceBand))).scalar()
    assert bands == 24  # 4 criteria * 6 bands

    tasks = (await db.execute(select(TaskInstance))).scalars().all()
    assert len(tasks) == 2
    assert all(t.status == "active" for t in tasks)

    bp = (await db.execute(select(TaskBlueprint))).scalar_one()
    assert bp.rubric_id is not None
    assert bp.evaluation_profile_id is not None
