# In views.py
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("200 OK", status=200)
