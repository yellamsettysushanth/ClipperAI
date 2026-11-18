# Clipper.ai • Mac edition

## Start here
1. Unzip the whole folder into Downloads. Keep its files together.
2. Double-click **Start.command**. If Finder won't launch it, open Terminal, type
   `bash ` (including the space), drag Start.command into Terminal, and press Return.
3. Leave that Terminal window running. The launcher opens the local studio in
   your browser at http://127.0.0.1:8642. Your existing Clip Watcher tabs can
   stay open. First launch downloads Python packages and FFmpeg with caption support
   through Homebrew. Internet and Homebrew are needed for setup.
4. Click **Try a sample clip**. Open **Queue**, then **Review edits → Refresh drafts**.
   Play or download the result. The included sample has supplied timed captions;
   your own videos use local speech recognition. Its model downloads on first use.

## Your clips and recordings
Drop one or more MP4/MOV/MKV/TS/WebM/M4V files into Import, or paste local paths.
To import a single YouTube video, Short, or live link, paste it and select **Import video
from this YouTube link**. The app downloads it into the local job folder, then suggests
highlights for you to choose. A live broadcast finishes downloading when the broadcast
ends; this version does not generate highlights while it is still live. YouTube may
restrict some sources, and you should only use footage you have the right to edit.
For a long stream.ts or a file above 512 MB, use its path. Browser imports are held
in memory during transfer; use paths for large batches. There is no fixed number
of jobs. Input copies, previews and job records use disk space under ~/Movies/ClipperAI.
Keep local path inputs in place until all their revisions finish.

Existing clips go straight to the editor. Full recordings get separate highlight
suggestions ranked by increases in audio intensity; this default doesn't interpret
the visuals. For transcript-based suggestions, enter an installed Ollama model name.
Pick individual highlights to render them. A YouTube or Twitch link supplies credit;
attach footage you can use. Play the source on your Mac for long-footage review.

Full frame fits the whole source in a vertical canvas. Center crop fills the
portrait frame. The app trims quiet clip edges, normalizes audio, and can burn
timed captions into the MP4. Automatic captions and scores can be wrong.
Choose Classic, Bold, Yellow, or Minimal captions when importing. In **Review edits**,
change the style and render a revised draft; the original preview remains available.
Check names, framing, and whether the highlight makes sense without context.
The current editor is optimized for footage with audio. For silent footage, turn
off captions and use Existing clips. Full recording discovery needs audio.

Move queued jobs to the front, follow progress, or retry an individual failure.
One worker processes video at a time so multiple encodes don't compete for your Mac.
Progress percentages mark stages; time estimates use finished jobs, not an encoding
benchmark. Leave the app process and Mac awake. Interrupted edits restart when
you reopen the app. No particular daily throughput has been validated.

## Revise a draft
Use one instruction at a time, for example:
- Keep the facecam
- Center crop
- Start at 5 seconds
- Trim to 20 seconds
- Replace "kay" with "Kai"

Each revision creates a new draft. You can record a commentary voiceover in the
browser; it starts at the beginning and lowers the original audio while it plays.
The clip length caps voiceover playback. Use your recording to add your perspective and preview captions after adding voiceover. Source footage
rights and the decision to publish remain yours.

Optional: install Ollama from https://ollama.com, start it and download a text
model appropriate for your Mac. Enter the exact name shown by `ollama list` in
the model field. Clipper.ai asks the local model to interpret more edit commands,
suggest a script from the transcript, or pick moments in long recordings if enabled
at import. Model output is text and validated edit settings. The app never runs
model-generated shell commands. No paid AI key is required for the core editor.

## YouTube setup (only when ready)
1. Visit https://console.cloud.google.com/ and select or create your project.
2. Enable **YouTube Data API v3**. Configure the OAuth consent screen with your
   account as a test user if using testing mode. Under Credentials, create
   **OAuth client ID → Desktop app** and download the JSON file.
3. In the studio's **YouTube** tab, choose that JSON and click **Sign in with Google**.
   Use the browser consent screen. Confirm the channel name in the app.
4. Select reviewed drafts, edit titles and descriptions, and choose **Approve
   and upload**. The first batch uses private visibility. Check the private upload
   in YouTube Studio. Later uploads can be private, unlisted, public, or scheduled
   for a UTC time. A scheduled batch uses the same time for all selected clips.
5. Keep the app running during transfer. A saved YouTube video ID is reused if
   a later caption or visibility update fails. Review the displayed error and
   your YouTube Studio listings before retrying an interrupted transfer.

After connecting, you can save **Automatic posting for future drafts** in the YouTube
tab. Only new jobs queued after saving inherit this setting. A job marked Ready uploads
automatically with its source credit and chosen visibility; jobs needing review stay
local. Start with Private and check your channel before enabling Public. Automatic
uploads need a valid saved OAuth token; if it expires without a refresh token, the
draft stays in Needs review and you can reconnect. Changing the settings does not
publish already queued drafts.

Video and audio stay on your computer until you approve uploading. Google sign-in
uses a desktop OAuth client with the youtube.force-ssl scope (required by caption
track management). Google credentials and refresh tokens are local to
~/Movies/ClipperAI. Do not share that folder. To disconnect, revoke the app at
https://myaccount.google.com/permissions, close the studio, and remove token.json
from that folder. For API details, see https://developers.google.com/youtube/v3.

## Storage
Download any MP4 you want to keep independently. Browser-uploaded inputs are
saved once by file content in the sources subfolder. Clips from the same file
queued more than once may be flagged for review. This is exact-source detection,
not visual near-duplicate matching. Each draft has its own output folder.
