#!/usr/bin/env python3
from __future__ import annotations
_G='fwzq_openid'
_F='fstage'
_E='fscene'
_D='fchannel'
_C='start_ts'
_B=True
_A='utf-8'
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
def _session_key():
	B=os.environ.get('WESTOCK_SESSION_KEY')
	if B:return B
	try:A=Path(os.getcwd()).resolve()
	except OSError:return'default'
	for C in(A,*A.parents):
		try:
			if(C/'.git').exists():return str(C)
		except OSError:break
	return str(A)
def _task_prefix():return f"task-{hashlib.md5(_session_key().encode(_A)).hexdigest()[:16]}"
def _new_task_file(start_ts):return STATE_DIR/f"{_task_prefix()}-{start_ts:013d}-{os.getpid()}-{uuid.uuid4().hex[:6]}.json"
def _pending_task_files():
	try:return sorted(STATE_DIR.glob(f"{_task_prefix()}-*.json"))
	except Exception:return[]
def _sweep(now_ms):
	try:B=list(STATE_DIR.glob(f"{_task_prefix()}*"))
	except Exception:return
	for A in B:
		try:
			if now_ms-int(A.stat().st_mtime*1000)>STALE_AFTER_MS:A.unlink()
		except OSError:pass
def _atomic_write(path,text):
	A=path;B=A.with_name(f"{A.name}.{os.getpid()}.tmp")
	try:B.write_text(text,encoding=_A);os.replace(str(B),str(A))
	except OSError:
		try:B.unlink()
		except OSError:pass
		raise
ESCAPE_MAP={'\x00':'\\0','\r':'\\r','\n':'\\n','\\':'\\\\','|':'\\|'}
def _escape(value):return''.join(ESCAPE_MAP.get(A,A)for A in value)
def _dev_id():
	try:
		A=DEV_ID_FILE.read_text(encoding=_A).strip()
		if A:return A
	except(OSError,ValueError):pass
	B=f"dev-{uuid.uuid4()}"
	try:
		STATE_DIR.mkdir(parents=_B,exist_ok=_B);C=os.open(str(DEV_ID_FILE),os.O_CREAT|os.O_EXCL|os.O_WRONLY,420)
		try:os.write(C,B.encode(_A))
		finally:os.close(C)
		return B
	except FileExistsError:
		try:
			A=DEV_ID_FILE.read_text(encoding=_A).strip()
			if A:return A
		except(OSError,ValueError):pass
		return B
	except OSError:return B
def _post(fdata):
	A=int(time.time()*1000);B=json.dumps({'fdata':fdata,'ftimestamp':A},ensure_ascii=False);C=json.dumps({'groupId':INLONG_GROUP_ID,'streamId':INLONG_STREAM_ID,'body':_escape(B),'cnt':'1','dt':str(A)}).encode(_A);D=urllib.request.Request(f"https://trace.inlong.qq.com/{INLONG_CLUSTER_TAG}/dataproxy/message",data=C,headers={'Content-Type':'application/json'},method='POST')
	try:
		with urllib.request.urlopen(D,timeout=REQUEST_TIMEOUT_S):return
	except Exception:return
def cmd_start():
	B=_dev_id();A=int(time.time()*1000)
	try:STATE_DIR.mkdir(parents=_B,exist_ok=_B);_sweep(A);_atomic_write(_new_task_file(A),json.dumps({_C:A}))
	except OSError:pass
	_post({_D:FCHANNEL,_E:FSCENE,_F:'task_start',_G:B})
def cmd_complete():
	B=None;G=int(time.time()*1000);A=B;E=False
	for C in _pending_task_files():
		D=C.with_name(f"{C.name}.claim.{os.getpid()}")
		try:os.replace(str(C),str(D))
		except OSError:continue
		A=B
		try:A=G-int(json.loads(D.read_text(encoding=_A))[_C])
		except Exception:pass
		try:D.unlink()
		except OSError:pass
		if A is not B and not 0<=A<=STALE_AFTER_MS:continue
		E=_B;break
	if not E:return
	F={_D:FCHANNEL,_E:FSCENE,_F:'task_complete',_G:_dev_id(),'fsuccess':_B}
	if A is not B:F['fcost_time']=A
	_post(F)
def main():
	B='dev-id';A=sys.argv[1]if len(sys.argv)>1 else B
	if A=='start':cmd_start()
	elif A=='complete':cmd_complete()
	elif A==B:print(_dev_id())
	else:print('用法: python3 bin/init_task.py [start|complete|dev-id]',file=sys.stderr);raise SystemExit(2)
if __name__=='__main__':main()
