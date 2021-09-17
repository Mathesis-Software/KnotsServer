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

def link2diagram(link, name):
    points, crossings = diagram4link_circles(link)

    maxX = max(p[0] for p in points)
    maxY = max(p[1] for p in points)
    minX = min(p[0] for p in points)
    minY = min(p[1] for p in points)
    points = [
        (int((p[0] - minX) / (maxX - minX) * 400 + 50),
         int((p[1] - minY) / (maxY - minY) * 400 + 50)) for p in points]

    return {
        'type': 'diagram',
        'name': name,
        'components': [{
            'vertices': [[index, pt[0], pt[1]] for (index, pt) in enumerate(points)],
            'crossings': [{'down': c[0], 'up': c[1]} for c in crossings],
            'isClosed': True
        }]
    }

def validate_letter_dt_code(code):
    if not re.match(r'^[a-zA-Z]+$', code):
        return None

    letters = set()
    for let in code:
        if ord(let.lower()) - ord('a') >= len(code):
            return None
            #raise ManagedException('Letter DT code error: %s is out of range A..%s' % (let, chr(ord('A') + len(code) - 1)))
        if let.lower() in letters:
            return None
            #raise ManagedException('Letter DT code error: duplicate %s' % let)
        letters.add(let.lower())

    def num(letter):
        return ord(letter) - ord('a') + 1 if letter.islower() else ord('A') - ord(letter) - 1
    return 'DT:[(' + ','.join([str(2 * num(letter)) for letter in code]) + ')]'

def validate_numeric_dt_code(code):
    if not re.match(r'^[-0-9 ]+$', code):
        return None

    try:
        intcode = [int(part) for part in code.split()]
    except:
        return None
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
    return 'DT:[(' + code.replace(' ', ',') + ')]'

def code2diagrams(code):
    # remove extra whitespaces
    code = ' '.join(code.split())
    # keep name for use in diagram json
    name = code

    # letter DT code
    validated = validate_letter_dt_code(code)

    if validated is None:
        # numeric DT code
        validated = validate_numeric_dt_code(code)

    if validated is None:
        # if code is regognized as knot name, extract letter DT code
        try:
            validated = validate_letter_dt_code(Knot.objects.get(identifier=code.lower()).dtcode)
        except:
            pass

    layouts = []

    try:
        # Last resort: maybe, spherogram know the knot name
        link = Link(validated if validated else name)
    except:
        raise ManagedException(f'No diagram found for `{name}`')

    try:
        layouts.append(link2diagram(link, name))
    except:
        raise ManagedException(f'Layout error for diagram `{name}`')

    return layouts

@require_POST
@csrf_exempt
@json_response
def diagram4Code(request):
    debug = False
    try:
        data = json.loads(request.body.decode('utf-8'))
        debug = data.get('debug') or False
        page = data['page']
        return {
            'layouts': code2diagrams(data['code']),
            'hasNextPage': False
        }
    except ManagedException as error:
        return {'error': '%s' % error}
    except Exception as error:
        if debug:
            return {'error': '%s' % error}
        else:
            return {'error': 'Diagram search error'}

@json_response
def test(request, code):
    try:
        return {'layouts': code2diagrams(code)}
    except Exception as error:
        return {'error': '%s' % error}
