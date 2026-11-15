# Final integration change review: original old catalog links are mapped to local hubs.
#!/usr/bin/env python3
"""Read-only comprehensive prompt #46 audit of Phantom local migration.

Checks root HTML, local links and anchors, source-vs-local links, navigation,
scheme assets, metadata, shared scripts and integrity of imported documents.
Writes a reproducible JSON report. Does not fetch URLs or modify site pages.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import json
import posixpath
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/"docs/PHANTOM_FINAL_MIGRATION_46.json"
EXPECTED="""atom-energy.html stantsiya-zapisi.html industrial.html government.html financial.html commercial.html auto-dealers.html phantom-micro.html phantom-boards.html phantom-active.html ip-telephony.html phantom-catalog.html connection-schemes.html personal-solutions.html modernization.html training.html telephone-recording.html dispatcher-recording.html pultex.html phantom-cross.html phantom-monitoring.html phantom-asr.html support.html company.html news.html certificates.html clients.html partners.html history.html rewards.html requisites.html articles.html services.html reviews.html faq.html support-phantom-cross.html support-phantom-active.html support-phantom-4.html support-phantom-2.html support-phantom-ultra.html support-stantsiya-zapisi.html solutions.html privacy-policy.html cookie-policy.html""".split()
UNWANTED="""scheme-ip-traffic.html scheme-tricom-gip.html scheme-minicom.html scheme-mixed-protocols.html phantom-pc.html phantom-pro.html contacts.html vacancies.html faq-general.html faq-install.html faq-functions.html faq-commercial.html""".split()
LEGACY=re.compile(r"^0[6-9]_.*\.html$",re.I)

class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids=[];self.refs=[];self.meta={};self.h1=0
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if a.get("id"):self.ids.append(a["id"])
        if tag=="h1":self.h1+=1
        if tag=="meta" and a.get("name"):self.meta[a["name"].lower()]=a.get("content","")
        for attr in ("href","src","poster","action","data-src"):
            if a.get(attr):self.refs.append({"tag":tag,"attr":attr,"url":a[attr]})
        if a.get("srcset"):
            for s in a["srcset"].split(","):
                if s.strip():self.refs.append({"tag":tag,"attr":"srcset","url":s.strip().split()[0]})
    def handle_startendtag(self,tag,attrs):self.handle_starttag(tag,attrs)

def parsed(path):
    p=Page()
    p.feed(path.read_text(encoding="utf-8-sig"))
    p.close()
    return p

def digest(path):
    h=sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def classify(url):
    a=urlsplit(url)
    host=a.netloc.lower()
    if host in ("mdis.ru","www.mdis.ru"):
        if a.path.endswith(".mp4"):return "pending_video_Rutube"
        if a.path.startswith("/upload/"):return "original_document_or_download"
        if a.path.startswith(("/privacy-policy/","/cookie-policy/")):return "legal_text_or_original"
        if "/news/" in a.path or "/article" in a.path:return "historical_news_or_article"
        if a.path=="/":return "official_website_brand"
        return "old_site_page_needs_review"
    if host.endswith("granulex.ru"):return "external_Granulex"
    return "other_external"

def run():
    all_pages=sorted(ROOT.glob("*.html"))
    pages={x.name:parsed(x) for x in all_pages}
    main_pages=[x for x in all_pages if not LEGACY.match(x.name)]
    findings=[];old=[];externals=[];checked=0
    def finding(kind,file,value,severity="ERROR"):
        findings.append({"severity":severity,"kind":kind,"file":file,"value":value})
    for f in all_pages:
        p=pages[f.name];historic=bool(LEGACY.match(f.name))
        duplicate={k:v for k,v in Counter(p.ids).items() if v>1}
        if duplicate:finding("duplicate_ids",f.name,duplicate)
        if not historic:
            if p.h1!=1:finding("h1_count",f.name,p.h1)
            if p.meta.get("robots","").replace(" ","").lower()!="noindex,nofollow":
                finding("noindex_missing",f.name,p.meta.get("robots",""))
            raw=f.read_text(encoding="utf-8-sig")
            for shared in ("assets/site-header.js","assets/footer-next.js"):
                if shared not in raw:finding("shared_js_missing",f.name,shared)
        for ref in p.refs:
            checked+=1
            url=ref["url"].strip()
            if not url:continue
            a=urlsplit(url)
            if a.scheme in ("mailto","tel"):
                if a.scheme=="mailto" and "@" not in a.path:finding("bad_mailto",f.name,url)
                if re.search(r"%(?![a-fA-F0-9]{2})",url):finding("url_encoding",f.name,url)
                continue
            if a.scheme in ("http","https") or a.netloc:
                item={"page":f.name,"tag":ref["tag"],"url":url,"category":classify(url)}
                externals.append(item)
                if a.netloc.lower() in ("mdis.ru","www.mdis.ru"):old.append(item)
                continue
            if a.scheme or url.startswith(("data:","javascript:")):continue
            if a.path.startswith("/"):
                finding("root_absolute_path",f.name,url);continue
            if a.path:
                name=posixpath.normpath(unquote(a.path))
                target=(ROOT/name).resolve()
                if ROOT.resolve() not in target.parents and target!=ROOT.resolve():
                    finding("escape_from_root",f.name,url);continue
                if not target.exists() or target.is_dir():
                    finding("broken_local_path",f.name,url);continue
                if a.fragment and name.endswith(".html") and name in pages:
                    if unquote(a.fragment) not in pages[name].ids:
                        finding("broken_crosspage_anchor",f.name,url)
            elif a.fragment and url!="#" and unquote(a.fragment) not in p.ids:
                finding("anchor_not_static",f.name,url,"REVIEW")
    for expected in EXPECTED:
        if expected not in pages:finding("missing_expected", "[inventory]",expected)
    for name in UNWANTED:
        if name in pages:finding("duplicate_unwanted", "[inventory]",name)
    scheme=pages.get("connection-schemes.html")
    if scheme:
        for id in ("ip-principle","tricom","minicom","protocols"):
            if id not in scheme.ids:finding("scheme_anchor_missing","connection-schemes.html",id)
        imgs=[r["url"] for r in scheme.refs if r["tag"]=="img" and r["attr"]=="src"]
        if len(imgs)!=4:finding("scheme_images_count","connection-schemes.html",len(imgs))
        for link in imgs:
            if link.startswith("http"):finding("scheme_hotlinked","connection-schemes.html",link)
    if (ROOT/"phantom-home.html").is_file():
        raw=(ROOT/"phantom-home.html").read_text(encoding="utf-8")
        if not re.search(r'class="solutions-switcher-label" href="solutions.html"',raw):
            finding("all_solutions_link","phantom-home.html","Not linked to local solutions hub")
    for file,links in {
        "assets/site-header.js":["solutions.html","phantom-catalog.html","support.html","company.html","services.html","news.html","privacy-policy.html","cookie-policy.html"],
        "assets/footer-next.js":["solutions.html","phantom-catalog.html","support.html","company.html","services.html","news.html","privacy-policy.html","cookie-policy.html"],
    }.items():
        contents=(ROOT/file).read_text(encoding="utf-8")
        for link in links:
            if link not in contents:finding("shared_navigation_missing",file,link,"REVIEW")
    manifest_results=[]
    for name in ("assets/support/pdf-manifest.json","assets/support/word-manifest.json","assets/support/legacy-media-manifest.json"):
        m=ROOT/name
        if not m.exists():continue
        rows=json.loads(m.read_text(encoding="utf-8"))
        for r in rows:
            target=ROOT/r.get("path",r.get("target"))
            if not target.is_file():finding("missing_manifest_asset",name,str(target));continue
            if target.stat().st_size!=r["bytes"] or digest(target)!=r["sha256"]:
                finding("manifest_integrity",name,target.name)
        manifest_results.append({"path":name,"count":len(rows),"bytes":sum(x["bytes"] for x in rows)})
    stats=Counter(x["category"] for x in externals)
    report={
        "base_sha":"1b02a502777878c077d4dbe2f80080ce6bd67d1b",
        "source_prompt":"prompts/46_Финальная_интеграция_и_проверка_миграции.md",
        "root_html_files":len(all_pages),
        "canonical_root_html_files":len(main_pages),
        "numbered_legacy_html":[f.name for f in all_pages if LEGACY.match(f.name)],
        "expected_pages":len(EXPECTED),
        "missing_expected":[f for f in EXPECTED if f not in pages],
        "unwanted_duplicate_pages":[f for f in UNWANTED if f in pages],
        "html_references_checked":checked,
        "external_total":len(externals),
        "external_categories":dict(stats),
        "mdis_links_total":len(old),
        "mdis_links":old,
        "asset_manifests":manifest_results,
        "findings":findings,
        "error_count":sum(x["severity"]=="ERROR" for x in findings),
        "review_count":sum(x["severity"]=="REVIEW" for x in findings),
    }
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("FINAL_MIGRATION_SUMMARY",json.dumps({k:v for k,v in report.items() if k not in ("mdis_links","findings")},ensure_ascii=False),flush=True)
    for f in findings:print("FINDING",json.dumps(f,ensure_ascii=False),flush=True)
    for u in old:print("MDIS_EXTERNAL",json.dumps(u,ensure_ascii=False),flush=True)
    print("REPORT_FILE",REPORT.relative_to(ROOT),flush=True)
    return report["error_count"]
if __name__=="__main__":
    raise SystemExit(1 if run() else 0)
