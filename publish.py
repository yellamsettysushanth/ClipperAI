"""Create a private YouTube draft before making it public or scheduling it."""
import os
import json
from pathlib import Path
from engine import ROOT, update

SCOPES=["https://www.googleapis.com/auth/youtube.force-ssl"]


def service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    token=ROOT/"token.json"
    creds=Credentials.from_authorized_user_file(str(token),SCOPES) if token.exists() else None
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    if not creds or not creds.valid:
        flow=InstalledAppFlow.from_client_secrets_file(str(ROOT/"client.json"),SCOPES,
                                                      autogenerate_code_verifier=True)
        creds=flow.run_local_server(host="127.0.0.1",port=0,timeout_seconds=180)
    temp=ROOT/"token.tmp"
    with os.fdopen(os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600),"w") as f:
        f.write(creds.to_json())
    temp.replace(token)
    return build("youtube","v3",credentials=creds,cache_discovery=False)


def channel(api):
    items=api.channels().list(part="snippet",mine=True).execute().get("items",[])
    if not items:
        raise ValueError("No YouTube channel found for this account.")
    return items[0]["snippet"]["title"],items[0]["id"]


def post(api,job,title,description,visibility,when=None):
    from googleapiclient.http import MediaFileUpload
    j=job["id"]
    vid=job["video_id"]
    snippet={"title":title.strip(),"description":description,"categoryId":"20"}
    if not snippet["title"] or len(snippet["title"])>100:
        raise ValueError("Title must be 1–100 characters.")
    if not vid:
        request=api.videos().insert(part="snippet,status",body={"snippet":snippet,
            "status":{"privacyStatus":"private"}},media_body=MediaFileUpload(str(ROOT/j/"preview.mp4"),
            mimetype="video/mp4",resumable=True,chunksize=8*1024*1024))
        response=None
        while response is None:
            _,response=request.next_chunk(num_retries=3)
        vid=response["id"]
        update(j,video_id=vid)
    else:
        api.videos().update(part="snippet",body={"id":vid,"snippet":snippet}).execute()
    # Subtitles are already burned into the MP4. Attach a selectable track as well.
    srt=ROOT/j/"captions.srt"
    if srt.exists() and srt.stat().st_size:
        tracks=api.captions().list(part="snippet",videoId=vid).execute().get("items",[])
        if not any(t["snippet"]["name"]=="Clipper.ai" for t in tracks):
            lang=json.loads(job["result"]).get("language") or "en"
            api.captions().insert(part="snippet",body={"snippet":{"videoId":vid,"language":lang,
                "name":"Clipper.ai","isDraft":False}},media_body=MediaFileUpload(str(srt),mimetype="application/octet-stream")).execute()
    status={"privacyStatus":visibility}
    if when:
        status.update(privacyStatus="private",publishAt=when)
    api.videos().update(part="status",body={"id":vid,"status":status}).execute()
    update(j,status="Published" if visibility=="public" else "Scheduled" if when else "Uploaded",step="Uploaded")
    return vid
