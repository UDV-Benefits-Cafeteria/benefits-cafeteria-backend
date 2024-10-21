from elasticsearch import AsyncElasticsearch

from src.config import get_settings

settings = get_settings()
es = AsyncElasticsearch(
    hosts=(settings.ELASTIC_URL,),
    basic_auth=("elastic", settings.ELASTIC_PASSWORD),
)


class SearchService:
    index_name = "benefits"

    @classmethod
    async def create_index(cls):
        mapping = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "ru_en_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "russian_stop",
                                "russian_stemmer",
                                "english_stop",
                                "english_stemmer",
                            ],
                        }
                    },
                    "filter": {
                        "russian_stop": {"type": "stop", "stopwords": "_russian_"},
                        "russian_stemmer": {"type": "stemmer", "language": "russian"},
                        "english_stop": {"type": "stop", "stopwords": "_english_"},
                        "english_stemmer": {"type": "stemmer", "language": "english"},
                    },
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "name": {
                        "type": "search_as_you_type",
                        "analyzer": "ru_en_analyzer",
                        "search_analyzer": "ru_en_analyzer",
                        "max_shingle_size": 3,
                    },
                    "coins_cost": {"type": "integer"},
                    "min_level_cost": {"type": "integer"},
                    "amount": {"type": "integer"},
                    "primary_image_url": {"type": "keyword"},
                    "is_active": {"type": "boolean"},
                    "adaptation_required": {"type": "boolean"},
                    "real_currency_cost": {"type": "float"},
                    "available_from": {"type": "date"},
                    "available_by": {"type": "date"},
                }
            },
        }

        index_exists = await es.indices.exists(index=cls.index_name)
        if not index_exists:
            await es.indices.create(index=cls.index_name, body=mapping)
