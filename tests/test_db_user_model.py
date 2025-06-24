import pytest
from app.src.database.models import User
from app.src.database.database import async_session
import sqlalchemy as sa
import uuid

@pytest.mark.asyncio
async def test_create_and_read_user():
    unique_email = f"dbtest_{uuid.uuid4()}@example.com"
    async with async_session() as session:
        # Create user
        user = User(email=unique_email, password="hashed", confirmed=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        # Read user
        result = await session.execute(sa.select(User).where(User.email == unique_email))
        user_db = result.scalar_one()
        assert user_db.email == unique_email
        assert user_db.role == "user"
        assert user_db.confirmed is True
