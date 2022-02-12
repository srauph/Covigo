# This probably isn't how you're supposed to create custom exceptions in Django.
# But it's the way I know how to do it, so I'll just do it this way until I find a better way.

class UserNotPatientNorStaffException(BaseException):
    def __init__(self):
        self.message = "User is neither staff nor patient"
        super().__init__(self.message)

class UserHasNoProfileException(BaseException):
    def __init__(self):
        self.message = "User does not have a profile"
        super().__init__(self.message)