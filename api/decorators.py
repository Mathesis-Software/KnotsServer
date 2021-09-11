from django.http import JsonResponse

class json_response:
    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return JsonResponse(self.func(*args, **kwargs))
