from django.http import HttpResponseForbidden

def doctor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'doctor'):
            return HttpResponseForbidden("Access denied: Doctors only")
        return view_func(request, *args, **kwargs)
    return wrapper