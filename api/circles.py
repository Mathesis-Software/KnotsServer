import itertools
from .CirclePack import CirclePack

def collect_data(link):
    face_id_to_obj = {}
    edge_to_face_id = {}
    for index, face in enumerate(link.faces()):
        face_id = 'f%s' % index
        face_id_to_obj[face_id] = face
        edge_to_face_id.update({strand: face_id for strand in face})

    edge_obj_to_id = {}
    edge_id_to_obj = {}
    oppos = set()
    for st in link.crossing_strands():
        if st in oppos:
            continue
        oppo = st.opposite()
        oppos.add(oppo)
        edge_id = 'e%s' % (len(edge_obj_to_id) // 2)
        edge_obj_to_id[st] = edge_id
        edge_obj_to_id[oppo] = edge_id
        edge_id_to_obj[edge_id] = st

    crossings = set(s[0] for s in link.crossing_strands())
    vert_obj_to_id = {crs: 'v%s' % (crs.label, ) for crs in crossings}

    initial_strand = link.crossing_strands()[0]
    strand = initial_strand
    route = []
    while True:
        edge = edge_obj_to_id[strand]
        vert = vert_obj_to_id[strand[0]]
        route.append({'id': edge})
        route.append({'id': vert, 'up': strand[1] % 2 == 0})
        strand = strand.next()
        if strand == initial_strand:
            break

    all_cycles = {}
    for face_id, face in face_id_to_obj.items():
        cycle = []
        for strand in face:
            cycle.append(edge_obj_to_id[strand])
            cycle.append(vert_obj_to_id[strand[0]])
        all_cycles[face_id] = cycle
    for edge, edge_id in edge_obj_to_id.items():
        oppo = edge.opposite()
        all_cycles[edge_id] = [
            vert_obj_to_id[edge[0]],
            edge_to_face_id[edge],
            vert_obj_to_id[oppo[0]],
            edge_to_face_id[oppo],
        ]
    for vert, vert_id in vert_obj_to_id.items():
        cycle = []
        for i in range(4):
            edge = (vert, i)
            cycle.append(edge_obj_to_id[edge])
            cycle.append(edge_to_face_id[edge])
        cycle.reverse()
        all_cycles[vert_id] = cycle

    return all_cycles, route

def is_vert(obj_id):
    return obj_id.startswith('v')
def is_edge(obj_id):
    return obj_id.startswith('e')
def is_face(obj_id):
    return obj_id.startswith('f')

def layout(all_cycles):
    best_cost = None
    for external_face_id in [f_id for f_id in all_cycles.keys() if is_face(f_id)]:
        levels = [{external_face_id}]
        all_levels = {external_face_id}
        while len(all_levels) < len(all_cycles):
            next_level = set()
            for obj_id in levels[-1]:
                for nbr in all_cycles[obj_id]:
                    if nbr not in all_levels:
                        next_level.add(nbr)
                        all_levels.add(nbr)
            levels.append(next_level)

        cost = [len(levels)] + [len(lev) for lev in reversed(levels)]
        if best_cost is None or cost < best_cost:
            best_cost = cost
            external_ids = all_cycles[external_face_id]
            internal_ids = [obj_id for obj_id in all_cycles.keys() if obj_id not in external_ids and obj_id != external_face_id]
            optimal = internal_ids, external_ids, levels, external_face_id
    return optimal

def diagram4link(link):
    all_cycles, route = collect_data(link)
    internal_ids, external_ids, levels, external_face_id = layout(all_cycles)

    external = {x_id: 1 if is_edge(x_id) else 1 for x_id in external_ids}
    internal = {obj_id: all_cycles[obj_id] for obj_id in internal_ids}
    pack = CirclePack(internal, external)

    max_distance = max(abs(c0[0] - c1[0]) for c0, c1 in itertools.combinations(pack.values(), 2))

    vertices = []
    up_crossings = {}
    down_crossings = {}

    def add_half_edge(key0, key1):
        c0 = pack[key0][0]
        c1 = pack[key1][0]
        r0 = pack[key0][1]
        r1 = pack[key1][1]

        if r0 + r1 >= max_distance / 5:
            ratio0 = r0 / (r0 + r1) * 2 / 3
            ratio1 = r1 / (r0 + r1) * 2 / 3
            pt0 = c1 * ratio0 + c0 * (1 - ratio0)
            pt1 = c0 * ratio1 + c1 * (1 - ratio1)
            return [pt0, pt1]
        else:
            ratio = r0 / (r0 + r1)
            pt = c1 * ratio + c0 * (1 - ratio)
            return [pt]

    for prev, curr in zip([route[-1]] + route, route + [route[0]]):
        for pt in add_half_edge(prev['id'], curr['id']):
            vertices.append((pt.real, pt.imag))
        if is_vert(curr['id']):
            if curr['up']:
                up_crossings[curr['id']] = len(vertices) - 1
            else:
                down_crossings[curr['id']] = len(vertices) - 1

    return (vertices, [(down_crossings[v], up_crossings[v]) for v in up_crossings.keys()])
