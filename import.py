#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree, objectify
import json
import re
import codecs
import argparse

parser = argparse.ArgumentParser(description='Convert HARE XML into JSON')
parser.add_argument('input', metavar='INPUT', type=str, help='input XML file')
parser.add_argument('--mongo', action='store_true', help='output in mongodump format')
parser.add_argument('--output', metavar='FILE', type=str, help='output file')

args = parser.parse_args()

def clean_text(text):
    text = text.replace('\n', ' ')
    text = text.replace(u'\u00a0', ' ')
    # remove consecutive whitespaces
    return re.sub(r'\s\s+', ' ', text, re.U).strip()

def objectified_to_python(o):
    if isinstance(o, objectify.IntElement):
        return int(o)
    if isinstance(o, objectify.NumberElement) or isinstance(o, objectify.FloatElement):
        return float(o)
    if isinstance(o, objectify.ObjectifiedDataElement):
        s = clean_text(unicode(o))
        if not s:
            return None
        return s
    if isinstance(o, dict):
        return o
    if hasattr(o, '__dict__'):
        #For objects with a __dict__, return the encoding of the __dict__
        d = o.__dict__
        return d
    return o

def camel_to_underscore(text):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
    s1 = s1.lower()
    if s1 == 'tyoanantaja':
        return 'tyonantaja'
    elif s1 == 'viimemuutos':
        return '_updated'
    elif s1 == 'luontiaika':
        return '_created'
    elif s1 == 'asettamis_paatos_liitteet':
        return 'asettamispaatos_liitteet'
    elif s1 == 'organisointi_tapa':
        return 'organisointitapa'
    elif s1 == 'asiankasittelye_kssa_he':
        return 'asian_kasittely_ekssa_he'
    elif s1 == 'ajankohta_he_v_noon':
        return 'ajankohta_he_vn'
    elif s1 == 'ww_wosoite':
        return 'www_osoite'
    return s1.replace('__', '_')

def clean_date(val, d):
    assert isinstance(val, objectify.StringElement)
    assert not val.getchildren()
    for k in d.values():
        if k:
            break
    else:
        return None
    ts = '%s-%s-%s' % (d['vuosi'], d['kuukausi'], d['paiva'])
    if 'minuutti' in d:
        ts += 'T%s:%s:%s' % (d['tunti'], d['minuutti'], d['sekuntti'])
    return ts

def clean_element(val, name=''):
    if hasattr(val, 'attrib') and val.attrib:
        attrib = dict(val.attrib)
        for key, dval in attrib.items():
            del attrib[key]
            dval = clean_text(dval)
            if not dval:
                dval = None
            attrib[camel_to_underscore(key)] = dval
        if 'vuosi' in attrib:
            return clean_date(val, attrib)
    else:
        attrib = None

    if name in ('asiasanat', 'aihealueet', 'allekirjoittajat', 'ryhmat', 'henkilot', 'asiakirjat', 'julkaisut'):
        val = [clean_element(x, name=camel_to_underscore(x.tag)) for x in val.getchildren()]
    elif name == 'asettaja':
        val = {'nimi': attrib['asettaja'], 'osasto': attrib['asettajan_osasto']}
        attrib = None
    elif name == 'ryhma':
        d = attrib
        if hasattr(val, 'Henkilot'):
            d['henkilot'] = [clean_element(x, name='henkilo') for x in val.Henkilot.getchildren()]
        return d

    if name == 'allekirjoittajat':
        val = [x for x in val if x['nimi'] or x['nimike']]

    if isinstance(val, objectify.StringElement):
        if val == 'Ei':
            val = False
        elif val == u'Kyllä':
            val = True

    val = objectified_to_python(val)
    if isinstance(val, dict):
        d = val
        for key, dval in d.items():
            del d[key]
            key = camel_to_underscore(key)
            d[key] = clean_element(dval, key)
    """
    if isinstance(val, list):
        new_list = []
        for el in val:
            new_list.append(clean_element(el))
        val = new_list
    """

    if attrib:
        if val:
            attrib['value'] = val
        return attrib

    return val

def clean_project(obj):
    project_id = int(obj.attrib['ID'])
    assert len(obj.keys()) == 1
    d = obj['Hanketiedot'].__dict__
    d['id'] = project_id
    d['_id'] = project_id
    return clean_element(d)

f = open(args.input)
context = etree.iterparse(f, huge_tree=True)
count = 0

if args.output:
    out_fname = args.output
else:
    out_fname = 'hare.json'

outf = codecs.open(out_fname, 'w', 'utf8')
if not args.mongo:
    outf.write('[')

for action, elem in context:
    if action != 'end' or elem.tag != 'Hanke':
        continue
    parent = elem.getparent()
    parent.remove(elem)
    count += 1
    if count % 100 == 0:
        print(count)

    obj = objectify.fromstring(etree.tostring(elem))
    obj = clean_project(obj)
    json_args = {'ensure_ascii': False, 'encoding': 'utf8'}
    if not args.mongo:
        json_args['indent'] = 4
    s = json.dumps(obj, **json_args)
    outf.write(s)
    outf.write('\n')

if not args.mongo:
    outf.write(']')
