from django.shortcuts import render

def page(request, page_id='root'):
    return render(request, page_id + '.html')
