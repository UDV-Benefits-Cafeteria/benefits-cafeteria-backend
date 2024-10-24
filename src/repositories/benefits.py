from typing import Any, Optional, Union

from src.config import get_settings, logger
from src.models import Benefit
from src.repositories.abstract import SQLAlchemyRepository
from src.repositories.exceptions import EntityReadError
from src.utils.elastic_index import SearchService, es

settings = get_settings()


class BenefitsRepository(SQLAlchemyRepository[Benefit]):
    model = Benefit

    async def create(self, data: dict) -> Benefit:
        benefit = await super().create(data)
        await self.index_benefit(benefit)
        return benefit

    async def update_by_id(self, entity_id: Union[int, str], data: dict) -> bool:
        success = await super().update_by_id(entity_id, data)
        if success:
            benefit = await self.read_by_id(entity_id)
            if benefit:
                await self.index_benefit(benefit)
        return success

    async def delete_by_id(self, entity_id: Union[int, str]) -> bool:
        success = await super().delete_by_id(entity_id)
        if success:
            await self.delete_benefit_from_index(entity_id)
        return success

    async def index_benefit(self, benefit: Benefit):
        benefit_data = {
            "id": benefit.id,
            "name": benefit.name,
            "coins_cost": benefit.coins_cost,
            "min_level_cost": benefit.min_level_cost,
            "amount": benefit.amount,
            "is_active": benefit.is_active,
            "adaptation_required": benefit.adaptation_required,
            "real_currency_cost": benefit.real_currency_cost
            if benefit.real_currency_cost
            else None,
            "created_at": benefit.created_at.isoformat()
            if benefit.created_at
            else None,
            "category_id": benefit.category_id,
        }

        if benefit.image_primary and benefit.image_primary.image_url:
            benefit_data["primary_image_url"] = benefit.image_primary.image_url
        else:
            benefit_data["primary_image_url"] = None

        try:
            await es.index(
                index=SearchService.index_name, id=benefit.id, document=benefit_data
            )
        except Exception as e:
            logger.error(f"Error indexing benefit {benefit.id} in Elasticsearch: {e}")

    async def delete_benefit_from_index(self, benefit_id: int):
        try:
            await es.delete(index=SearchService.index_name, id=benefit_id)
        except Exception as e:
            logger.error(f"Error deleting benefit {benefit_id} from Elasticsearch: {e}")

    async def search_benefits(
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
                        "name^3",
                        "name._2gram^2",
                        "name._3gram",
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
                if field in [
                    "coins_cost",
                    "real_currency_cost",
                    "min_level_cost",
                    "created_at",
                ]:
                    bool_query["bool"]["filter"].append({"range": {field: value}})
                elif field == "category_id":
                    bool_query["bool"]["filter"].append({"terms": {field: value}})
                else:
                    # Bool fields
                    bool_query["bool"]["filter"].append({"term": {field: value}})
            es_query["query"] = bool_query
        else:
            es_query["query"] = base_query

        if sort_by:
            es_query["sort"] = [{sort_by: {"order": sort_order}}]

        try:
            response = await es.search(index=SearchService.index_name, body=es_query)
            hits = response["hits"]["hits"]
            results = [hit["_source"] for hit in hits]
            return results
        except Exception as e:
            logger.error(f"Error searching benefits in Elasticsearch: {e}")
            raise EntityReadError(self.model.__name__, "", str(e))
