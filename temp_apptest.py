"""Temporary smoke test: run app.py headlessly in both study contexts."""
import json
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py", default_timeout=90).run()
print("UK exceptions:", [e.value for e in at.exception])
deck = json.loads(at.get("deck_gl_json_chart")[0].proto.json)
print("UK map:", deck.get("mapProvider"), deck.get("mapStyle"), len(deck["layers"][0]["data"]), "zoom", round(deck["initialViewState"]["zoom"], 2))
print("UK first table rows:", len(at.dataframe[0].value))

at.sidebar.radio[0].set_value("India Transferability Case (Bengaluru)").run()
print("India exceptions:", [e.value for e in at.exception])
deck = json.loads(at.get("deck_gl_json_chart")[0].proto.json)
print("India map:", deck.get("mapProvider"), len(deck["layers"][0]["data"]), "zoom", round(deck["initialViewState"]["zoom"], 2),
      deck["initialViewState"]["latitude"], deck["initialViewState"]["longitude"])
print("India road classes:", at.sidebar.multiselect[0].value)
print("India quad rows:", len(at.dataframe[0].value))
print("India markdown sample:", [m.value[:90] for m in at.markdown if "Rank #" in m.value or "Peak crash" in m.value][:3])

at.sidebar.radio[1].set_value("Raw Crash Frequency (Counts)").run()
print("Raw metric exceptions:", [e.value for e in at.exception])
