class User():

    def __init__(self, _id=None, name="", email="", profile_pic=""):
        self._id = _id
        self.name = name
        self.email = email
        self.profile_pic=profile_pic

        self.is_active = True
        self.is_authenticated = True
    
    def get_id(self):
        return self._id