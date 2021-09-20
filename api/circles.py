import itertools, math
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
        route.append({'id': vert, 'up': strand[1] % 2 == 0, 'prev': edge})
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

    def replace(lst, elt, repl):
        index = lst.index(elt)
        return lst[:index] + repl + lst[index + 1:]

    def extend_x(x_id, nbr01, nbr10):
        nonlocal external_ids, internal_ids, route
        neighbours = all_cycles[x_id]
        index = neighbours.index(nbr01)
        neighbours = neighbours[index:] + neighbours[:index]

        index01 = 0
        index10 = neighbours.index(nbr10)

        num = 2
        new_xs = [f'{x_id}_{index}' for index in range(num)]

        del all_cycles[x_id]
        all_cycles[new_xs[0]] = [neighbours[0], new_xs[1]] + neighbours[index10:]
        all_cycles[new_xs[1]] = neighbours[:index10 + 1] + [new_xs[0]]

        for index, nbr in enumerate(neighbours):
            if index == index01:
                replacement = new_xs[::-1]
            elif index in range(index01 + 1, index10):
                replacement = [new_xs[1]]
            elif index == index10:
                replacement = new_xs
            else:
                replacement = [new_xs[0]]
            all_cycles[nbr] = replace(all_cycles[nbr], x_id, replacement)

        if x_id in external_ids:
            external_ids.remove(x_id)
            external_ids += new_xs
        else:
            internal_ids.remove(x_id)
            internal_ids += new_xs

        while True:
            inds = [index for index, elt in enumerate(route) if elt['id'] == x_id]
            if not inds:
                break
            index = inds[0]
            def copy(new_id):
                elt = dict(route[index])
                elt['id'] = new_id
                return elt
            replacement = [copy(xx_id) for xx_id in new_xs]
            prev = route[index - 1]['id']
            if new_xs[-1] in all_cycles[prev]:
                replacement = replacement[::-1]
            route = replace(route, route[index], replacement)

    def extend_vert(vert_id, face_along):
        nbrs = all_cycles[vert_id]
        return extend_x(vert_id, face_along, nbrs[nbrs.index(face_along) - 4])

    small_faces = []
    for obj_id, cycle in all_cycles.items():
        if is_face(obj_id) and len(cycle) == 4:
            small_faces.append(obj_id)

    vert_to_face = {}
    for face_id in small_faces:
        for nbr in all_cycles[face_id]:
            if is_vert(nbr):
                vert_to_face[nbr] = face_id

    for nbr in all_cycles[external_face_id]:
        if is_vert(nbr):
            vert_to_face[nbr] = external_face_id

    for v, f in vert_to_face.items():
        extend_vert(v, f)

    external = {x_id: 1 if is_edge(x_id) else 1 for x_id in external_ids}
    internal = {obj_id: all_cycles[obj_id] for obj_id in internal_ids}
    pack = CirclePack(internal, external)

    max_distance = max(abs(c0[0] - c1[0]) for c0, c1 in itertools.combinations(pack.values(), 2))

    vertices = []
    up_crossings = {}
    down_crossings = {}

    rot = pow(math.e, complex(0, 1/6))
    def add_half_edge(elt0, elt1):
        key0 = elt0['id']
        key1 = elt1['id']
        c0, r0 = pack[key0]
        c1, r1 = pack[key1]

        if is_vert(key0) and is_vert(key1):
            ratio0 = r0 / (r0 + r1) * 1 / 2
            ratio1 = r1 / (r0 + r1) * 1 / 2
            pt0 = c1 * ratio0 + c0 * (1 - ratio0)
            pt1 = c0 * ratio1 + c1 * (1 - ratio1)
            nbs = [x_id for x_id in all_cycles[key0] if not is_face(x_id)]
            if (nbs.index(key1) - nbs.index(elt0['prev'])) in [1, -2]:
                pt0 = c1 + (pt0 - c1) * rot.conjugate()
                pt1 = c0 + (pt1 - c0) * rot.conjugate()
            else:
                pt0 = c1 + (pt0 - c1) * rot
                pt1 = c0 + (pt1 - c0) * rot
            return [pt0, pt1]
        elif r0 + r1 >= max_distance / 5:
            ratio0 = r0 / (r0 + r1) * 2 / 3
            ratio1 = r1 / (r0 + r1) * 2 / 3
            pt0 = c1 * ratio0 + c0 * (1 - ratio0)
            pt1 = c0 * ratio1 + c1 * (1 - ratio1)
            return [pt0, pt1]
        else:
            ratio = r0 / (r0 + r1)
            pt = c1 * ratio + c0 * (1 - ratio)
            return [pt]

    flag = False
    for prev, curr in zip(route, route[1:] + [route[0]]):
        for pt in add_half_edge(prev, curr):
            vertices.append((pt.real, pt.imag))
        flag = not flag and is_vert(curr['id'])
        if flag:
            curr_id = curr['id']
            if curr_id[-2] == '_':
                curr_id = curr_id[:-2]
            if curr['up']:
                up_crossings[curr_id] = len(vertices) - 1
            else:
                down_crossings[curr_id] = len(vertices) - 1

    return (vertices, [(down_crossings[v], up_crossings[v]) for v in up_crossings.keys()])
