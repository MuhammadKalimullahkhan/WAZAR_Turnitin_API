class BaseClass(Exception): 
    def __init__(self, message=None, code=None):
        super().__init__(message)
        self.message=message
        self.code = code

    def __repr__(self) -> str:
        return f"Code: {self.code}, Message: {self.message}"

    def __str__(self) -> str:
        return f"{self.message}"
    

class ClassNotFound(BaseClass):
    pass