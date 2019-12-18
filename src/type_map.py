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
]

HEADQUARTERS = [
    'teskanen',
    'yvaeroure',
    'ishkad',
    'arakor',
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
