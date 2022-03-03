class Dict2Obj:
    def __init__(self, dictionary):
        for key in dictionary:
            setattr(self, key, dictionary[key])

    def __repr__(self):
        """"""
        return "<Dict2Obj: %s>" % self.__dict__

    def __getitem__(self, key):
        return self.__dict__[key]
