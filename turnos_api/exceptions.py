from rest_framework.exceptions import APIException

class CustomAPIException(APIException):
    def __init__(self, detail, status_code):
        self.status_code= status_code
        self.detail = {
            "success": False,
            "message": detail
        }