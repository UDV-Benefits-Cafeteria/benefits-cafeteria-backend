from typing import Any, Optional

from elasticsearch import AsyncElasticsearch
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.logger import repository_logger
from src.models.users import User
from src.repositories.base import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError
from src.utils.elastic_index import SearchService


class UsersRepository(SQLAlchemyRepository[User]):
    model = User

    def __init__(self, es_client: Optional[AsyncElasticsearch] = None):
        self.es = es_client

    async def create(self, session: AsyncSession, data: dict) -> User:
        user = await super().create(session, data)
        if self.es is not None:
            await self.index_user(user)
        return user

    async def update_by_id(
        self, session: AsyncSession, entity_id: int, data: dict
    ) -> bool:
        is_updated = await super().update_by_id(session, entity_id, data)
        if is_updated:
            user = await self.read_by_id(session, entity_id)
            if user and self.es is not None:
                await self.index_user(user)
        return is_updated

    async def delete_by_id(self, session: AsyncSession, entity_id: int) -> bool:
        is_deleted = await super().delete_by_id(session, entity_id)
        if is_deleted and self.es is not None:
            await self.delete_user_from_index(entity_id)
        return is_deleted

    async def index_user(self, user: User):
        repository_logger.info(f"Indexing created User with ID={user.id}")
        user_data = {
            "id": user.id,
            "email": user.email,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "middlename": user.middlename,
            "fullname": f"{user.lastname} {user.firstname} {user.middlename or ''}".strip(),
            "is_active": user.is_active,
            "is_adapted": user.is_adapted,
            "is_verified": user.is_verified,
            "coins": user.coins,
            "role": user.role.value,
            "hired_at": user.hired_at.isoformat(),
            "experience": user.experience,
            "level": user.level,
            "legal_entity_id": user.legal_entity_id,
            "position_id": user.position_id,
            "image_url": user.image_url,
        }

        await self.es.index(
            index=SearchService.users_index_name,
            id=user.id,
            document=user_data,
            refresh=True,
        )
        repository_logger.info(f"Successfully indexed User with ID={user.id}")

    async def search_users(
        self,
        query: Optional[str],
        filters: Optional[dict] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        limit: int = 10,
        offset: int = 0,
    ) -> list[dict]:
        es_query: dict[str, Any] = {
            "from": offset,
            "size": limit,
        }
        repository_logger.info(
            f"Searching Users: query='{query}', filters={filters}, sort_by={sort_by}, "
            f"sort_order={sort_order}, limit={limit}, offset={offset}"
        )

        if query:
            base_query = {
                "multi_match": {
                    "query": query,
                    "type": "bool_prefix",
                    "fields": [
                        "fullname^4",
                        "fullname._2gram^3",
                        "fullname._3gram^2",
                    ],
                    "fuzziness": "AUTO",
                }
            }
        else:
            base_query = {"match_all": {}}

        if filters:
            bool_query = {
                "bool": {
                    "must": base_query,
                    "filter": [],
                }
            }
            for field, value in filters.items():
                if field == "hired_at":
                    bool_query["bool"]["filter"].append({"range": {field: value}})
                elif field in ["legal_entity_id", "role"]:
                    bool_query["bool"]["filter"].append({"terms": {field: value}})
                else:
                    bool_query["bool"]["filter"].append({"term": {field: value}})
            es_query["query"] = bool_query
        else:
            es_query["query"] = base_query

        if sort_by:
            if sort_by == "fullname":
                sort_field = "fullname.keyword"
            else:
                sort_field = sort_by
            es_query["sort"] = [{sort_field: {"order": sort_order}}]

        try:
            response = await self.es.search(
                index=SearchService.users_index_name, body=es_query
            )
            hits = response["hits"]["hits"]
            results = [hit["_source"] for hit in hits]
        except Exception as e:
            repository_logger.error(
                f"Error searching Users: query='{query}', filters={filters}, sort_by={sort_by}, "
                f"sort_order={sort_order}, limit={limit}, offset={offset}: {e}"
            )
            raise EntityReadError(
                self.__class__.__name__, self.model.__tablename__, str(filters), str(e)
            )

        repository_logger.info(f"Found {len(results)} Users matching query: {query}")
        return results

    async def delete_user_from_index(self, user_id: int):
        repository_logger.info(f"Deleting User from index: ID={user_id}")
        await self.es.delete(
            index=SearchService.users_index_name, id=str(user_id), refresh=True
        )
        repository_logger.info(f"Successfully deleted User from index: ID={user_id}")

    async def read_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """
        Retrieve a User entity by email.

        Args:
            session: SQLAlchemy AsyncSession.
            email: The email of the user to retrieve.

        Returns:
            A User entity if found, otherwise None.

        Raises:
            EntityReadError: If an error occurs while reading the entity.
        """
        repository_logger.info(f"Fetching {self.model.__name__} with email: {email}.")

        try:
            result = await session.execute(
                select(self.model).where(self.model.email == email)
            )
            user = result.scalar_one_or_none()
        except Exception as e:
            repository_logger.error(
                f"Error fetching {self.model.__name__} with email: {email} - {e}"
            )
            raise EntityReadError(
                self.__class__.__name__,
                self.model.__tablename__,
                f"email: {email}",
                str(e),
            )

        if user:
            repository_logger.info(
                f"Successfully fetched {self.model.__name__} with email: {email}."
            )
        else:
            repository_logger.warning(
                f"No {self.model.__name__} found with email: {email}."
            )
        return user
