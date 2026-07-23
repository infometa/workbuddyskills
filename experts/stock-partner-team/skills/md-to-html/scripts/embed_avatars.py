#!/usr/bin/env python3
from __future__ import annotations
import argparse,base64,io,re,sys
from pathlib import Path
def build_data_uri(png_path,max_size=128,quality=85):
	A=max_size
	try:from PIL import Image as B
	except ImportError:print('[embed_avatars] 缺少依赖 Pillow，请执行: pip install pillow',file=sys.stderr);raise SystemExit(1)
	C=B.open(png_path).convert('RGBA');C.thumbnail((A,A),B.LANCZOS);D=io.BytesIO();C.save(D,format='WEBP',quality=quality,method=6);E=base64.b64encode(D.getvalue()).decode('ascii');return f"data:image/webp;base64,{E}"
def embed(html_path,avatars_dir):
	K='utf-8';C=avatars_dir;A=html_path
	if not A.is_file():print(f"[embed_avatars] HTML 文件不存在: {A}",file=sys.stderr);raise SystemExit(2)
	if not C.is_dir():print(f"[embed_avatars] avatars 目录不存在: {C}",file=sys.stderr);raise SystemExit(2)
	G=A.read_text(encoding=K);H=re.compile('src="avatars/([^"/]+\\.png)"');I=sorted(set(H.findall(G)))
	if not I:print('[embed_avatars] 未发现 src="avatars/*.png" 的引用，无需处理。');return
	D=0;E=[];B={}
	for F in I:
		J=C/F
		if not J.is_file():E.append(F);continue
		B[F]=build_data_uri(J)
	def L(match):
		A=match;nonlocal D;C=A.group(1)
		if C in B:D+=1;return f'src="{B[C]}"'
		return A.group(0)
	M=H.sub(L,G);A.write_text(M,encoding=K);N=A.stat().st_size//1024;print(f"[embed_avatars] 已内嵌 {len(B)} 张头像，替换 {D} 处引用 → {A} ({N} KB)")
	if E:print(f"[embed_avatars] 警告: 以下头像文件缺失，保留相对路径不变: {E}",file=sys.stderr)
def main():
	A=argparse.ArgumentParser(description='就地内嵌圆桌报告 HTML 中的头像');A.add_argument('html_file',help='目标 HTML 文件路径');A.add_argument('avatars_dir',nargs='?',default=None,help='头像目录（默认: 脚本相对的 ../../../avatars）');B=A.parse_args()
	if B.avatars_dir:C=Path(B.avatars_dir).resolve()
	else:C=(Path(__file__).resolve().parent/'../../../avatars').resolve()
	embed(Path(B.html_file).resolve(),C)
if __name__=='__main__':main()