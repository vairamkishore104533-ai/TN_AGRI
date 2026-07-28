from datetime import datetime
import threading
import uuid

class ObjectId:
    def __init__(self, oid=None):
        self.oid = oid if oid else str(uuid.uuid4()).replace("-", "")[:24]
    def __str__(self):
        return self.oid
    def __repr__(self):
        return f"ObjectId('{self.oid}')"

class MockCollection:
    def __init__(self, name):
        self.name = name
        self._docs = {}
        self._lock = threading.Lock()
        self._counter = 0

    def _new_id(self):
        self._counter += 1
        return ObjectId()

    def insert_one(self, data):
        doc = dict(data)
        doc["_id"] = self._new_id()
        with self._lock:
            self._docs[str(doc["_id"])] = doc
        return type("InsertResult", (), {"inserted_id": doc["_id"]})()

    def find_one(self, query):
        with self._lock:
            for doc in self._docs.values():
                if self._matches(doc, query):
                    return dict(doc)
        return None

    def find(self, query=None):
        query = query or {}
        with self._lock:
            results = [dict(d) for d in self._docs.values() if self._matches(d, query)]
        return MockCursor(results)

    def find_one_and_update(self, query, update):
        with self._lock:
            for doc in self._docs.values():
                if self._matches(doc, query):
                    if "$set" in update:
                        doc.update(update["$set"])
                    return dict(doc)
        return None

    def update_one(self, query, update):
        modified = 0
        with self._lock:
            for doc in self._docs.values():
                if self._matches(doc, query):
                    for op, val in update.items():
                        if op == "$set":
                            doc.update(val)
                        elif op == "$push":
                            for key, value in val.items():
                                if key not in doc:
                                    doc[key] = []
                                doc[key].append(value)
                    modified = 1
                    break
        return type("UpdateResult", (), {"modified_count": modified})()

    def update_many(self, query, update):
        modified = 0
        with self._lock:
            for doc in self._docs.values():
                if self._matches(doc, query):
                    if "$set" in update:
                        doc.update(update["$set"])
                    modified += 1
        return type("UpdateResult", (), {"modified_count": modified})()

    def delete_one(self, query):
        deleted = 0
        with self._lock:
            for oid in list(self._docs.keys()):
                if self._matches(self._docs[oid], query):
                    del self._docs[oid]
                    deleted = 1
                    break
        return type("DeleteResult", (), {"deleted_count": deleted})()

    def delete_many(self, query):
        deleted = 0
        with self._lock:
            for oid in list(self._docs.keys()):
                if self._matches(self._docs[oid], query):
                    del self._docs[oid]
                    deleted += 1
        return type("DeleteResult", (), {"deleted_count": deleted})()

    def count_documents(self, query=None):
        query = query or {}
        with self._lock:
            return sum(1 for d in self._docs.values() if self._matches(d, query))

    def aggregate(self, pipeline):
        return []

    def _matches(self, doc, query):
        if not query:
            return True
        for key, value in query.items():
            if isinstance(value, dict):
                for op, val in value.items():
                    if op == "$gte":
                        if doc.get(key, "") < val:
                            return False
                    elif op == "$regex":
                        import re
                        if not re.search(val, str(doc.get(key, ""))):
                            return False
                    elif op == "$in":
                        if doc.get(key) not in val:
                            return False
            else:
                if key == "_id":
                    if str(doc.get("_id")) != str(value):
                        return False
                elif doc.get(key) != value:
                    return False
        return True

class MockCursor:
    def __init__(self, results):
        self._results = results
        self._idx = 0

    def sort(self, key, direction=-1):
        if isinstance(key, str):
            self._results.sort(key=lambda x: x.get(key, ""), reverse=(direction == -1))
        return self

    def limit(self, n):
        self._results = self._results[:n]
        return self

    def __iter__(self):
        return iter(self._results)

    def __len__(self):
        return len(self._results)

class MockDB:
    def __init__(self):
        self.db = self
        self._collections = {}

    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattribute__(name)
        if name not in self._collections:
            self._collections[name] = MockCollection(name)
        return self._collections[name]

    def __getitem__(self, name):
        if name not in self._collections:
            self._collections[name] = MockCollection(name)
        return self._collections[name]
