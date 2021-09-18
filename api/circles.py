import itertools
from .CirclePack import CirclePack

def diagram4link(link):
    face_id_to_obj = {}
    edge_to_face_id = {}
    for index, face in enumerate(link.faces()):
        face_id = 'f%s' % index
        face_id_to_obj[face_id] = face
        edge_to_face_id.update({strand: face_id for strand in face})

    edge_obj_to_id = {}
    strands = set(link.crossing_strands())
    while strands:
        st = strands.pop()
        oppo = st.opposite()
        strands.remove(oppo)
        edge_id = 'e%s' % (len(edge_obj_to_id) // 2)
        edge_obj_to_id[st] = edge_id
        edge_obj_to_id[oppo] = edge_id

    crossings = set(s[0] for s in link.crossing_strands())
    vert_obj_to_id = {crs: 'v%s' % (crs.label, ) for crs in crossings}
    vert_id_to_obj = {vert_id: obj for (obj, vert_id) in vert_obj_to_id.items()}

    strands = [link.crossing_strands()[0]]
    while True:
        s = strands[-1].next()
        if s == strands[0]:
            break
        strands.append(s)

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
    for vert_id, vert in vert_id_to_obj.items():
        cycle = []
        for i in range(4):
            edge = (vert, i)
            cycle.append(edge_obj_to_id[edge])
            cycle.append(edge_to_face_id[edge])
        cycle.reverse()
        all_cycles[vert_id] = cycle

    best_cost = None
    optimal = None
    for external_face_id in face_id_to_obj.keys():
        external_ids = all_cycles[external_face_id]
        external = {x_id: 1 for x_id in external_ids}

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

        internal_ids = [f for f in face_id_to_obj.keys() if f != external_face_id] + \
                       [e for e in edge_obj_to_id.values() if e not in external_ids] + \
                       [v for v in vert_id_to_obj.keys() if v not in external_ids]
        internal = {obj_id: all_cycles[obj_id] for obj_id in internal_ids}

        cost = [len(levels)] + [len(lev) for lev in reversed(levels)]
        if best_cost is None or cost < best_cost:
            best_cost = cost
            optimal = (internal, external)

    pack = CirclePack(optimal[0], optimal[1])


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

    for strand in strands:
        prev = strand.opposite().rotate(2)
        v0 = vert_obj_to_id[prev[0]]
        edge = edge_obj_to_id[strand]
        v1 = vert_obj_to_id[strand[0]]
        pts = add_half_edge(v0, edge) + add_half_edge(edge, v1)
        for pt in pts:
            vertices.append((pt.real, pt.imag))
        if strand[1] % 2 == 0:
            up_crossings[v1] = len(vertices) - 1
        else:
            down_crossings[v1] = len(vertices) - 1

    return (vertices, [(down_crossings[v], up_crossings[v]) for v in up_crossings.keys()])
