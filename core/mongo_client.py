from pymongo import MongoClient
from pymongo.errors import PyMongoError

class MongoClientWrapper:
    def __init__(self):
        self.client = None

    def connect(self, ip, port, db, login, password, tls):
        try:
            if login and password:
                uri = f"mongodb://{login}:{password}@{ip}:{port}/{db}"
            else:
                uri = f"mongodb://{ip}:{port}/{db}"
            options = {}
            if tls:
                options["tls"] = True
            self.client = MongoClient(uri, **options)
            return True, "Connected successfully"
        except PyMongoError as e:
            return False, str(e)

    def run_query(self, db_name, collection_name, query_dict):
        try:
            db = self.client[db_name]
            collection = db[collection_name]
            results = list(collection.find(query_dict))
            return True, results
        except Exception as e:
            return False, str(e)

    def run_aggregate(self, db_name, collection_name, pipeline):
        try:
            db = self.client[db_name]
            collection = db[collection_name]
            results = list(collection.aggregate(pipeline))
            return True, results
        except Exception as e:
            return False, str(e)