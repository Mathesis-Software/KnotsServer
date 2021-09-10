from django.http import JsonResponse
from django.shortcuts import render

from spherogram.links import Link
from spherogram.links.orthogonal import OrthogonalLinkDiagram

def code2diagram(code):
    link = Link(code)
    diagram = OrthogonalLinkDiagram(link)
    data = diagram.plink_data()
    points = data[0]
    maxX = max(p[0] for p in points)
    maxY = max(p[1] for p in points)
    minX = min(p[0] for p in points)
    minY = min(p[1] for p in points)
    points = [
        (int((p[0] - minX) / (maxX - minX) * 400 + 50),
         int((p[1] - minY) / (maxY - minY) * 400 + 50)) for p in points]
    crossings = data[2]

    return {
        'type': 'diagram',
        'name': 'Generated',
        'components': [{
            'vertices': [[index, pt[0], pt[1]] for (pt, index) in zip(points, range(len(points)))],
            'crossings': [{'down': c[0], 'up': c[1]} for c in crossings],
            'isClosed': True
        }]
    }

def index(request, code):
    try:
        return JsonResponse(code2diagram(code))
    except:
        return JsonResponse({'error': 'Invalid DT code'})
