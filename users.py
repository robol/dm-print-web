import json

class User():

    def __init__(self, *args):
        if len(args) == 1:
            self._id = args[0]["id"]
            self._name = args[0]["name"]
            self.email = args[0]["email"]
            self.profile_pic = args[0]["profile_pic"]
        else:
            self._id = args[0]
            self.name = args[1]
            self.email = args[2]
            self.profile_pic = args[3]

        self.is_active = True
        self.is_authenticated = True
    
    def get_id(self):
        return self._id

    def to_json(self):
        return json.dumps({
            "id": self._id, 
            "name": self.name, 
            "email": self.email,
            "profile_pic": self.profile_pic
        })

    