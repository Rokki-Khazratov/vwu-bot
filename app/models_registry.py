"""Imports every ORM model so ``Base.metadata`` is fully populated.

Used by Alembic autogenerate and by the test harness (``create_all``).
Add new model modules here as they are introduced.
"""

from app.core.database import Base  # noqa: F401
from app.modules.access import models as _access  # noqa: F401
from app.modules.catalog import models as _catalog  # noqa: F401
from app.modules.evaluation import models as _evaluation  # noqa: F401
from app.modules.llm import models as _llm  # noqa: F401
from app.modules.system import models as _system  # noqa: F401
from app.modules.tasks import models as _tasks  # noqa: F401
from app.modules.training import models as _training  # noqa: F401

__all__ = ["Base"]
