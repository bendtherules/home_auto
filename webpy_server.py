import web
# import redis
# import csv
# import json
import time
# r = redis.StrictRedis(host='localhost', port=6379, db=0)
from pymongo import MongoClient

urls = [
    "/set", "set_params",
    "/get", "get_params",
    "/refresh", "get_all",
    "/confirm", "confirm_params"
]


dms_client = MongoClient('localhost', 27017, connect=True)
db = dms_client.test_database
db_states = db["device_states"]


class DataStore(object):

    """docstring for DataStore"""

    def __init__(self):
        super(DataStore, self).__init__()
        self.db_id = db_states.insert_one({}).inserted_id

    def __setitem__(self, key, value):
        key, value = unicode(key), unicode(value)
        # self.check_key(key)
        update = True
        param_old_wrapper_dict = db_states.find_one({"_id": self.db_id, key: {"$exists": True}}, {"_id": 0, key: 1})
        if param_old_wrapper_dict:
            param_old_dict = param_old_wrapper_dict[key]
            if param_old_dict["new_value"] == value:
                update = False

        if update is True:
            db_states.update_one(filter={"_id": self.db_id},
                                 update={"$set": {key: {"confirmed": False, "new_value": value}}})

    def confirm(self, key, value):
        key, value = unicode(key), unicode(value)
        param_wrapper_dict = db_states.find_one({"_id": self.db_id, key: {"$exists": True}}, {"_id": 0, key: 1})
        if param_wrapper_dict:
            param_dict = param_wrapper_dict[key]
            if param_dict["new_value"] == value:
                db_states.find_one_and_update(filter={"_id": self.db_id, key: {"$exists": True}},
                                              update={"$set": {key + ".confirmed": True}})

    def __getitem__(self, key):
        key = unicode(key)
        param_wrapper_dict = db_states.find_one({"_id": self.db_id, key: {"$exists": True}}, {"_id": 0, key: 1})
        if param_wrapper_dict:
            param_dict = param_wrapper_dict[key]
            if (not param_dict["confirmed"]) and (param_dict["new_value"] is not None):
                return param_dict["new_value"]
        return None

    def check_key(self, key):
        # todo: is needed ??
        if key not in self._dict:
            self._dict[key] = {"confirmed": False, "new_value": None}

    def get_modified(self):
        dict_modified = {}
        param_wrapper_dict = db_states.find_one({"_id": self.db_id}, {"_id": 0})

        for key in param_wrapper_dict:
            param_dict = param_wrapper_dict[key]
            confirmed = param_dict["confirmed"]
            value = param_dict["new_value"]
            if (not confirmed) and (value is not None):
                dict_modified[key] = value
        return dict_modified


def dict_to_response(_dict):
    str_response = ""
    for key in _dict:
        value = _dict[key]
        str_response += "=".join([key, value]) + " "
    str_response += "time=" + time.ctime().replace(" ", "-") + " "
    str_response = "`" + str_response + "`"
    return str_response

data = DataStore()

data["a"] = 5
data["c"] = 45
data.get_modified()


class get_params:

    def GET(self):
        global data
        print("Sending data back")
        print(data._dict)
        return dict_to_response(data.get_modified())


class set_params:

    def GET(self):
        dict_input = dict(web.input())
        for key in dict_input:
            value = dict_input[key]
            data[key] = value


class get_all:

    def GET(self):
        dict_all = {}
        for key in data._dict:
            value = data._dict[key]["new_value"]
            if value is not None:
                dict_all[key] = value
        return dict_to_response(dict_all)


class confirm_params(object):

    def GET(self):
        dict_input = dict(web.input())
        for key in dict_input:
            value = dict_input[key]
            data.confirm(key, value)


app = web.application(urls, globals())
app_wsgi_func = app.wsgifunc()

if __name__ == "__main__":

    app.run()
