import json
import re
import urllib.request


def suggest(prompt,model):
    req=urllib.request.Request("http://127.0.0.1:11434/api/generate",
        data=json.dumps(dict(model=model,prompt=prompt,stream=False,format="json")).encode(),
        headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req,timeout=180) as response:
        return json.loads(json.load(response)["response"])


def revise(options, words, duration, model=""):
    opt=dict(options)
    normalized=words.lower().strip()
    if model:
        result=suggest("Translate the user's video edit into a JSON object. Allowed keys only: start (seconds), length (seconds), layout ('Full frame' or 'Center crop'), replace_from, replace_to (strings), captions (boolean). Current settings: "+json.dumps({k:opt.get(k) for k in ["start","length","layout","captions"]})+" Source duration seconds: "+str(duration)+" User edit: "+words,model)
        for key,value in result.items():
            if key in ("start","length"):
                opt[key]=float(value)
            elif key=="layout" and value in ("Full frame","Center crop"):
                opt[key]=value
            elif key in ("replace_from","replace_to") and isinstance(value,str):
                opt[key]=value
            elif key=="captions" and isinstance(value,bool):
                opt[key]=value
    elif "facecam" in normalized or "full frame" in normalized:
        opt["layout"]="Full frame"
    elif "center crop" in normalized:
        opt["layout"]="Center crop"
    elif m:=re.fullmatch(r"(?:start at|trim to) (\d+) seconds?",normalized):
        opt["start" if normalized.startswith("start") else "length"]=int(m[1])
    elif m:=re.fullmatch(r"start (\d+) seconds? (earlier|later)",normalized):
        opt["start"]=max(0,opt.get("start",0)+int(m[1])*(-1 if m[2]=="earlier" else 1))
    elif m:=re.fullmatch(r'replace "([^"]+)" with "([^"]*)"',words.strip(),re.I):
        opt.update(replace_from=m[1],replace_to=m[2])
    else:
        raise ValueError('Try “keep the facecam”, “center crop”, “trim to 20 seconds”, “start at 5 seconds”, or replace "old" with "new".')
    if not 0<=opt.get("start",0)<duration or not 0<opt["length"]<=3600:
        raise ValueError("That edit falls outside the source or exceeds one hour.")
    if opt==options:
        raise ValueError("This instruction did not change the edit.")
    return opt
