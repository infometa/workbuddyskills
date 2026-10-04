#!/usr/bin/env python3
from __future__ import annotations
_N='fstart_time'
_M='fwzq_openid'
_L='fstage'
_K='fscene'
_J='fchannel'
_I='start_ts'
_H='task_id'
_G='task_dir'
_F='ensure-complete'
_E='complete'
_D=False
_C='utf-8'
_B=None
_A=True
import hashlib,json,os,sys,time,urllib.request,uuid
from pathlib import Path
INLONG_GROUP_ID='b_cdg_cft_msg_zq'
INLONG_CLUSTER_TAG='hn_cdgcft4'
INLONG_STREAM_ID='workbuddy_connector_expert'
FCHANNEL='workbuddy'
FSCENE='expert'
REQUEST_TIMEOUT_S=3
STALE_AFTER_MS=21600000
STATE_DIR=Path.home()/'.westock-stock-partner'
DEV_ID_FILE=STATE_DIR/'dev_id'
TASK_ID_FILENAME='.westock-task-id'
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
def _resolve_task_dir(*,anchor=_B):
	B=anchor
	for C in('WESTOCK_TASK_DIR','WESTOCK_SESSION_KEY'):
		A=os.environ.get(C,'').strip()
		if A:
			try:return str(Path(A).expanduser().resolve())
			except OSError:return A
	if B is not _B:return _task_dir_from_path(B)
	try:return _task_dir_from_path(Path.cwd())
	except OSError:return
def _dir_hash(task_dir):return hashlib.md5(task_dir.encode(_C)).hexdigest()[:16]
def _marker_path(task_id):return STATE_DIR/f"task-{task_id}.json"
def _index_dir(task_dir):return STATE_DIR/f"dir-{_dir_hash(task_dir)}"
def _index_link(task_dir,task_id):return _index_dir(task_dir)/task_id
def _pending_ids(task_dir):
	A=_index_dir(task_dir)
	try:B=sorted(A.name for A in A.iterdir()if A.is_file()and _marker_path(A.name).is_file())
	except OSError:return[]
	return B
def _sweep_task_dir(task_dir,now_ms):
	C=_index_dir(task_dir)
	try:D=list(C.iterdir())
	except OSError:return
	for A in D:
		try:
			B=_marker_path(A.name)
			if B.is_file():
				E=now_ms-int(B.stat().st_mtime*1000)
				if E>STALE_AFTER_MS:
					try:B.unlink()
					except OSError:pass
					try:A.unlink()
					except OSError:pass
			else:A.unlink()
		except OSError:pass
def _atomic_write(path,text):
	A=path;A.parent.mkdir(parents=_A,exist_ok=_A);B=A.with_name(f"{A.name}.{os.getpid()}.tmp")
	try:B.write_text(text,encoding=_C);os.replace(str(B),str(A))
	except OSError:
		try:B.unlink()
		except OSError:pass
		raise
ESCAPE_MAP={'\x00':'\\0','\r':'\\r','\n':'\\n','\\':'\\\\','|':'\\|'}
def _escape(value):return''.join(ESCAPE_MAP.get(A,A)for A in value)
def _dev_id():
	try:
		A=DEV_ID_FILE.read_text(encoding=_C).strip()
		if A:return A
	except(OSError,ValueError):pass
	B=f"dev-{uuid.uuid4()}"
	try:
		STATE_DIR.mkdir(parents=_A,exist_ok=_A);C=os.open(str(DEV_ID_FILE),os.O_CREAT|os.O_EXCL|os.O_WRONLY,420)
		try:os.write(C,B.encode(_C))
		finally:os.close(C)
		return B
	except FileExistsError:
		try:
			A=DEV_ID_FILE.read_text(encoding=_C).strip()
			if A:return A
		except(OSError,ValueError):pass
		return B
	except OSError:return B
def _post(fdata):
	A=int(time.time()*1000);B=json.dumps({'fdata':fdata,'ftimestamp':A},ensure_ascii=_D);C=json.dumps({'groupId':INLONG_GROUP_ID,'streamId':INLONG_STREAM_ID,'body':_escape(B),'cnt':'1','dt':str(A)}).encode(_C);D=urllib.request.Request(f"https://trace.inlong.qq.com/{INLONG_CLUSTER_TAG}/dataproxy/message",data=C,headers={'Content-Type':'application/json'},method='POST')
	try:
		with urllib.request.urlopen(D,timeout=REQUEST_TIMEOUT_S):return
	except Exception as E:
		F=os.environ.get('WESTOCK_TELEMETRY_DEBUG','').strip().lower()
		if F in{'1','true','yes','on'}:print(f"[init_task] post failed: {E}",file=sys.stderr)
		return
def _resolve_task_id(task_dir):
	B=task_dir;C=os.environ.get('WESTOCK_TASK_ID','').strip()
	if C:return C
	if len(sys.argv)>=3 and sys.argv[1]in{_E,_F}:
		A=sys.argv[2].strip()
		if A and not A.startswith('-'):return A
	if not B:return
	E=Path(B)/TASK_ID_FILENAME
	try:
		D=E.read_text(encoding=_C).strip()
		if D:return D
	except OSError:pass
def _claim_marker(task_id):
	B=task_id;C=_marker_path(B);D=C.with_name(f"{C.name}.claim.{os.getpid()}")
	try:os.replace(str(C),str(D))
	except OSError:return
	A={}
	try:A=json.loads(D.read_text(encoding=_C))
	except Exception:A={}
	try:D.unlink()
	except OSError:pass
	E=A.get(_G)
	if isinstance(E,str)and E:
		try:_index_link(E,B).unlink()
		except OSError:pass
	A[_H]=B;return A
def cmd_start():
	A=_resolve_task_dir()
	if not A:return
	D=_dev_id();C=int(time.time()*1000);B=uuid.uuid4().hex
	try:
		STATE_DIR.mkdir(parents=_A,exist_ok=_A);_sweep_task_dir(A,C);E={_I:C,_H:B,_G:A};_atomic_write(_marker_path(B),json.dumps(E,ensure_ascii=_D));_atomic_write(_index_link(A,B),B)
		try:Path(A).mkdir(parents=_A,exist_ok=_A);_atomic_write(Path(A)/TASK_ID_FILENAME,B)
		except OSError:pass
	except OSError:pass
	_post({_J:FCHANNEL,_K:FSCENE,_L:'task_start',_M:D,_N:C})
def cmd_complete():
	C=_resolve_task_dir();B=_resolve_task_id(C)
	if not B and C:
		E=_pending_ids(C)
		if len(E)==1:B=E[0]
		else:return
	if not B:return
	F=_claim_marker(B)
	if F is _B:return
	G=int(time.time()*1000);A=_B
	try:A=int(F[_I])
	except Exception:A=_B
	H=_D
	if A is not _B:
		I=G-A
		if not 0<=I<=STALE_AFTER_MS:A=_B;H=_A
	D={_J:FCHANNEL,_K:FSCENE,_L:'task_complete',_M:_dev_id(),'fsuccess':_A}
	if A is not _B:
		D[_N]=A
		if not H:D['fcost_time']=G-A
	_post(D)
def cmd_ensure_complete():
	try:cmd_complete()
	except Exception:pass
def main():
	B='dev-id';A=sys.argv[1]if len(sys.argv)>1 else B
	if A=='start':cmd_start()
	elif A==_E:cmd_complete()
	elif A==_F:cmd_ensure_complete()
	elif A==B:print(_dev_id())
	else:print('用法: WESTOCK_TASK_DIR=<产物目录> python3 bin/init_task.py [start|complete|ensure-complete|dev-id]',file=sys.stderr);raise SystemExit(2)
if __name__=='__main__':main()