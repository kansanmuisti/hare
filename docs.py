from __future__ import absolute_import
import os
import pymongo
import settings
import requests
from pprint import pprint

client = pymongo.MongoClient(settings.MONGO_HOST, settings.MONGO_PORT)
db = client[settings.MONGO_DBNAME]

download_count = 0

def download_doc(doc, url):
    #print("%s: %s" % (doc['asiakirja_id'], url))
    ext = url.split('.')[-1].lower()
    fname = url.split('/')[-1]
    if ext == 'htm':
        ext = 'html'
    if ext not in ('doc', 'pdf', 'docx', 'rtf', 'txt', 'html', 'odt', 'xls', 'dot', 'ppt', 'tif', 'xlsx', 'msg', 'pptx', 'ods', 'zip', 'docm', 'lwp', 'pptm'):
        ext = 'unknown'
    else:
        fname = fname[0:-(len(ext) + 1)]

    doc_hash = int(doc['asiakirja_id']) % 100
    hash_path = 'docs/%d' % doc_hash
    if not os.path.exists(hash_path):
        os.mkdir(hash_path)
    fpath = '%s/%d.%s' % (hash_path, doc['asiakirja_id'], ext)
    doc['local_file'] = fpath
    if os.path.exists(fpath):
        return

    print("%s: %s" % (download_count, url.encode('utf8')))
    download_count += 1
    resp = requests.get(url, stream=True)
    if not resp.status_code == 200:
        print("%d: %s" % (resp.status_code, url))
        doc['local_file'] = None
        doc['error'] = resp.status_code

    try:
        with open(fpath, 'wb') as outf:
            for chunk in resp.iter_content(chunk_size=131072):
                if chunk:
                    outf.write(chunk)
    except:
        os.unlink(fpath)
        raise

projects = db.projects

for project in projects.find():
    if not 'asiakirjat' in project:
        continue
    changed = False
    for doc in project['asiakirjat']:
        if not doc['tiedosto']:
            continue
        if doc.get('local_file', None):
            continue
        url = doc['tiedosto']
        if not url.startswith('http://'):
            assert url.startswith('www.hare')
            url = 'http://' + url
        download_doc(doc, url)
        changed = True

    if changed:
        projects.save(project)
