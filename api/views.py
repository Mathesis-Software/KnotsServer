import json, re

from spherogram.links import Link
from spherogram.links.orthogonal import OrthogonalLinkDiagram

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .decorators import json_response
from .models import Knot

def code2diagram(code):
    # remove extra whitespaces
    code = ' '.join(code.split())
    # keep name for use in diagram json
    name = code

    # if code is known by database, replace it with dt code
    try:
        knot = Knot.objects.get(identifier=code.lower())
        code = knot.dtcode
    except:
        pass

    # replace sequence of integers by spherogram-supported DT code notation
    if re.match(r'^[-\d ]+$', code):
        code = 'DT:[(' + code.replace(' ', ',') + ')]'

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
        'name': name,
        'components': [{
            'vertices': [[index, pt[0], pt[1]] for (pt, index) in zip(points, range(len(points)))],
            'crossings': [{'down': c[0], 'up': c[1]} for c in crossings],
            'isClosed': True
        }]
    }

@require_POST
@csrf_exempt
@json_response
def diagram4Code(request):
    debug = False
    try:
        data = json.loads(request.body.decode("utf-8"))
        debug = data.get("debug") or False
        return code2diagram(data["code"])
    except Exception as error:
        if debug:
            return {'error': 'Internal error: %s' % error}
        else:
            return {'error': 'Cannot convert code to a diagram'}

@json_response
def test(request, code):
    try:
        return code2diagram(code)
    except Exception as error:
        return {'error': '%s' % error}
