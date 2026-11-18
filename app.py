import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
import engine as e
from edits import revise, suggest
import publish

st.set_page_config(page_title="Clipper.ai Studio",layout="wide")
e.launch()
st.title("Clipper.ai")
st.caption("Your editing studio")
root=e.ROOT
defaults_path=root/"style.json"
defaults=json.loads(defaults_path.read_text()) if defaults_path.exists() else {}
posting_path=root/"posting.json"
posting=json.loads(posting_path.read_text()) if posting_path.exists() else {}
intake,queue,review,youtube=st.tabs(["Import","Queue","Review edits","YouTube"])

def store_file(file):
    folder=root/"sources"
    folder.mkdir(exist_ok=True)
    suffix=Path(file.name).suffix.lower()
    digest=hashlib.sha256(file.getbuffer()).hexdigest()
    target=folder/(digest+suffix)
    if not target.exists():
        temp=target.with_suffix("."+uuid.uuid4().hex+".part")
        with temp.open("wb") as f:
            f.write(file.getbuffer())
        temp.replace(target)
    return target,digest


with intake:
    st.subheader("Add footage")
    if st.button("Try a sample clip"):
        demo=Path(__file__).resolve().parent/"sample"
        e.enqueue(demo/"wheels.mp4","Wheel speed demo",dict(mode="Edit",layout="Full frame",captions=True,length=12,
            start=0,angle="Why the smaller wheel spins faster",credit="Clipper.ai studio sample",
            demo_cues=json.loads((demo/"captions.json").read_text())))
        st.success("Sample queued with provided English captions. Open Queue to follow it.")
    mode=st.radio("What are you editing?",["Existing clips","Full recordings"],horizontal=True)
    files=st.file_uploader("Drop videos here",type=["mp4","mov","mkv","ts","webm","m4v"],accept_multiple_files=True)
    paths=st.text_area("Or paste local file paths, one per line",placeholder="Use a local path for large recordings.")
    link=st.text_input("Source link or streamer credit",placeholder="YouTube video/live link, Twitch link, or creator name")
    import_link=st.checkbox("Import video from this YouTube link",value=False,help="A live broadcast downloads until it ends; then highlights are suggested.")
    if link and not files and not paths.strip() and not import_link:
        st.info("Attach the original recording, enter its local path, or choose YouTube link import.")
    angle=st.text_input("Story or working title",placeholder="What should the viewer notice?")
    a,b,c=st.columns(3)
    layout=a.selectbox("Vertical layout",["Full frame","Center crop"],index=int(defaults.get("layout")=="Center crop"))
    caps=b.checkbox("Generate captions",defaults.get("captions",True))
    length=c.number_input("Maximum clip length (seconds)",5,3600,45)
    caption_style=st.selectbox("Caption style",list(e.CAPTION_STYLES),index=list(e.CAPTION_STYLES).index(defaults.get("caption_style","Classic")) if defaults.get("caption_style") in e.CAPTION_STYLES else 0,disabled=not caps)
    count=st.number_input("Highlights per recording",1,50,3) if mode=="Full recordings" or import_link else 1
    rank_model=st.text_input("Optional Ollama model for transcript-based highlights",placeholder="Leave blank to rank by audio changes") if mode=="Full recordings" else ""
    if st.button("Remember style"):
        defaults_path.write_text(json.dumps(dict(layout=layout,captions=caps,caption_style=caption_style)))
        st.success("Style saved.")
    if st.button("Add to queue",type="primary"):
        try:
            sources=[]
            for line in paths.splitlines():
                if not line.strip():
                    continue
                p=Path(line.strip().strip('"').strip("'")).expanduser().resolve()
                if not p.is_file():
                    raise ValueError(f"File not found: {p.name}")
                sources.append((p,p.name,f"{p}:{p.stat().st_size}:{p.stat().st_mtime_ns}"))
            for f in files:
                p,d=store_file(f)
                sources.append((p,f.name,d))
            if import_link:
                url=e.youtube_url(link)
                if sources:
                    raise ValueError("Queue the YouTube link and local files separately.")
                sources.append((url,"YouTube · "+url.rsplit("=",1)[-1],url))
            if not sources:
                raise ValueError("Add a recording first.")
            for p,name,d in sources:
                e.enqueue(p,name,dict(mode="Fetch" if import_link else "Discover" if mode=="Full recordings" else "Edit",
                    url=p if import_link else "",layout=layout,auto_trim=True,ranking_model=rank_model,captions=caps,
                    caption_style=caption_style,length=length,count=count,start=0,credit=link,angle=angle,
                    auto_publish=bool(posting.get("enabled") and (root/"token.json").exists()),
                    post_visibility=posting.get("visibility","private"),post_footer=posting.get("footer","")),d)
            st.success(f"Added {len(sources)} to the queue. Open Queue for progress.")
        except Exception as err:
            st.error(str(err))

@st.fragment(run_every=3)
def progress():
    jobs=e.rows()
    if not jobs:
        st.info("Jobs appear here after you add footage.")
        return
    durations=[r["ended"]-r["started"] for r in jobs if r["ended"] and r["status"] in ("Ready","Needs review","Highlights")]
    waiting=sum(r["status"] in ("Queued","Working") for r in jobs)
    st.caption(f"{waiting} unfinished · {sum(r['status']=='Ready' for r in jobs)} ready · {sum(r['status']=='Needs review' for r in jobs)} need review")
    if waiting and durations:
        avg=sum(durations)/len(durations)
        st.caption(f"Queue estimate: about {max(1,round(avg*waiting/60))} min remaining, based on completed jobs. Long recordings can take longer.")
    for r in jobs:
        with st.container(border=True):
            st.markdown("**"+r["name"]+"**")
            elapsed=max(0,(r["ended"] or time.time())-r["started"]) if r["started"] else 0
            eta="Estimating…" if not durations else f"Estimated time left: ~{max(1,round((sum(durations)/len(durations)-elapsed)/60))} min"
            st.progress(r["pct"]/100,text=f"{r['step']} · {round(elapsed)}s elapsed"+(f" · {eta}" if r["status"]=="Working" else ""))
            if r["status"]=="Queued" and st.button("Move to front",key="priority"+r["id"]):
                e.update(r["id"],priority=time.time())
            if r["error"]:
                st.error(r["error"])
            if r["status"]=="Failed" and st.button("Retry",key="retry"+r["id"]):
                e.update(r["id"],status="Queued",pct=0,error="",step="Waiting",started=None,ended=None)
                st.rerun()
with queue:
    progress()

with review:
    if st.button("Refresh drafts"):
        st.rerun()
    jobs=[r for r in e.rows() if r["status"] in ("Highlights","Ready","Needs review","Uploaded","Published","Scheduled")]
    if not jobs:
        st.info("When a job finishes, click Refresh drafts.")
    else:
        r=st.selectbox("Choose a draft",jobs,format_func=lambda x:f"{x['name']} · {x['status']} · {x['id'][:6]}")
        j=r["id"]
        opt=json.loads(r["opts"])
        res=json.loads(r["result"])
        if r["status"]=="Highlights":
            st.caption("Select a moment to render and preview. The reason explains why it was suggested.")
            if not res["picks"]:
                st.info("No clear audio peaks found. Reimport as an existing clip and set a manual trim.")
            for idx,pick in enumerate(res["picks"]):
                t=pick["start"]
                if st.button(f"Edit from {int(t)//60}:{int(t)%60:02d} · {pick['reason']}",key=j+str(idx)):
                    e.enqueue(r["source"],r["name"],dict(opt,mode="Edit",start=t))
                    st.success("Added highlight to queue.")
            st.code(r["source"])
        else:
            left,right=st.columns([1,2])
            video=root/j/"preview.mp4"
            left.video(str(video))
            with video.open("rb") as f:
                left.download_button("Download MP4",f,file_name=Path(r["name"]).stem+"-short.mp4",mime="video/mp4")
            with right:
                st.write(f"Source starts at {res['start']:.1f}s · {res['duration']:.1f}s · {opt['layout']}")
                st.caption(res.get("reason",""))
                for n in res["notes"]:
                    st.warning(n)
                capfile=root/j/"captions.srt"
                if capfile.exists():
                    with st.expander("Read captions"):
                        st.text(capfile.read_text())
                model=st.text_input("Optional local Ollama model",placeholder="Installed model name",key="model"+j)
                if st.button("Suggest commentary",key="script"+j):
                    try:
                        if not model:
                            raise ValueError("Select a local Ollama model for a generated script, or record your own take below.")
                        script=suggest("Write one brief commentary suggestion based only on this transcript. Do not invent visual events. If context is insufficient ask for the editor's observation. JSON key: script. Transcript: "+(capfile.read_text()[:12000] if capfile.exists() else "")+" Editor's angle: "+opt["angle"],model)
                        st.session_state["draftscript"+j]=str(script["script"])
                    except Exception as err:
                        st.error(str(err))
                if st.session_state.get("draftscript"+j):
                    st.write(st.session_state["draftscript"+j])
                instruction=st.text_input("Change the edit",placeholder="Start 3 seconds earlier",key="edit"+j)
                revised_style=st.selectbox("Caption style",list(e.CAPTION_STYLES),index=list(e.CAPTION_STYLES).index(opt.get("caption_style","Classic")) if opt.get("caption_style","Classic") in e.CAPTION_STYLES else 0,key="style"+j)
                speech=st.audio_input("Optional voiceover",key="speech"+j)
                if st.button("Render revised draft",key="render"+j):
                    try:
                        changed=revise(opt,instruction,e.duration(Path(r["source"])),model) if instruction.strip() else dict(opt)
                        if speech:
                            changed["voice"]=str(store_file(speech)[0])
                        changed["caption_style"]=revised_style
                        if not instruction.strip() and not speech and changed==opt:
                            raise ValueError("Change the caption style, add an edit instruction, or record a voiceover.")
                        e.enqueue(r["source"],r["name"],changed)
                        st.success("Revision queued. Your previous preview is saved.")
                    except Exception as err:
                        st.error(str(err))

with youtube:
    st.subheader("Approve uploads")
    with st.expander("Connect your channel",expanded=not (root/"token.json").exists()):
        st.write("Enable YouTube Data API v3 in Google Cloud. Create an OAuth desktop client and add your Google account as a test user if the app is in testing. Select its downloaded JSON below.")
        client=st.file_uploader("Desktop OAuth client JSON",type=["json"])
        if st.button("Sign in with Google"):
            try:
                if client:
                    data=json.loads(client.getvalue())
                    if "installed" not in data:
                        raise ValueError("Choose a Desktop app client JSON.")
                    (root/"client.json").write_text(json.dumps(data))
                    (root/"client.json").chmod(0o600)
                    (root/"token.json").unlink(missing_ok=True)
                st.session_state.api=publish.service()
                st.session_state.channel=publish.channel(st.session_state.api)
                st.success("Connected.")
            except Exception as err:
                st.error(str(err))
    if "channel" in st.session_state:
        st.write("Posting to **"+st.session_state.channel[0]+"**")
        st.subheader("Automatic posting for future drafts")
        auto=st.checkbox("Automatically upload ready drafts",value=posting.get("enabled",False),help="Only new jobs you queue after saving are uploaded. Drafts needing review stay in the studio.")
        auto_visibility=st.selectbox("Automatic visibility",["private","unlisted","public"],index=["private","unlisted","public"].index(posting.get("visibility","private")) if posting.get("visibility") in ("private","unlisted","public") else 0)
        footer=st.text_area("Description footer",value=posting.get("footer",""),help="Source credit from Import is added above this footer.")
        if st.button("Save automatic posting settings"):
            posting_path.write_text(json.dumps({"enabled":auto,"visibility":auto_visibility,"footer":footer}))
            posting_path.chmod(0o600)
            st.success("Saved for future jobs. Review a private upload before selecting public.")
        choices=[r for r in e.rows() if r["status"] in ("Ready","Needs review","Uploaded","Published","Scheduled")]
        selected=st.multiselect("Select reviewed drafts",choices,format_func=lambda x:x["name"]+" · "+x["id"][:6])
        first=not any(r["video_id"] for r in e.rows())
        visibility=st.selectbox("Visibility",["private"] if first else ["private","unlisted","public","schedule"])
        when=None
        if visibility=="schedule":
            day=st.date_input("Date (UTC)")
            at=st.time_input("Time (UTC)")
            when=datetime.combine(day,at,tzinfo=timezone.utc)
        posts=[]
        for r in selected:
            result=json.loads(r["result"])
            st.caption(r["name"])
            title=st.text_input("Title",result["title"],max_chars=100,key="title"+r["id"])
            description=st.text_area("Description and credit",result["description"],key="desc"+r["id"])
            posts.append((r,title,description))
        if st.button("Approve and upload",disabled=not posts,type="primary"):
            if when and when<=datetime.now(timezone.utc):
                st.error("Choose a future UTC time.")
            else:
                for r,title,description in posts:
                    try:
                        vid=publish.post(st.session_state.api,r,title,description,visibility,when.isoformat() if when else None)
                        st.success("Saved to YouTube: https://youtu.be/"+vid)
                    except Exception as err:
                        st.error(r["name"]+": "+str(err))
