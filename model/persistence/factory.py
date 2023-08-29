from model.persistence.core import IYtVideoRepository
from model.persistence.mongo import YtVideoMongoRepository


class YtVideoRepositoryFactory:
    @staticmethod
    def mongo_repository(db_name: str, collection_name: str) -> IYtVideoRepository:
        import pymongo

        from config_data_provider import get_mongo_db_url

        client = pymongo.MongoClient(get_mongo_db_url())
        db = client[db_name]
        collection = db[collection_name]
        return YtVideoMongoRepository(collection)
