#!/usr/bin/env python3
from __future__ import annotations
_A=True
import argparse,datetime,subprocess,sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent
SHELL_PATH=SCRIPT_DIR.parent/'shell.html'
EMBED_SCRIPT=SCRIPT_DIR/'embed_avatars.py'
PLUGIN_ROOT=SCRIPT_DIR.parents[2]
INIT_TASK=PLUGIN_ROOT/'bin'/'init_task.py'
def render(body_file,output_html,title,date):
	H='{{DATE}}';G='{{BODY}}';F='{{TITLE}}';C='utf-8';B=body_file;A=output_html
	if not SHELL_PATH.is_file():print(f"[render] shell.html 缺失: {SHELL_PATH}",file=sys.stderr);raise SystemExit(2)
	if not B.is_file():print(f"[render] body 文件不存在: {B}",file=sys.stderr);raise SystemExit(2)
	D=SHELL_PATH.read_text(encoding=C);I=B.read_text(encoding=C)
	for E in(F,G,H):
		if E not in D:print(f"[render] shell.html 缺少占位符 {E}",file=sys.stderr);raise SystemExit(3)
	J=D.replace(F,title).replace(G,I).replace(H,date);A.parent.mkdir(parents=_A,exist_ok=_A);A.write_text(J,encoding=C);K=A.stat().st_size//1024;print(f"[render] 已合成 → {A} ({K} KB)",flush=_A)
def embed_avatars(html_path):
	if not EMBED_SCRIPT.is_file():print(f"[render] embed_avatars.py 缺失: {EMBED_SCRIPT}",file=sys.stderr);raise SystemExit(2)
	B=[sys.executable,str(EMBED_SCRIPT),str(html_path)];A=subprocess.run(B,check=False)
	if A.returncode!=0:print(f"[render] embed_avatars 退出码 {A.returncode}",file=sys.stderr);raise SystemExit(A.returncode)
def report_complete():
	if not INIT_TASK.is_file():return
	try:subprocess.run([sys.executable,str(INIT_TASK),'complete'],check=False,timeout=8,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
	except Exception:pass
def main():
	E='store_true';A=argparse.ArgumentParser(description='圆桌报告 body → 完整 HTML');A.add_argument('body_file',help='agent 写的 body 片段路径');A.add_argument('output_html',help='最终 HTML 输出路径');A.add_argument('--title',required=_A,help='HTML <title> 标签内容');A.add_argument('--date',default=None,help='报告日期 YYYY-MM-DD，默认今天');A.add_argument('--no-embed',action=E,help='跳过头像内嵌（调试用）');A.add_argument('--keep-body',action=E,help='保留 body 片段文件（默认渲染完即删）');B=A.parse_args();C=Path(B.body_file).resolve();D=Path(B.output_html).resolve();F=B.date or datetime.date.today().isoformat();render(C,D,B.title,F)
	if not B.no_embed:embed_avatars(D)
	if not B.keep_body:
		try:C.unlink();print(f"[render] 已清理 body 片段: {C.name}",flush=_A)
		except OSError as G:print(f"[render] 删除 body 片段失败（忽略）: {G}",file=sys.stderr)
	report_complete()
if __name__=='__main__':main()