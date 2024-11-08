from typing import Any, Optional

from sqlalchemy import select

from src.config import logger
from src.db.db import async_session_factory
from src.models.users import User
from src.repositories.abstract import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError
from src.utils.elastic_index import SearchService, es


class UsersRepository(SQLAlchemyRepository[User]):
    model = User

    async def create(self, data: dict) -> User:
        user = await super().create(data)
        await self.index_user(user)
        return user

    async def update_by_id(self, entity_id: int, data: dict) -> bool:
        success = await super().update_by_id(entity_id, data)
        if success:
            user = await self.read_by_id(entity_id)
            if user:
                await self.index_user(user)
        return success

    async def delete_by_id(self, entity_id: int) -> bool:
        success = await super().delete_by_id(entity_id)
        if success:
            await self.delete_user_from_index(entity_id)
        return success

    async def index_user(self, user: User):
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

        try:
            await es.index(
                index=SearchService.users_index_name, id=user.id, document=user_data
            )
        except Exception as e:
            logger.error(f"Error indexing user {user.id} in Elasticsearch: {e}")

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
            response = await es.search(
                index=SearchService.users_index_name, body=es_query
            )
            hits = response["hits"]["hits"]
            results = [hit["_source"] for hit in hits]
            return results
        except Exception as e:
            logger.error(f"Error searching users in Elasticsearch: {e}")
            raise EntityReadError(self.model.__name__, "", str(e))

    async def delete_user_from_index(self, user_id: int):
        try:
            await es.delete(index=SearchService.users_index_name, id=user_id)
        except Exception as e:
            logger.error(f"Error deleting user {user_id} from Elasticsearch: {e}")

    async def read_by_email(self, email: str) -> Optional[User]:
        async with async_session_factory() as session:
            try:
                result = await session.execute(
                    select(self.model).where(self.model.email == email)
                )
                user = result.scalar_one_or_none()

                if user:
                    logger.info(f"Found User with email: {email}")
                else:
                    logger.warning(f"No User found with email: {email}")

                return user

            except Exception as e:
                logger.error(f"Error reading User by email '{email}': {e}")
                raise EntityReadError(self.model.__name__, email, str(e))
