#!/usr/bin/env python
# -*- coding: utf-8 -*-

from lxml import etree, objectify
import json
import re
import codecs

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
    s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
    if s1 == 'ww_wosoite':
        return 'www_osoite'
    if s1 == 'tyoanantaja':
        return 'tyonantaja'
    return s1.replace('__', '_')

def clean_element(val, name=''):
    if hasattr(val, 'attrib') and val.attrib:
        attrib = dict(val.attrib)
        for key, dval in attrib.items():
            del attrib[key]
            dval = clean_text(dval)
            if not dval:
                dval = None
            attrib[camel_to_underscore(key)] = dval
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

f = open('hare.xml')
context = etree.iterparse(f)
count = 0

outf = codecs.open('hare-2014-05-29.json', 'w', 'utf8')
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
    s = json.dumps(obj, ensure_ascii=False, encoding='utf8')
    outf.write(s)
    outf.write('\n')
