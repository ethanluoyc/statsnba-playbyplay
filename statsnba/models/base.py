from mongoengine import Document, DictField, StringField


class StatsNBABaseDocument(Document):
    resource = StringField()
    parameters = DictField()
    resultSets = DictField()
    meta = {'allow_inheritance': True}

    @staticmethod
    def create_collection_proxy(collection):
        return type(collection, (StatsNBABaseDocument, ))

    def find(self):
        pass
