from elasticsearch import AsyncElasticsearch

from src.config import get_settings

settings = get_settings()
es = AsyncElasticsearch(
    hosts=(settings.ELASTIC_URL,),
    basic_auth=("elastic", settings.ELASTIC_PASSWORD),
)


class SearchService:
    benefits_index_name = "benefits"
    users_index_name = "users"

    @classmethod
    async def create_benefits_index(cls):
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
                    "created_at": {"type": "date"},
                    "category_id": {"type": "integer"},
                }
            },
        }

        benefits_index_exists = await es.indices.exists(index=cls.benefits_index_name)
        if not benefits_index_exists:
            await es.indices.create(index=cls.benefits_index_name, body=mapping)

    @classmethod
    async def create_users_index(cls):
        mapping = {
            "settings": {
                "analysis": {
                    "analyzer": {
                        "fullname_analyzer": {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                            ],
                        }
                    },
                }
            },
            "mappings": {
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "keyword", "index": False},
                    "firstname": {"type": "text", "index": False},
                    "lastname": {"type": "text", "index": False},
                    "middlename": {"type": "text", "index": False},
                    "fullname": {
                        "type": "search_as_you_type",
                        "analyzer": "fullname_analyzer",
                        "search_analyzer": "fullname_analyzer",
                        "fields": {"keyword": {"type": "keyword"}},
                    },
                    "is_active": {"type": "boolean"},
                    "is_adapted": {"type": "boolean"},
                    "is_verified": {"type": "boolean"},
                    "role": {"type": "keyword"},
                    "hired_at": {"type": "date"},
                    "experience": {"type": "integer", "index": False},
                    "level": {"type": "integer", "index": False},
                    "legal_entity_id": {"type": "integer"},
                    "position_id": {"type": "integer", "index": False},
                    "image_url": {"type": "keyword", "index": False},
                }
            },
        }
        users_index_exists = await es.indices.exists(index=cls.users_index_name)
        if not users_index_exists:
            await es.indices.create(index=cls.users_index_name, body=mapping)
