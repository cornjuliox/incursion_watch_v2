# scout, vanguard, assault, hq, and mothership type sites
# staging type excluded because it is already identified
# in the initial request.


ASSAULT = [
    'okkamon',
    'vaaralen',
    'vecodie',
    'ilahed',
    'esa',
    'kari',
    'Nikh',
    'Amphar',
    'Usroh',
]

VANGUARD = [
    'asakai',
    'mushikegi',
    'elunala',
    'ikoskio',
    'arasare',
    'sosa',
    'uhodoh',
    'hath',
    'judra',
    'sharios',
    'eshwil',
    'aranir',
    'yvelet',
    'lazer',
    'salashayama',
    'janus',
    'iosantin',
    'orva',
    'zet',
    'thiarer',
]

HEADQUARTERS = [
    'teskanen',
    'yvaeroure',
    'ishkad',
    'arakor',
    'Agha',
]

TYPEMAP = {}
TYPEMAP.update({
    x: 'Assault'
    for x in ASSAULT

})

TYPEMAP.update({
    x: 'Vanguard'
    for x in VANGUARD
})

TYPEMAP.update({
    x: 'Headquarters'
    for x in HEADQUARTERS
})
