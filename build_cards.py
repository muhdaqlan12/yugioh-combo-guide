#!/usr/bin/env python3
"""Build static card metadata and locally hosted card thumbnails for the trainer.
Card links point to Master Duel Meta; image and base rules data are sourced from
YGOPRODeck's public API and downloaded once at deployment (no image hotlinking).
"""
import json, pathlib, urllib.request, urllib.parse, time
root=pathlib.Path(__file__).resolve().parent
deck=json.loads((root/"data/blue-eyes-primite.json").read_text(encoding="utf-8"))
names=list(dict.fromkeys(x[0] for x in deck["mainDeck"]+deck["extraDeck"]))
imgdir=root/"assets"/"cards"
imgdir.mkdir(parents=True,exist_ok=True)
metadata={}
for name in names:
    link="https://www.masterduelmeta.com/cards/"+urllib.parse.quote(name,safe="")
    entry={"name":name,"masterDuelMeta":link}
    try:
        url="https://db.ygoprodeck.com/api/v7/cardinfo.php?name="+urllib.parse.quote(name,safe="")
        req=urllib.request.Request(url,headers={"User-Agent":"BlueEyesComboGuide/1.0 (static personal guide)"})
        with urllib.request.urlopen(req,timeout=25) as resp:
            info=json.load(resp)["data"][0]
        if info["name"].casefold()!=name.casefold():
            raise ValueError("Name mismatch")
        for key in ("type","race","attribute","level","atk","def","desc","archetype","linkval","scale"):
            if key in info:entry[key]=info[key]
        card_id=info["card_images"][0]["id"]
        imgpath=imgdir/(str(card_id)+".jpg")
        if not imgpath.exists():
            src=info["card_images"][0]["image_url_small"]
            req=urllib.request.Request(src,headers={"User-Agent":"BlueEyesComboGuide/1.0"})
            with urllib.request.urlopen(req,timeout=25) as resp:
                payload=resp.read(350000)
            if not payload.startswith(b"\xff\xd8"):
                raise ValueError("Unexpected image format")
            imgpath.write_bytes(payload)
        entry["image"]="assets/cards/"+imgpath.name
        print("OK",name,flush=True)
    except Exception as exc:
        print("Unavailable",name,str(exc),flush=True)
    metadata[name]=entry
    time.sleep(.15)
(root/"data"/"card-details.json").write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding="utf-8")
print("Saved",len(metadata),"card entries")
