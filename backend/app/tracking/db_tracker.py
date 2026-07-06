from sqlalchemy.orm import Session

from .. import models


class DBClickTracker:
    """Writes clicks to the Postgres `clicks` table. The default/always-on tracker."""

    name = "db"

    def __init__(self, db: Session):
        self.db = db

    async def record_click(self, *, link_id: int, ip_address: str | None,
                            user_agent: str | None, referrer: str | None,
                            metadata: dict | None = None) -> None:
        click = models.Click(
            link_id=link_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            device_metadata=metadata or {},
        )
        self.db.add(click)
        self.db.commit()
