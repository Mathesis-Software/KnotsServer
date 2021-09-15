from .CirclePack import CirclePack

def diagram4link(link):
    face_id_to_obj = {}
    edge_to_face_id = {}
    for index, face in enumerate(link.faces()):
        face_id = 'f%s' % index
        face_id_to_obj[face_id] = face
        edge_to_face_id.update({strand: face_id for strand in face})

    edge_obj_to_id = {}
    edge_id_to_obj = {}
    strands = set(link.crossing_strands())
    while strands:
        st = strands.pop()
        oppo = st.opposite()
        strands.remove(oppo)
        edge_id = 'e%s' % (len(edge_obj_to_id) // 2)
        edge_obj_to_id[st] = edge_id
        edge_obj_to_id[oppo] = edge_id
        edge_id_to_obj[edge_id] = st

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
        #print('%s => %s' % (face_id, all_cycles[face_id]))
    for edge_id, edge in edge_id_to_obj.items():
        oppo = edge.opposite()
        all_cycles[edge_id] = [
            vert_obj_to_id[edge[0]],
            edge_to_face_id[edge],
            vert_obj_to_id[oppo[0]],
            edge_to_face_id[oppo],
        ]
        #print('%s => %s' % (edge_id, all_cycles[edge_id]))
    for vert_id, vert in vert_id_to_obj.items():
        cycle = []
        for i in range(4):
            edge = (vert, i)
            cycle.append(edge_obj_to_id[edge])
            cycle.append(edge_to_face_id[edge])
        cycle.reverse()
        all_cycles[vert_id] = cycle
        #print('%s => %s' % (vert_id, all_cycles[vert_id]))

    best_ratio = -1
    pack = None
    max_edges = max(len(face) for face in face_id_to_obj.values())
    for external_face_id, face in face_id_to_obj.items():
        if len(face) < max_edges:
            continue

        external_edge_ids = [edge_obj_to_id[strand] for strand in face]
        external_vert_ids = [vert_obj_to_id[strand[0]] for strand in face]

        external = {edge_id: 1 for edge_id in external_edge_ids}
        external.update({vert_id: 1 for vert_id in external_vert_ids})

        internal_ids = [f for f in face_id_to_obj.keys() if f != external_face_id] + \
                       [e for e in edge_id_to_obj.keys() if e not in external_edge_ids] + \
                       [v for v in vert_id_to_obj.keys() if v not in external_vert_ids]
        internal = {obj_id: all_cycles[obj_id] for obj_id in internal_ids}

        candidate = CirclePack(internal, external)
        opts = [key for key in candidate.keys() if key.startswith('v')]
        radiis = [candidate[v][1] for v in opts]
        candidate_ratio = min(radiis) / max(radiis)
        if candidate_ratio > best_ratio:
            #print('%s => %.3f' % (external_face_id, candidate_ratio))
            pack = candidate
            best_ratio = candidate_ratio

    vertices = []
    up_crossings = {}
    down_crossings = {}

    def add_half_edge(key0, key1):
        c0 = pack[key0][0]
        c1 = pack[key1][0]
        r0 = pack[key0][1]
        r1 = pack[key1][1]

        ratio0 = r0 / (r0 + r1) * 2 / 3
        ratio1 = r1 / (r0 + r1) * 2 / 3
        pt0 = c1 * ratio0 + c0 * (1 - ratio0)
        pt1 = c0 * ratio1 + c1 * (1 - ratio1)
        vertices.append((pt0.real, pt0.imag))
        vertices.append((pt1.real, pt1.imag))

    for strand in strands:
        prev = strand.opposite().rotate(2)
        v0 = vert_obj_to_id[prev[0]]
        edge = edge_obj_to_id[strand]
        v1 = vert_obj_to_id[strand[0]]
        add_half_edge(v0, edge)
        add_half_edge(edge, v1)
        if strand[1] % 2 == 0:
            up_crossings[v1] = len(vertices) - 1
        else:
            down_crossings[v1] = len(vertices) - 1

    return (vertices, [(down_crossings[v], up_crossings[v]) for v in up_crossings.keys()])
