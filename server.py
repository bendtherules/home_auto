import web
# import redis
# import csv
# import json
import time
# r = redis.StrictRedis(host='localhost', port=6379, db=0)

urls = [
    "/set", "set_params",
    "/get", "get_params",
    "/refresh", "get_all",
    "/confirm", "confirm_params"
]


class DataStore(object):

    """docstring for DataStore"""

    def __init__(self):
        super(DataStore, self).__init__()
        self._dict = {}

    def __setitem__(self, key, value):
        value = str(value)
        self.check_key(key)
        param_dict = self._dict[key]
        if param_dict["new_value"] != value:
            param_dict["confirmed"] = False
            param_dict["new_value"] = value

    def confirm(self, key, value):
        value = str(value)
        self.check_key(key)
        param_dict = self._dict[key]
        if param_dict["new_value"] == value:
            param_dict["confirmed"] = True

    def __getitem__(self, key):
        self.check_key(key)
        param_dict = self._dict[key]
        if (not param_dict["confirmed"]) and (param_dict["new_value"] is not None):
            return param_dict["new_value"]
        else:
            return None

    def check_key(self, key):
        if key not in self._dict:
            self._dict[key] = {"confirmed": False, "new_value": None}

    def get_modified(self):
        dict_modified = {}
        for key in self._dict:
            value = self[key]
            if value is not None:
                dict_modified[key] = value
        return dict_modified


def dict_to_response(_dict):
    str_response = ""
    for key in _dict:
        value = _dict[key]
        str_response += "=".join([key, value]) + " "
    str_response += "time=" + time.ctime().replace(" ", "-")
    str_response = "`" + str_response + "`"
    return str_response

data = DataStore()

data["a"] = 5
data["c"] = 45


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


# class refresh:

#     def GET(self):


if __name__ == "__main__":

    app = web.application(urls, globals())
    app.run()
