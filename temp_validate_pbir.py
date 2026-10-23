"""Temporary: validate every PBIR JSON file against its published $schema."""
import glob
import json
import os
import urllib.request

import jsonschema
from referencing import Registry, Resource

CACHE = {}


def fetch(uri):
    if uri not in CACHE:
        with urllib.request.urlopen(urllib.request.Request(uri, headers={"User-Agent": "x"}), timeout=30) as r:
            CACHE[uri] = json.loads(r.read().decode("utf-8-sig"))
    return CACHE[uri]


def retrieve(uri):
    return Resource.from_contents(fetch(uri), default_specification=jsonschema.Draft7Validator.META_SCHEMA and None or None) \
        if False else Resource.opaque(fetch(uri)) if False else Resource.from_contents(fetch(uri))


registry = Registry(retrieve=retrieve)
root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "powerbi")
files = [f for f in glob.glob(os.path.join(root, "**", "*.json"), recursive=True) if "assets" not in f and "data" not in f.split(os.sep)]
files += glob.glob(os.path.join(root, "**", "*.pbir"), recursive=True) + glob.glob(os.path.join(root, "*.pbip"))
errors = 0
for f in files:
    doc = json.load(open(f, encoding="utf-8"))
    sch = doc.get("$schema")
    if not sch:
        continue
    schema = fetch(sch)
    cls = jsonschema.validators.validator_for(schema)
    v = cls(schema, registry=registry)
    errs = list(v.iter_errors(doc))
    if errs:
        errors += len(errs)
        print("FAIL", os.path.relpath(f, root))
        for e in errs[:4]:
            print("   ", "/".join(map(str, e.absolute_path)), "->", e.message[:220])
print(f"checked {len(files)} files, {errors} errors")
