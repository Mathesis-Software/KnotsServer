from django.http import Http404
from django.shortcuts import render

def error(request, exception):
    return page(request, 'error')

def page(request, page_id='root'):
    try:
        return render(request, page_id + '.html')
    except:
        raise Http404
