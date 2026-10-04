#!/usr/bin/env python3
from __future__ import annotations
_B='utf-8'
_A=True
import argparse,datetime,os,subprocess,sys
from pathlib import Path
SCRIPT_DIR=Path(__file__).resolve().parent
SHELL_PATH=SCRIPT_DIR.parent/'shell.html'
EMBED_SCRIPT=SCRIPT_DIR/'embed_avatars.py'
PLUGIN_ROOT=SCRIPT_DIR.parents[2]
INIT_TASK=PLUGIN_ROOT/'bin'/'init_task.py'
def _task_dir_from_path(path):
	A=path.expanduser().resolve()
	if A.suffix or A.is_file():A=A.parent
	B=A.parts
	try:C=B.index('deliverables')
	except ValueError:return str(A)
	if len(B)>=C+3:
		D=Path(*B[:C+3])
		try:E=A.relative_to(D)
		except ValueError:return str(D)
		if E.parts:return str(A)
		return str(D)
	if len(B)>=C+2:return str(Path(*B[:C+2]))
	return str(Path(*B[:C+1]))
def render(body_file,output_html,title,date):
	G='{{DATE}}';F='{{BODY}}';E='{{TITLE}}';B=body_file;A=output_html
	if not SHELL_PATH.is_file():print(f"[render] shell.html 缺失: {SHELL_PATH}",file=sys.stderr);raise SystemExit(2)
	if not B.is_file():print(f"[render] body 文件不存在: {B}",file=sys.stderr);raise SystemExit(2)
	C=SHELL_PATH.read_text(encoding=_B);H=B.read_text(encoding=_B)
	for D in(E,F,G):
		if D not in C:print(f"[render] shell.html 缺少占位符 {D}",file=sys.stderr);raise SystemExit(3)
	I=C.replace(E,title).replace(F,H).replace(G,date);A.parent.mkdir(parents=_A,exist_ok=_A);A.write_text(I,encoding=_B);J=A.stat().st_size//1024;print(f"[render] 已合成 → {A} ({J} KB)",flush=_A)
def embed_avatars(html_path):
	if not EMBED_SCRIPT.is_file():print(f"[render] embed_avatars.py 缺失: {EMBED_SCRIPT}",file=sys.stderr);raise SystemExit(2)
	B=[sys.executable,str(EMBED_SCRIPT),str(html_path)];A=subprocess.run(B,check=False)
	if A.returncode!=0:print(f"[render] embed_avatars 失败（退出码 {A.returncode}），已保留相对路径头像；可用当前解释器安装 Pillow 后重跑 embed_avatars.py（解释器: {sys.executable}）",file=sys.stderr)
def report_complete(anchor_path):
	E='WESTOCK_TASK_ID';D='WESTOCK_TASK_DIR'
	if not INIT_TASK.is_file():return
	A=os.environ.copy();B=A.get(D)or A.get('WESTOCK_SESSION_KEY')
	if not B:B=_task_dir_from_path(anchor_path);A[D]=B
	if not A.get(E):
		F=Path(B)/'.westock-task-id'
		try:
			C=F.read_text(encoding=_B).strip()
			if C:A[E]=C
		except OSError:pass
	try:subprocess.run([sys.executable,str(INIT_TASK),'ensure-complete'],check=False,timeout=8,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,env=A)
	except Exception:pass
def main():
	E='store_true';A=argparse.ArgumentParser(description='圆桌报告 body → 完整 HTML');A.add_argument('body_file',help='agent 写的 body 片段路径');A.add_argument('output_html',help='最终 HTML 输出路径');A.add_argument('--title',required=_A,help='HTML <title> 标签内容');A.add_argument('--date',default=None,help='报告日期 YYYY-MM-DD，默认今天');A.add_argument('--no-embed',action=E,help='跳过头像内嵌（调试用）');A.add_argument('--keep-body',action=E,help='保留 body 片段文件（默认渲染完即删）');B=A.parse_args();C=Path(B.body_file).resolve();D=Path(B.output_html).resolve();F=B.date or datetime.date.today().isoformat();render(C,D,B.title,F)
	if not B.no_embed:embed_avatars(D)
	if not B.keep_body:
		try:C.unlink();print(f"[render] 已清理 body 片段: {C.name}",flush=_A)
		except OSError as G:print(f"[render] 删除 body 片段失败（忽略）: {G}",file=sys.stderr)
	report_complete(D)
if __name__=='__main__':main()