from spherogram.links.orthogonal import OrthogonalLinkDiagram

def diagram4link(link):
    diagram = OrthogonalLinkDiagram(link)
    data = diagram.plink_data()
    return (data[0], data[2])
