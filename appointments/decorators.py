from django.http import HttpResponseForbidden
from functools import wraps

def doctor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'doctor':
            return HttpResponseForbidden("Access denied: Doctors only")
        return view_func(request, *args, **kwargs)
    return wrapper
