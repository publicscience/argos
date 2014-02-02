from core.models import Entity, Article, Cluster, Source

from database.datastore import db

def entity(num=1):
    args = [
        {'name': 'Argos'},
        {'name': 'Ceres'},
        {'name': 'Iliad'}
    ]
    e_s = [Entity(**args[i]) for i in range(num)]

    save(e_s)

    if len(e_s) is 1:
        return e_s[0]
    return e_s

def source(num=1):
    args = [
        {'url': 'foo'},
        {'url': 'bar'},
        {'url': 'sup'}
    ]
    s_s = [Source(**args[i]) for i in range(num)]

    save(s_s)

    if len(s_s) is 1:
        return s_s[0]
    return s_s

def article(num=1, **kwargs):
    args = [
        {'title':'Dinosaurs', 'text':'Dinosaurs are cool, Clinton'},
        {'title':'Robots', 'text':'Robots are nice, Clinton'},
        {'title':'Mudcrabs', 'text':'Mudcrabs are everywhere, Clinton'}
    ]

    if not kwargs:
        a_s = [Article(**args[i]) for i in range(num)]
    else:
        a_s = [Article(**kwargs) for i in range(num)]

    save(a_s)

    if len(a_s) is 1:
        return a_s[0]
    return a_s

def event(num=1, num_members=2):
    """
    Creates an event cluster.
    """
    return cluster(
            tag='event',
            member_factory=article,
            num=num,
            num_members=num_members
    )

def story(num=1, num_members=2):
    """
    Creates a story cluster.
    """
    return cluster(
            tag='story',
            member_factory=event,
            num=num,
            num_members=num_members
    )

def cluster(num=1, num_members=2, tag='default', member_factory=article):
    """
    Creates a generic cluster.

    Args:
        | num (int)             -- number of clusters to create
        | num_members (int)     -- number of members in each cluster
        | tag (str)             -- tag of the cluster to create
        | member_factory (func) -- function for creating members
    """
    c_s = []
    for i in range(num):
        members = member_factory(num=num_members)
        c = Cluster(members, tag=tag)
        c_s.append(c)
    save(c_s)
    if len(c_s) is 1:
        return c_s[0]
    return c_s


def save(objs):
    """
    Saves a set of objects to the database.
    """
    if type(objs) is list:
        for obj in objs:
            db.session.add(obj)
    else:
        print("Here")
        db.session.add(objs)
    db.session.commit()
