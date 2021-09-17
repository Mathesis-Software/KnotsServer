import json, re

from spherogram.links import Link

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .decorators import json_response
from .models import Knot

from .circles import diagram4link as diagram4link_circles
from .ortho import diagram4link as diagram4link_ortho

class ManagedException(Exception):
    pass

def code2diagram(code):
    # remove extra whitespaces
    code = ' '.join(code.split())
    # keep name for use in diagram json
    name = code

    # DT code validation
    if re.match(r'^[a-zA-Z]+$', code):
        # letter DT code
        letters = set()
        for let in code:
            if ord(let.lower()) - ord('a') >= len(code):
                raise ManagedException('Letter DT code error: %s is out of range A..%s' % (let, chr(ord('A') + len(code) - 1)))
            if let.lower() in letters:
                raise ManagedException('Letter DT code error: duplicate %s' % let)
            letters.add(let.lower())

    elif re.match(r'^[-\d ]+$', code):
        # numeric DT code
        intcode = [int(num) for num in code.split()]
        indices = set()
        for num in intcode:
            if num == 0:
                raise ManagedException('Numeric DT code error: 0 occured')
            if num % 2 == 1:
                raise ManagedException('Numeric DT code error: odd %d occured' % num)
            if abs(num) in indices:
                raise ManagedException('Numeric DT code error: duplicate %d' % num)
            max_value = 2 * len(intcode)
            if abs(num) > max_value:
                raise ManagedException('Numeric DT code error: %d is out of range -%d..%d' % (num, max_value, max_value))
            indices.add(abs(num))

    # if code is regognized as knot name, replace it with dt code
    try:
        knot = Knot.objects.get(identifier=code.lower())
        code = knot.dtcode
    except:
        pass

    if re.match(r'^[a-zA-Z]+$', code):
        # replace letter DT code by spherogram-supported DT code notation
        def num(letter):
            return ord(letter) - ord('a') + 1 if letter.islower() else ord('A') - ord(letter) - 1
        code = 'DT:[(' + ','.join([str(2 * num(letter)) for letter in code]) + ')]'
    elif re.match(r'^[-\d ]+$', code):
        # replace sequence of integers by spherogram-supported DT code notation
        code = 'DT:[(' + code.replace(' ', ',') + ')]'

    link = Link(code)
    layouts = []

    for diagram4link in diagram4link_circles, diagram4link_ortho:
        points, crossings = diagram4link(link)

        maxX = max(p[0] for p in points)
        maxY = max(p[1] for p in points)
        minX = min(p[0] for p in points)
        minY = min(p[1] for p in points)
        points = [
            (int((p[0] - minX) / (maxX - minX) * 400 + 50),
             int((p[1] - minY) / (maxY - minY) * 400 + 50)) for p in points]

        layouts.append({
            'type': 'diagram',
            'name': name,
            'components': [{
                'vertices': [[index, pt[0], pt[1]] for (index, pt) in enumerate(points)],
                'crossings': [{'down': c[0], 'up': c[1]} for c in crossings],
                'isClosed': True
            }]
        })

    return {'layouts': layouts}

@require_POST
@csrf_exempt
@json_response
def diagram4Code(request):
    debug = False
    try:
        data = json.loads(request.body.decode('utf-8'))
        debug = data.get('debug') or False
        page = data['page']
        response = code2diagram(data['code'])
        response['hasNextPage'] = False
        return response
    except ManagedException as error:
        return {'error': '%s' % error}
    except Exception as error:
        if debug:
            return {'error': '%s' % error}
        else:
            return {'error': 'Cannot convert code to a diagram'}

@json_response
def test(request, code):
    try:
        return code2diagram(code)
    except Exception as error:
        return {'error': '%s' % error}
