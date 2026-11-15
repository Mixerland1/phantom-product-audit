#!/usr/bin/env python3
"""Archive official MDIS legacy downloads without altering original bytes.

Four sub-100-MB RAR/ZIP distributions are stored as same-origin site assets.
Two >50-MB MP4 recordings are placed in a GitHub Release (100-MB Git blob limit);
the public pages link directly to those publisher-hosted release assets.
Never execute extracted files or claim that videos are served from site origin.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"assets/support/legacy-media-manifest.json"
TAG="phantom-support-media-20261115"
OWNER="Mixerland1/phantom-product-audit"
ASSETS=[
  {"page":"support-phantom-2.html","kind":"archive","url":"https://mdis.ru/upload/iblock/ac5/ac503ee2bb08cfee9be9795d499e50fe.rar"},
  {"page":"support-phantom-2.html","kind":"archive","url":"https://mdis.ru/upload/iblock/c41/c41342b68e31dd4d0c5237ac11a60c53.zip"},
  {"page":"support-phantom-2.html","kind":"archive","url":"https://mdis.ru/upload/iblock/0d2/0d26de81c315bc07de62b5b1554f0c5f.rar"},
  {"page":"support-phantom-2.html","kind":"archive","url":"https://mdis.ru/upload/iblock/b89/b89ccb97df04c6d346f24dbad01c1e02.rar"},
  {"page":"support-phantom-2.html","kind":"video","url":"https://mdis.ru/upload/iblock/698/698df4b84c9601a56bd472681149a94c.mp4"},
  {"page":"support-phantom-4.html","kind":"video","url":"https://mdis.ru/upload/iblock/c92/c92d52d725a8b52f6388e629b0c1d53e.mp4"},
]

def run(args, **kwargs):
  return subprocess.run(args,check=True,text=True,**kwargs)

def checksum(path):
  h=hashlib.sha256()
  with path.open("rb") as f:
    for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
  return h.hexdigest()

def get(url,path):
  if path.exists() and path.stat().st_size>1000: return
  cmd=["curl","--fail","--location","--silent","--show-error","--retry","3",
       "--retry-all-errors","--retry-delay","3","--connect-timeout","25","--max-time","1800",
       "--continue-at","-","--user-agent","Mozilla/5.0 (MDIS original asset archive)",
       "--output",str(path),url]
  run(cmd,timeout=1950)
  if not path.exists():raise RuntimeError(f"Missing downloaded source: {url}")
  print("DOWNLOADED",url.rsplit("/",1)[-1],path.stat().st_size,flush=True)

def archive_ok(path):
  if not 1000<path.stat().st_size<100*1024*1024:raise ValueError(f"Unexpected archive size {path.name}")
  with path.open("rb") as f:header=f.read(16)
  if path.suffix==".zip":
    if not header.startswith(b"PK\x03\x04"):raise ValueError("Invalid ZIP header")
    with zipfile.ZipFile(path) as z:
      if z.testzip() is not None:raise ValueError(f"Damaged ZIP: {path.name}")
      names=z.namelist()
  else:
    if not header.startswith(b"Rar!\x1a\x07"):raise ValueError(f"Invalid RAR signature: {header!r}")
    p=subprocess.run(["7z","t","-y",str(path)],capture_output=True,text=True,timeout=120)
    if p.returncode:raise ValueError(f"RAR validation failed: {path.name}: {p.stdout[-700:]} {p.stderr[-200:]}")
    names=[]
  print("ARCHIVE_OK",path.name,path.stat().st_size,"zip_items",len(names),flush=True)

def video_ok(path):
  if not 1024*1024<path.stat().st_size<700*1024*1024:raise ValueError(f"Unexpected MP4 size: {path}")
  with path.open("rb") as f:header=f.read(32)
  if b"ftyp" not in header[:20]:raise ValueError(f"No ISO base media header: {path.name}")
  info=json.loads(run(["ffprobe","-v","error","-show_entries",
        "format=duration,format_name:stream=codec_type,codec_name",
        "-of","json",str(path)],capture_output=True,timeout=90).stdout)
  if not any(s.get("codec_type")=="video" for s in info.get("streams",[])):raise ValueError(f"No video stream in {path.name}")
  duration=float(info["format"]["duration"])
  if duration<5:raise ValueError(f"Suspicious duration {duration}: {path.name}")
  print("VIDEO_OK",path.name,path.stat().st_size,round(duration,1),"seconds",flush=True)
  return duration

def ensure_release():
  r=subprocess.run(["gh","release","view",TAG,"--repo",OWNER],capture_output=True,text=True)
  if r.returncode==0:return
  run(["gh","release","create",TAG,"--repo",OWNER,"--target","main","--title",
       "Original Phantom 2 and Phantom 4 support videos",
       "--notes","Original archived video instructions from the manufacturer. Byte-for-byte originals; SHA-256 recorded in assets/support/legacy-media-manifest.json.",
       "--prerelease"],timeout=75)
  print("RELEASE_CREATED",TAG,flush=True)

def published_video_asset(name,size,digest):
  raw=run(["gh","release","view",TAG,"--repo",OWNER,"--json","assets"],capture_output=True,timeout=80).stdout
  assets=json.loads(raw)["assets"]
  matches=[a for a in assets if a["name"]==name]
  if len(matches)!=1:raise ValueError(f"Missing release asset {name}")
  found=matches[0]
  if found["size"]!=size:raise ValueError(f"Release size differs {name}: {found['size']} vs {size}")
  # GitHub asset.digest is sha256:<hex> on modern GitHub; validate if exposed.
  gh_digest=found.get("digest")
  if gh_digest and gh_digest!=f"sha256:{digest}":raise ValueError(f"Release SHA mismatch {name}")
  print("RELEASE_VERIFIED",name,size,gh_digest or "size-confirmed",flush=True)

def read_manifest():
  if not MANIFEST.exists():return []
  return json.loads(MANIFEST.read_text(encoding="utf-8"))

def store(rows):
  MANIFEST.parent.mkdir(parents=True,exist_ok=True)
  MANIFEST.write_text(json.dumps(sorted(rows,key=lambda r:(r["kind"],r["page"],r["source"])),ensure_ascii=False,indent=2)+"\n",encoding="utf-8")

def replace(page,source,target,video=False):
  path=ROOT/page
  html=path.read_text(encoding="utf-8")
  if html.count(source)!=1:raise ValueError(f"Expected one source in {page}: {source}, count={html.count(source)}")
  html=html.replace(source,target)
  if video and page=="support-phantom-4.html":
    html=html.replace('aria-label="Смотреть видео в новой вкладке: Установка Phantom 4.10"','aria-label="Скачать видео: Установка Phantom 4.10"')
    html=html.replace('>Смотреть видео <span','>Скачать видео <span')
  if video and page=="support-phantom-2.html":
    html=html.replace('>Открыть видеоинструкцию<span','>Скачать видеоинструкцию<span')
  path.write_text(html,encoding="utf-8")

def migrate(kind):
  chosen=[a for a in ASSETS if a["kind"]==kind]
  if not chosen:raise ValueError(kind)
  previous=read_manifest()
  with tempfile.TemporaryDirectory(prefix=f"phantom-{kind}-") as tmp:
    rows=[]
    for a in chosen:
      name=a["url"].rsplit("/",1)[-1]
      destination=f"assets/support/{Path(a['page']).stem}/{name}" if kind=="archive" else f"https://github.com/{OWNER}/releases/download/{TAG}/{name}"
      path=ROOT/destination if kind=="archive" else Path(tmp)/name
      path.parent.mkdir(parents=True,exist_ok=True)
      get(a["url"],path)
      duration=video_ok(path) if kind=="video" else (archive_ok(path) or None)
      row=dict(kind=kind,page=a["page"],source=a["url"],target=destination,bytes=path.stat().st_size,sha256=checksum(path))
      if kind=="video":row["duration_seconds"]=round(duration,2)
      rows.append(row)
    if kind=="video":
      ensure_release()
      for row in rows:
        p=Path(tmp)/row["source"].rsplit("/",1)[-1]
        # Prior upload check allows reruns without duplicates.
        existing=subprocess.run(["gh","release","view",TAG,"--repo",OWNER,"--json","assets"],capture_output=True,text=True)
        names=[x["name"] for x in json.loads(existing.stdout)["assets"]]
        if p.name not in names:
          run(["gh","release","upload",TAG,str(p),"--repo",OWNER],timeout=1200)
        published_video_asset(p.name,row["bytes"],row["sha256"])
  # Only after all originals and (if relevant) release assets are validated.
  for row in rows:replace(row["page"],row["source"],row["target"],video=kind=="video")
  store([x for x in previous if x["kind"]!=kind]+rows)
  print("MIGRATED",kind,len(rows),flush=True)

def verify():
  rows=read_manifest()
  for row in rows:
    html=(ROOT/row["page"]).read_text(encoding="utf-8")
    if row["source"] in html or f'href="{row["target"]}"' not in html:
      raise ValueError(f"Invalid localized link: {row['page']}/{row['target']}")
    if row["kind"]=="archive":
      p=ROOT/row["target"]
      archive_ok(p)
      if p.stat().st_size!=row["bytes"] or checksum(p)!=row["sha256"]:raise ValueError(f"SHA-256 mismatch: {p}")
    if row["kind"]=="video" and os.environ.get("GH_TOKEN"):
      published_video_asset(row["source"].rsplit("/",1)[-1],row["bytes"],row["sha256"])
  print("VERIFIED",len(rows),"legacy archive/video links and original checksums",flush=True)

if __name__=="__main__":
  p=argparse.ArgumentParser()
  modes=p.add_mutually_exclusive_group(required=True)
  modes.add_argument("--archives",action="store_true")
  modes.add_argument("--videos",action="store_true")
  modes.add_argument("--verify",action="store_true")
  a=p.parse_args()
  if a.archives:migrate("archive")
  elif a.videos:migrate("video")
  else:verify()
