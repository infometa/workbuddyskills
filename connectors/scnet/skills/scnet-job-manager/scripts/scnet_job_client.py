#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SCNet Job Client
"""

import hashlib
import hmac
import json
import os
import shlex
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Optional
import requests

from constant import SCNET_CENTER_URL, SCNET_TOKEN_URL

class JobStatus(Enum):
    statQ = ("statQ", "排队中")
    statR = ("statR", "运行中")
    statC = ("statC", "已完成")
    statDE = ("statDE", "取消")
    statD = ("statD", "失败")
    statEX = ("statEX", "异常")
    statE = ("statE", "退出")
    statH = ("statH", "保留")
    statS = ("statS", "挂起")
    statW = ("statW", "等待")
    statX = ("statX", "其他")
    statT = ("statT", "超时")
    statN = ("statN", "节点异常")
    statRQ = ("statRQ", "重新运行")

    def __init__(self, code, zh):
        self.code = code
        self.zh = zh

    @property
    def label(self):
        return self.zh


class SCNetJobClient:
    CACHE_DIR_RELATIVE = Path(".data") / "tokens"
    TOKEN_CACHE_TTL_SECONDS = 4 * 60 * 60
    TOKEN_CACHE_FILENAME = "scnet_tokens_cache.json"
    TOKEN_CACHE_LOCK_FILENAME = "scnet_tokens_cache.lock"
    CLUSTER_MAP_CACHE_TTL_SECONDS = 24 * 60 * 60
    CLUSTER_MAP_CACHE_FILENAME = "scnet_cluster_map_cache.json"
    CLUSTER_MAP_CACHE_LOCK_FILENAME = "scnet_cluster_map_cache.lock"
    """SCNet 作业相关客户端。"""

    access_key: str = ""
    secret_key: str = ""
    user: str = ""
    cluster_map: Dict[str, Dict[str, Any]] = {}

    def __init__(self, access_key: str, secret_key: str, user: str):
        self.access_key = access_key
        self.secret_key = secret_key
        self.user = user
        self._cluster_map_error: Optional[Dict[str, str]] = None

    def _set_cluster_map_error(self, stage: str, code: str, message: str) -> None:
        self._cluster_map_error = {
            "stage": stage,
            "code": code,
            "message": message,
        }

    @classmethod
    def _cache_dir(cls) -> Path:
        home_dir = os.getenv("HOME", "").strip()
        if not home_dir:
            raise ValueError("HOME environment variable is required")
        cache_dir = Path(home_dir) / cls.CACHE_DIR_RELATIVE
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    @classmethod
    def _token_cache_path(cls) -> Path:
        return cls._cache_dir() / cls.TOKEN_CACHE_FILENAME

    @classmethod
    def _token_cache_lock_path(cls) -> Path:
        return cls._cache_dir() / cls.TOKEN_CACHE_LOCK_FILENAME

    @classmethod
    def _cluster_map_cache_path(cls) -> Path:
        return cls._cache_dir() / cls.CLUSTER_MAP_CACHE_FILENAME

    @classmethod
    def _cluster_map_cache_lock_path(cls) -> Path:
        return cls._cache_dir() / cls.CLUSTER_MAP_CACHE_LOCK_FILENAME

    @classmethod
    def _read_token_cache(cls) -> Optional[Dict[str, Any]]:
        cache_path = cls._token_cache_path()
        if not cache_path.exists():
            return None

        try:
            with cache_path.open("r", encoding="utf-8") as fh:
                cached = json.load(fh)
            if isinstance(cached, dict):
                return cached
        except Exception as exc:
            print(f"read token cache failed: {exc}")
        return None

    @classmethod
    def _write_token_cache(cls, payload: Dict[str, Any]) -> None:
        cache_path = cls._token_cache_path()
        temp_path = cache_path.with_suffix(f"{cache_path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        os.replace(temp_path, cache_path)

    @classmethod
    def _read_cluster_map_cache(cls) -> Optional[Dict[str, Any]]:
        cache_path = cls._cluster_map_cache_path()
        if not cache_path.exists():
            return None

        try:
            with cache_path.open("r", encoding="utf-8") as fh:
                cached = json.load(fh)
            if isinstance(cached, dict):
                return cached
        except Exception as exc:
            print(f"read cluster map cache failed: {exc}")
        return None

    @classmethod
    def _write_cluster_map_cache(cls, payload: Dict[str, Any]) -> None:
        cache_path = cls._cluster_map_cache_path()
        temp_path = cache_path.with_suffix(f"{cache_path.suffix}.tmp")
        with temp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False)
        os.replace(temp_path, cache_path)

    @classmethod
    def _acquire_token_cache_lock(cls, timeout_seconds: float = 10.0, poll_interval: float = 0.2) -> bool:
        lock_path = cls._token_cache_lock_path()
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return True
            except FileExistsError:
                time.sleep(poll_interval)
            except Exception as exc:
                print(f"acquire token cache lock failed: {exc}")
                return False
        return False

    @classmethod
    def _release_token_cache_lock(cls) -> None:
        lock_path = cls._token_cache_lock_path()
        try:
            if lock_path.exists():
                lock_path.unlink()
        except Exception as exc:
            print(f"release token cache lock failed: {exc}")

    @classmethod
    def _acquire_cluster_map_cache_lock(cls, timeout_seconds: float = 10.0, poll_interval: float = 0.2) -> bool:
        lock_path = cls._cluster_map_cache_lock_path()
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            try:
                fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return True
            except FileExistsError:
                time.sleep(poll_interval)
            except Exception as exc:
                print(f"acquire cluster map cache lock failed: {exc}")
                return False
        return False

    @classmethod
    def _release_cluster_map_cache_lock(cls) -> None:
        lock_path = cls._cluster_map_cache_lock_path()
        try:
            if lock_path.exists():
                lock_path.unlink()
        except Exception as exc:
            print(f"release cluster map cache lock failed: {exc}")

    @classmethod
    def _is_token_cache_valid(cls, cache_payload: Dict[str, Any], user: str) -> bool:
        cached_user = cache_payload.get("user")
        cached_timestamp = cache_payload.get("cached_at")
        cached_tokens = cache_payload.get("tokens")

        if cached_user != user or not isinstance(cached_tokens, dict):
            return False
        if not isinstance(cached_timestamp, (int, float)):
            return False

        return (time.time() - cached_timestamp) < cls.TOKEN_CACHE_TTL_SECONDS

    @classmethod
    def _is_cluster_map_cache_valid(cls, cache_payload: Dict[str, Any], user: str) -> bool:
        cached_user = cache_payload.get("user")
        cached_timestamp = cache_payload.get("cached_at")
        cached_cluster_map = cache_payload.get("cluster_map")

        if cached_user != user or not isinstance(cached_cluster_map, dict):
            return False
        if not isinstance(cached_timestamp, (int, float)):
            return False

        return (time.time() - cached_timestamp) < cls.CLUSTER_MAP_CACHE_TTL_SECONDS

    @staticmethod
    def _translate_job_status(status: Optional[str]) -> Optional[str]:
        if not status:
            return status
        try:
            return JobStatus[status].label
        except KeyError:
            return status

    @staticmethod
    def _escape_json(value: Optional[str]) -> str:
        if value is None:
            return ""
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _generate_signature(self, timestamp: str) -> str:
        payload = (
            f'{{"accessKey":"{self._escape_json(self.access_key)}",'
            f'"timestamp":"{self._escape_json(timestamp)}",'
            f'"user":"{self._escape_json(self.user)}"}}'
        )
        return hmac.new(
            key=self.secret_key.encode("utf-8"),
            msg=payload.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest().lower()

    def _get_tokens(self) -> Optional[Dict[str, Any]]:
        cached_payload = self._read_token_cache()
        if cached_payload and self._is_token_cache_valid(cached_payload, self.user):
            return self._filter_unavailable_clusters(cached_payload.get("tokens"))

        lock_acquired = self._acquire_token_cache_lock()
        if not lock_acquired:
            cached_payload = self._read_token_cache()
            if cached_payload and self._is_token_cache_valid(cached_payload, self.user):
                return cached_payload.get("tokens")

        timestamp = str(int(time.time()))
        headers = {
            "user": self.user,
            "accessKey": self.access_key,
            "signature": self._generate_signature(timestamp),
            "timestamp": timestamp,
        }

        try:
            response = requests.post(
                SCNET_TOKEN_URL,
                headers=headers,
                timeout=30,
            )
            response_data = response.json()
            if response.status_code == 200 and isinstance(response_data, dict):
                response_data = self._filter_unavailable_clusters(response_data)
                self._write_token_cache(
                    {
                        "user": self.user,
                        "cached_at": time.time(),
                        "tokens": response_data,
                    }
                )
            return self._filter_unavailable_clusters(response_data)
        except Exception as exc:
            print(f"get_tokens failed: {exc}")
            cached_payload = self._read_token_cache()
            if cached_payload and self._is_token_cache_valid(cached_payload, self.user):
                return self._filter_unavailable_clusters(cached_payload.get("tokens"))
            return None
        finally:
            if lock_acquired:
                self._release_token_cache_lock()

    @staticmethod
    def _filter_unavailable_clusters(token_result: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(token_result, dict):
            return token_result

        token_data = token_result.get("data")
        if not isinstance(token_data, list):
            return token_result

        filtered_result = dict(token_result)
        filtered_result["data"] = [
            item for item in token_data
            if str(item.get("clusterId", "")).strip() != "20090"
        ]
        return filtered_result

    @staticmethod
    def _get_center_info(token: str) -> Optional[Dict[str, Any]]:
        headers = {"token": token, "Content-Type": "application/json"}
        urls = [
            SCNET_CENTER_URL
        ]
        for url in urls:
            try:
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    return response.json()
            except Exception:
                continue
        return None

    @staticmethod
    def _extract_hpc_urls(center_info: Dict[str, Any]) -> List[str]:
        if center_info.get("code") != "0":
            return []

        hpc_urls: List[str] = []
        for item in center_info.get("data", {}).get("hpcUrls", []):
            url = item.get("url")
            if item.get("enable") == "true" and url:
                hpc_urls.append(url)
        return hpc_urls

    @staticmethod
    def _extract_efile_urls(center_info: Dict[str, Any]) -> List[str]:
        if center_info.get("code") != "0":
            return []

        efile_urls: List[str] = []
        for item in center_info.get("data", {}).get("efileUrls", []):
            url = item.get("url")
            if item.get("enable") == "true" and url:
                efile_urls.append(url)
        return efile_urls

    @staticmethod
    def _get_cluster_info(hpc_url: str, token: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(
                f"{hpc_url}/hpc/openapi/v2/cluster",
                headers={"token": token, "Content-Type": "application/json"},
                timeout=30,
            )
            return response.json()
        except Exception as exc:
            print(f"get_cluster_info failed: {exc}, hpc_url: {hpc_url}")
            return None

    @staticmethod
    def _query_user_queues(hpc_url: str, token: str, user: str, scheduler_id: str) -> Optional[Dict[str, Any]]:
        retry_delays = (5, 10)
        for attempt in range(len(retry_delays) + 1):
            try:
                response = requests.get(
                    f"{hpc_url}/hpc/openapi/v2/queuenames/users/{user}",
                    headers={"token": token, "Content-Type": "application/json"},
                    params={"strJobManagerID": scheduler_id},
                    timeout=30,
                )
                result = response.json()
            except Exception as exc:
                print(f"query_user_queues failed: {exc}")
                return None

            if not isinstance(result, dict) or result.get("code") != "0" or result.get("data") != []:
                return result
            if attempt < len(retry_delays):
                time.sleep(retry_delays[attempt])

        return result

    @staticmethod
    def _query_realtime_job_detail(hpc_url: str, token: str, job_id: str, scheduler_id: str) -> Optional[Dict[str, Any]]:
        try:
            response = requests.get(
                f"{hpc_url}/hpc/openapi/v2/jobs",
                headers={"token": token, "Content-Type": "application/json"},
                params={"strClusterIDList": scheduler_id, "strJobId": job_id},
                timeout=30,
            )
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as exc:
            print(f"query_realtime_job_detail failed: {exc}")
            return None

    @staticmethod
    def _query_history_job_detail(hpc_url: str, token: str, job_id: str, scheduler_id: str) -> Optional[Dict[str, Any]]:
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        try:
            response = requests.get(
                f"{hpc_url}/hpc/openapi/v2/historyjobs",
                headers={"token": token, "Content-Type": "application/json"},
                params={
                    "strClusterNameList": scheduler_id,
                    "jobId": job_id,
                    "timeType": "CUSTOM",
                    "isQueryByQueueTime": "false",
                    "start": 0,
                    "limit": 10,
                    "startTime": start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "endTime": end_time.strftime("%Y-%m-%d %H:%M:%S"),
                },
                timeout=30,
            )
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as exc:
            print(f"query_history_job_detail failed: {exc}")
            return None

    @staticmethod
    def _cancel_job(hpc_url: str, token: str, scheduler_id: str, user: str, job_id: str) -> Optional[Dict[str, Any]]:
        payload = {
            "jobMethod": "5",
            "strJobInfoMap": f"{scheduler_id},{user}:{job_id}:",
        }
        try:
            response = requests.delete(
                f"{hpc_url}/hpc/openapi/v2/jobs",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "token": token,
                },
                data=payload,
                timeout=30,
            )
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as exc:
            print(f"cancel_job failed: {exc}")
            return None

    @staticmethod
    def _query_file_content(hpc_url: str, token: str, workdir: str, filename: str) -> Optional[Dict[str, Any]]:
        payload = {
            "dirPath": f"{workdir.rstrip('/')}/{filename}",
            "triggerNum": "1",
            "rollDirection": "DOWN",
        }
        try:
            response = requests.post(
                f"{hpc_url}/hpc/openapi/v2/file/content",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "token": token,
                },
                data=payload,
                timeout=30,
            )
            return {"status_code": response.status_code, "data": response.json()}
        except Exception as exc:
            print(f"query_file_content failed: {exc}")
            return None

    @staticmethod
    def _upload_file_to_efile(
        efile_url: str,
        token: str,
        remote_path: str,
        local_file_path: Path,
        cover: str,
    ) -> Optional[Dict[str, Any]]:
        try:
            with local_file_path.open("rb") as fh:
                upload_url = f"{efile_url.rstrip('/')}/openapi/v2/file/upload"
                response = requests.request(
                    "POST",
                    upload_url,
                    headers={"token": token},
                    data={
                        "path": remote_path,
                        "cover": cover,
                    },
                    files=[
                        ("file", (local_file_path.name, fh, "application/octet-stream")),
                    ],
                    timeout=300,
                )

            try:
                response_data = response.json()
            except ValueError:
                response_data = {"raw_text": response.text}

            return {
                "status_code": response.status_code,
                "data": response_data,
                "request": {
                    "url": upload_url,
                    "path": remote_path,
                    "filename": local_file_path.name,
                    "cover": cover,
                },
            }
        except Exception as exc:
            print(f"upload_file_to_efile failed: {exc}, efile_url: {efile_url}")
            return None

    @staticmethod
    def _download_file_from_efile(
        efile_url: str,
        token: str,
        remote_path: str,
        local_file_path: Path,
        byte_range: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        download_url = f"{efile_url.rstrip('/')}/openapi/v2/file/download"
        headers = {
            "Content-Type": "application/json",
            "token": token,
        }
        if byte_range:
            headers["Range"] = byte_range

        try:
            with requests.get(
                download_url,
                headers=headers,
                params={"path": remote_path},
                stream=True,
                timeout=300,
            ) as response:
                content_type = response.headers.get("Content-Type", "")
                if "application/json" in content_type.lower():
                    response_content = response.content
                    try:
                        response_data = response.json()
                    except ValueError:
                        response_data = None
                    if isinstance(response_data, dict) and (
                        "code" in response_data or "msg" in response_data
                    ):
                        return {
                            "status_code": response.status_code,
                            "data": response_data,
                            "request": {
                                "url": download_url,
                                "path": remote_path,
                                "local_file": str(local_file_path),
                                "range": byte_range,
                            },
                        }

                    if response.status_code in {200, 206}:
                        local_file_path.parent.mkdir(parents=True, exist_ok=True)
                        with local_file_path.open("wb") as fh:
                            fh.write(response_content)
                        return {
                            "status_code": response.status_code,
                            "data": {
                                "path": remote_path,
                                "local_file": str(local_file_path),
                                "bytes": len(response_content),
                                "content_type": content_type,
                            },
                            "request": {
                                "url": download_url,
                                "path": remote_path,
                                "local_file": str(local_file_path),
                                "range": byte_range,
                            },
                        }

                    return {
                        "status_code": response.status_code,
                        "data": {"raw_text": response_content.decode("utf-8", errors="replace")},
                        "request": {
                            "url": download_url,
                            "path": remote_path,
                            "local_file": str(local_file_path),
                            "range": byte_range,
                        },
                    }

                if response.status_code not in {200, 206}:
                    try:
                        response_data = response.json()
                    except ValueError:
                        response_data = {"raw_text": response.text}
                    return {
                        "status_code": response.status_code,
                        "data": response_data,
                        "request": {
                            "url": download_url,
                            "path": remote_path,
                            "local_file": str(local_file_path),
                            "range": byte_range,
                        },
                    }

                local_file_path.parent.mkdir(parents=True, exist_ok=True)
                bytes_written = 0
                with local_file_path.open("wb") as fh:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            fh.write(chunk)
                            bytes_written += len(chunk)

                return {
                    "status_code": response.status_code,
                    "data": {
                        "path": remote_path,
                        "local_file": str(local_file_path),
                        "bytes": bytes_written,
                        "content_type": content_type,
                    },
                    "request": {
                        "url": download_url,
                        "path": remote_path,
                        "local_file": str(local_file_path),
                        "range": byte_range,
                    },
                }
        except Exception as exc:
            print(f"download_file_from_efile failed: {exc}, efile_url: {efile_url}")
            return None

    @staticmethod
    def _extract_file_content(response_data: Dict[str, Any]) -> str:
        data = response_data.get("data")
        if isinstance(data, str):
            return data
        if isinstance(data, dict):
            for key in ("content", "fileContent", "text", "data"):
                value = data.get(key)
                if isinstance(value, str):
                    return value
        for key in ("content", "fileContent", "text"):
            value = response_data.get(key)
            if isinstance(value, str):
                return value
        return ""

    @staticmethod
    def _parse_slurm_script(script_content: str, workdir: str) -> Dict[str, str]:
        job_info = {
            "GAP_CMD_FILE": "",
            "GAP_NNODE": "",
            "GAP_NODE_STRING": "",
            "GAP_SUBMIT_TYPE": "cmd",
            "GAP_JOB_NAME": "",
            "GAP_WORK_DIR": workdir,
            "GAP_QUEUE": "",
            "GAP_NPROC": "",
            "GAP_PPN": "",
            "GAP_NGPU": "",
            "GAP_NDCU": "",
            "GAP_JOB_MEM": "",
            "GAP_WALL_TIME": "24:00:00",
            "GAP_EXCLUSIVE": "",
            "GAP_APPNAME": "BASE",
            "GAP_MULTI_SUB": "",
            "GAP_STD_OUT_FILE": f"{workdir}/slurm.out",
            "GAP_STD_ERR_FILE": f"{workdir}/slurm.err",
        }

        command_lines: List[str] = []
        for raw_line in script_content.splitlines():
            stripped_line = raw_line.strip()
            if stripped_line.startswith("#SBATCH"):
                directive = stripped_line[len("#SBATCH"):].strip()
                try:
                    tokens = shlex.split(directive, comments=True)
                except ValueError:
                    tokens = directive.split()

                if not tokens:
                    continue

                option = tokens[0]
                value = ""
                if "=" in option:
                    option, value = option.split("=", 1)
                elif len(tokens) > 1:
                    value = tokens[1]

                if option in ("-J", "--job-name"):
                    job_info["GAP_JOB_NAME"] = value
                elif option in ("-p", "--partition"):
                    job_info["GAP_QUEUE"] = value
                elif option in ("-N", "--nodes"):
                    job_info["GAP_NNODE"] = value
                elif option in ("-w", "--nodelist"):
                    job_info["GAP_NODE_STRING"] = value
                    job_info["GAP_NNODE"] = ""
                elif option in ("-n", "--ntasks"):
                    job_info["GAP_NPROC"] = value
                elif option == "--ntasks-per-node":
                    job_info["GAP_PPN"] = value
                elif option in ("-o", "--output"):
                    job_info["GAP_STD_OUT_FILE"] = value
                elif option in ("-e", "--error"):
                    job_info["GAP_STD_ERR_FILE"] = value
                elif option in ("-t", "--time"):
                    job_info["GAP_WALL_TIME"] = value
                elif option == "--exclusive":
                    job_info["GAP_EXCLUSIVE"] = "1"
                elif option in ("--mem", "--mem-per-node"):
                    job_info["GAP_JOB_MEM"] = value
                elif option.startswith("--gpus-per-node"):
                    job_info["GAP_NGPU"] = value
                elif option == "--gres" and value.startswith("gpu:"):
                    job_info["GAP_NGPU"] = value.split("gpu:", 1)[1]
                elif option == "--gres" and value.startswith("dcu:"):
                    job_info["GAP_NDCU"] = value.split("dcu:", 1)[1]
                continue

            command_lines.append(raw_line)

        job_info["GAP_CMD_FILE"] = "\n".join(command_lines).strip()
        return job_info

    @staticmethod
    def _normalize_job_detail(job: Dict[str, Any], status_field: str, duration_field: str) -> Dict[str, Any]:
        return {
            "jobStatus": job.get(status_field),
            "jobName": job.get("jobName"),
            "jobId": job.get("jobId"),
            "queue": job.get("queue"),
            "duration": job.get(duration_field),
        }

    @staticmethod
    def _normalize_job_detail_response(
        response_payload: Optional[Dict[str, Any]], query_label: str
    ) -> Dict[str, Any]:
        if not response_payload:
            return {
                "status_code": None,
                "payload": {},
                "list": [],
                "message": f"{query_label}请求无响应",
            }

        raw_payload = response_payload.get("data")
        if not isinstance(raw_payload, dict):
            return {
                "status_code": response_payload.get("status_code"),
                "payload": {},
                "list": [],
                "message": f"{query_label}返回格式异常: {raw_payload}",
                "raw_data": raw_payload,
            }

        payload_data = raw_payload.get("data")
        if isinstance(payload_data, dict):
            payload_list = payload_data.get("list", [])
            if not isinstance(payload_list, list):
                payload_list = []
        else:
            payload_list = []

        return {
            "status_code": response_payload.get("status_code"),
            "payload": raw_payload,
            "list": payload_list,
            "message": raw_payload.get("msg", "unknown error"),
        }

    def _build_cluster_map(self, force_refresh: bool = False, cluster_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        self._cluster_map_error = None
        if self.cluster_map.get(cluster_id) and not force_refresh:
            return self.cluster_map

        cached_payload = self._read_cluster_map_cache()
        cached_cluster_map: Dict[str, Dict[str, Any]] = {}
        if not force_refresh and cached_payload and self._is_cluster_map_cache_valid(cached_payload, self.user):
            cached_cluster_map = cached_payload.get("cluster_map", {})
            if cluster_id is None or cached_cluster_map.get(str(cluster_id)):
                SCNetJobClient.cluster_map = cached_cluster_map
                return SCNetJobClient.cluster_map

        lock_acquired = self._acquire_cluster_map_cache_lock() if not force_refresh else False
        if not force_refresh and not lock_acquired:
            cached_payload = self._read_cluster_map_cache()
            if cached_payload and self._is_cluster_map_cache_valid(cached_payload, self.user):
                cached_cluster_map = cached_payload.get("cluster_map", {})
                if cluster_id is None or cached_cluster_map.get(str(cluster_id)):
                    SCNetJobClient.cluster_map = cached_cluster_map
                    return SCNetJobClient.cluster_map

        token_result = self._get_tokens()
        if not isinstance(token_result, dict) or token_result.get("code") != "0":
            token_message = (
                token_result.get("msg", "unknown error")
                if isinstance(token_result, dict)
                else "token request failed"
            )
            self._set_cluster_map_error(
                "get_tokens",
                "TOKEN_QUERY_FAILED",
                f"获取 SCNet token 失败: {token_message}",
            )
            if isinstance(SCNetJobClient.cluster_map, dict) and SCNetJobClient.cluster_map:
                return SCNetJobClient.cluster_map
            if cached_cluster_map:
                SCNetJobClient.cluster_map = cached_cluster_map
                return SCNetJobClient.cluster_map
            SCNetJobClient.cluster_map = {}
            return SCNetJobClient.cluster_map

        base_cluster_map: Dict[str, Dict[str, Any]] = {}
        if cluster_id is not None:
            if isinstance(SCNetJobClient.cluster_map, dict):
                base_cluster_map.update(SCNetJobClient.cluster_map)
            if isinstance(cached_cluster_map, dict):
                base_cluster_map.update(cached_cluster_map)

        cluster_map: Dict[str, Dict[str, Any]] = {}

        try:
            for item in token_result.get("data", []):
                current_cluster_id = str(item.get("clusterId", "")).strip()
                cluster_name = item.get("clusterName", "")

                if cluster_id is not None and current_cluster_id != cluster_id:
                    continue

                cluster_start_time = time.perf_counter()
                try:
                    token = item.get("token", "")

                    if not current_cluster_id or not cluster_name or not token:
                        continue
                    if cluster_name.lower() == "ac":
                        continue

                    center_info = self._get_center_info(token)
                    if not center_info or center_info.get("code") != "0":
                        center_message = (
                            center_info.get("msg", "unknown error")
                            if isinstance(center_info, dict)
                            else "center request failed"
                        )
                        self._set_cluster_map_error(
                            "get_center_info",
                            "CENTER_INFO_QUERY_FAILED",
                            f"获取集群中心信息失败: {center_message}",
                        )
                        continue

                    hpc_urls = self._extract_hpc_urls(center_info)
                    if not hpc_urls:
                        self._set_cluster_map_error(
                            "get_center_info",
                            "HPC_URLS_NOT_FOUND",
                            "集群中心信息中没有可用的 hpcUrls",
                        )
                        continue
                    efile_urls = self._extract_efile_urls(center_info)

                    scheduler_id = ""
                    for hpc_url in hpc_urls:
                        cluster_info = self._get_cluster_info(hpc_url, token)
                        if cluster_info and cluster_info.get("code") == "0":
                            cluster_data = cluster_info.get("data", [])
                            if cluster_data and cluster_data[0].get("id") is not None:
                                scheduler_id = str(cluster_data[0].get("id"))
                                break

                    if not scheduler_id:
                        self._set_cluster_map_error(
                            "get_cluster_info",
                            "SCHEDULER_ID_NOT_FOUND",
                            "未能从任何 hpcUrl 获取 scheduler_id",
                        )
                        continue

                    cluster_map[current_cluster_id] = {
                        "token": token,
                        "clusterName": cluster_name,
                        "hpcUrls": hpc_urls,
                        "efileUrls": efile_urls,
                        "scheduler_id": scheduler_id,
                    }
                finally:
                    elapsed = time.perf_counter() - cluster_start_time
                    print(f"_build_cluster_map cluster_id={current_cluster_id}, cluster_name={cluster_name}, elapsed={elapsed:.3f}s")

            merged_cluster_map = cluster_map if cluster_id is None else {**base_cluster_map, **cluster_map}
            SCNetJobClient.cluster_map = merged_cluster_map
            if SCNetJobClient.cluster_map:
                self._write_cluster_map_cache(
                    {
                        "user": self.user,
                        "cached_at": time.time(),
                        "cluster_map": SCNetJobClient.cluster_map,
                    }
                )
            return SCNetJobClient.cluster_map
        except Exception as exc:
            print(f"build cluster map failed: {exc}")
            self._set_cluster_map_error(
                "build_cluster_map",
                "CLUSTER_MAP_BUILD_FAILED",
                f"构建集群信息失败: {exc}",
            )
            cached_payload = self._read_cluster_map_cache()
            if cached_payload and self._is_cluster_map_cache_valid(cached_payload, self.user):
                cached_cluster_map = cached_payload.get("cluster_map", {})
                if cluster_id is None or cached_cluster_map.get(str(cluster_id)):
                    SCNetJobClient.cluster_map = cached_cluster_map
                    return SCNetJobClient.cluster_map
            SCNetJobClient.cluster_map = {}
            return SCNetJobClient.cluster_map
        finally:
            if lock_acquired:
                self._release_cluster_map_cache_lock()

    def get_clusters(self) -> Dict[str, Any]:
        """返回非 ac 集群列表，不包含 token。"""
        token_result = self._get_tokens()
        if not isinstance(token_result, dict) or token_result.get("code") != "0":
            token_message = (
                token_result.get("msg", "unknown error")
                if isinstance(token_result, dict)
                else "token request failed"
            )
            return {
                "success": False,
                "error": {
                    "stage": "get_tokens",
                    "code": "TOKEN_QUERY_FAILED",
                    "message": f"查询可用集群失败: {token_message}",
                },
            }

        token_data = token_result.get("data")
        if not isinstance(token_data, list):
            return {
                "success": False,
                "error": {
                    "stage": "get_tokens",
                    "code": "INVALID_TOKEN_RESPONSE",
                    "message": "查询可用集群失败: token 响应中的 data 不是列表",
                },
            }

        clusters: List[Dict[str, Any]] = []
        for item in token_data:
            if not isinstance(item, dict):
                return {
                    "success": False,
                    "error": {
                        "stage": "get_tokens",
                        "code": "INVALID_TOKEN_RESPONSE",
                        "message": "查询可用集群失败: token 响应包含无效的集群数据",
                    },
                }
            cluster_id = str(item.get("clusterId", "")).strip()
            cluster_name = item.get("clusterName", "")
            if not cluster_id or not cluster_name or cluster_name.lower() == "ac":
                continue
            clusters.append(
                {
                    "clusterId": cluster_id,
                    "clusterName": cluster_name,
                }
            )
        return {
            "success": True,
            "clusters": clusters,
        }


    def get_available_queues(self, cluster_id: str) -> Dict[str, Any]:
        """返回指定集群的精简队列信息。"""
        cluster_map = self._build_cluster_map(cluster_id=cluster_id)
        cluster_info = cluster_map.get(str(cluster_id))
        if not cluster_info:
            return {
                "success": False,
                "clusterId": str(cluster_id),
                "clusterName": None,
                "error": self._cluster_map_error
                or {
                    "stage": "build_cluster_map",
                    "code": "CLUSTER_NOT_FOUND",
                    "message": f"未找到 cluster_id={cluster_id} 对应的集群信息",
                },
            }

        queue_result = None
        queue_error = None
        for hpc_url in cluster_info["hpcUrls"]:
            queue_result = self._query_user_queues(
                hpc_url=hpc_url,
                token=cluster_info["token"],
                user=self.user,
                scheduler_id=cluster_info["scheduler_id"],
            )
            if isinstance(queue_result, dict) and queue_result.get("code") == "0":
                break
            if isinstance(queue_result, dict):
                queue_error = {
                    "stage": "query_queues",
                    "code": "QUEUE_QUERY_REJECTED",
                    "message": f"查询队列失败: {queue_result.get('msg', 'unknown error')}",
                }
            elif queue_result is None:
                queue_error = {
                    "stage": "query_queues",
                    "code": "QUEUE_QUERY_FAILED",
                    "message": "查询队列接口请求失败",
                }
            else:
                queue_error = {
                    "stage": "query_queues",
                    "code": "INVALID_QUEUE_RESPONSE",
                    "message": "查询队列失败: 接口响应不是对象",
                }

        if not isinstance(queue_result, dict) or queue_result.get("code") != "0":
            return {
                "success": False,
                "clusterId": str(cluster_id),
                "clusterName": cluster_info["clusterName"],
                "error": queue_error
                or {
                    "stage": "query_queues",
                    "code": "QUEUE_QUERY_FAILED",
                    "message": "查询队列失败",
                },
            }

        queue_data = queue_result.get("data")
        if not isinstance(queue_data, list):
            return {
                "success": False,
                "clusterId": str(cluster_id),
                "clusterName": cluster_info["clusterName"],
                "error": {
                    "stage": "query_queues",
                    "code": "INVALID_QUEUE_RESPONSE",
                    "message": "查询队列失败: 响应中的 data 不是列表",
                },
            }

        queues = []
        for item in queue_data:
            if not isinstance(item, dict):
                return {
                    "success": False,
                    "clusterId": str(cluster_id),
                    "clusterName": cluster_info["clusterName"],
                    "error": {
                        "stage": "query_queues",
                        "code": "INVALID_QUEUE_RESPONSE",
                        "message": "查询队列失败: 响应包含无效的队列数据",
                    },
                }
            queue_name = str(item.get("queueName") or "").strip()
            if "hd" in queue_name.lower():
                continue

            queues.append(
                {
                    "queueName": item.get("queueName"),
                    "queNodes": item.get("queNodes"),
                    "queFreeNodes": item.get("queFreeNodes"),
                    "queFreeNcpus": item.get("queFreeNcpus"),
                }
            )

        return {
            "success": True,
            "clusterId": str(cluster_id),
            "clusterName": cluster_info["clusterName"],
            "queues": queues,
        }

    def _get_job_detail(self, hpc_urls: List[str], scheduler_id: str, token: str, job_id: str) -> Dict[str, Any]:
        realtime_failure: Optional[Dict[str, Any]] = None
        history_failure: Optional[Dict[str, Any]] = None

        for hpc_url in hpc_urls:
            realtime_result = self._query_realtime_job_detail(
                hpc_url=hpc_url,
                token=token,
                job_id=str(job_id),
                scheduler_id=scheduler_id,
            )
            if realtime_result:
                realtime_response = self._normalize_job_detail_response(realtime_result, "实时作业查询")
                realtime_data = realtime_response.get("payload", {})
                realtime_list = realtime_response.get("list", [])
                if realtime_response.get("status_code") == 200 and realtime_data.get("code") == "0" and realtime_list:
                    return {
                        "success": True,
                        "message": "获取实时作业详情成功",
                        "data": self._normalize_job_detail(realtime_list[0], "jobStatus", "jobRunTime"),
                    }
                realtime_failure = {
                    "success": False,
                    "message": f"实时作业查询失败: {realtime_response.get('message', 'unknown error')}",
                    "data": realtime_data or realtime_response.get("raw_data"),
                }

            history_result = self._query_history_job_detail(
                hpc_url=hpc_url,
                token=token,
                job_id=str(job_id),
                scheduler_id=scheduler_id,
            )
            if history_result:
                history_response = self._normalize_job_detail_response(history_result, "历史作业查询")
                history_data = history_response.get("payload", {})
                history_list = history_response.get("list", [])
                if history_response.get("status_code") == 200 and history_data.get("code") == "0" and history_list:
                    return {
                        "success": True,
                        "message": "获取历史作业详情成功",
                        "data": self._normalize_job_detail(history_list[0], "jobState", "jobWalltimeUsed"),
                    }
                history_failure = {
                    "success": False,
                    "message": f"历史作业查询失败: {history_response.get('message', 'unknown error')}",
                    "data": history_data or history_response.get("raw_data"),
                }

        if history_failure:
            return history_failure
        if realtime_failure:
            return realtime_failure

        return {
            "success": False,
            "message": f"查询作业详情失败，job_id={job_id}",
        }

    def get_job_info(self, cluster_id: str, job_id: str) -> Dict[str, Any]:
        cluster_map = self._build_cluster_map(cluster_id=cluster_id)
        cluster_info = cluster_map.get(str(cluster_id))
        if not cluster_info:
            return {
                "success": False,
                "message": f"未找到 cluster_id={cluster_id} 对应的集群信息",
            }
        
        result = self._get_job_detail(
            hpc_urls=cluster_info.get("hpcUrls", []),
            scheduler_id=cluster_info.get("scheduler_id", ""),
            token=cluster_info.get("token", ""),
            job_id=job_id,
        )

        if result.get("success") and isinstance(result.get("data"), dict):
            result["data"]["jobStatus"] = self._translate_job_status(
                result["data"].get("jobStatus")
            )

        return result

    @staticmethod
    def _monitor_interval_seconds(elapsed_seconds: float) -> int:
        if elapsed_seconds < 60:
            return 10
        if elapsed_seconds < 600:
            return 60
        if elapsed_seconds < 1800:
            return 120
        return 300

    def monitor_job(self, cluster_id: str, job_id: str) -> Dict[str, Any]:
        cluster_map = self._build_cluster_map(cluster_id=cluster_id)
        cluster_info = cluster_map.get(str(cluster_id))
        if not cluster_info:
            return {
                "success": False,
                "message": f"未找到 cluster_id={cluster_id} 对应的集群信息",
            }

        abnormal_statuses = {"statDE", "statD", "statEX", "statH", "statS", "statT", "statN"}

        result = self._get_job_detail(
            hpc_urls=cluster_info.get("hpcUrls", []),
            scheduler_id=cluster_info.get("scheduler_id", ""),
            token=cluster_info.get("token", ""),
            job_id=job_id,
        )

        if not result.get("success"):
            return result

        data = result.get("data", {})
        status_code = data.get("jobStatus")
        status_label = self._translate_job_status(status_code)

        translated_result = {
            "success": result.get("success", False),
            "message": "Async job monitoring has started. Wait for the job completion feedback message.",
            "data": {
                **data,
                "jobStatus": status_label,
                "asyncMonitor": True,
                "terminal": False,
                "agentAction": "stop_response",
                "agentInstruction": "End the current response after receiving the async monitoring handoff, then wait for the job completion feedback before continuing.",
            },
        }

        if status_code == "statC":
            translated_result["message"] = "Job completed"
            translated_result["data"]["asyncMonitor"] = False
            translated_result["data"]["terminal"] = True
            return translated_result

        if status_code in abnormal_statuses:
            translated_result["success"] = False
            translated_result["message"] = f"Job ended abnormally: {status_label}"
            translated_result["data"]["asyncMonitor"] = False
            translated_result["data"]["terminal"] = True
            return translated_result

        return translated_result

    def cancel_job(self, cluster_id: str, job_id: str) -> Dict[str, Any]:
        cluster_map = self._build_cluster_map(cluster_id=cluster_id)
        cluster_info = cluster_map.get(str(cluster_id))
        if not cluster_info:
            return {
                "success": False,
                "message": f"未找到 cluster_id={cluster_id} 对应的集群信息",
            }

        hpc_urls = cluster_info.get("hpcUrls", [])
        if not hpc_urls:
            return {
                "success": False,
                "message": f"cluster_id={cluster_id} 未配置可用 hpcUrls",
            }

        scheduler_id = cluster_info.get("scheduler_id", "")
        if not scheduler_id:
            return {
                "success": False,
                "message": f"cluster_id={cluster_id} 未配置可用 scheduler_id",
            }

        token = cluster_info.get("token", "")
        if not token:
            return {
                "success": False,
                "message": f"cluster_id={cluster_id} 未配置可用 token",
            }

        cancel_failure: Optional[Dict[str, Any]] = None
        for hpc_url in hpc_urls:
            cancel_result = self._cancel_job(
                hpc_url=hpc_url,
                token=token,
                scheduler_id=scheduler_id,
                user=self.user,
                job_id=str(job_id),
            )
            if not cancel_result:
                continue

            cancel_data = cancel_result.get("data", {})
            if cancel_result.get("status_code") == 200 and cancel_data.get("code") == "0":
                return {
                    "success": True,
                    "message": cancel_data.get("msg", "success"),
                    "data": cancel_data.get("data", {}),
                }

            cancel_failure = {
                "success": False,
                "message": f"取消作业失败: {cancel_data.get('msg', 'unknown error')}",
                "data": cancel_data.get("data", {}),
            }

        if cancel_failure:
            return cancel_failure

        return {
            "success": False,
            "message": f"取消作业失败，job_id={job_id}",
        }

    def submit_job(self, cluster_id: str, workdir: str, filename: str, appname: str="BASE") -> Dict[str, Any]:
        """提交作业，除必要字段外其他字段全部置空。"""
        cluster_map = self._build_cluster_map(cluster_id=cluster_id)
        cluster_info = cluster_map.get(str(cluster_id))
        if not cluster_info:
            return {
                "success": False,
                "message": f"未找到 cluster_id={cluster_id} 对应的集群信息",
            }

        hpc_urls = cluster_info.get("hpcUrls", [])
        if not hpc_urls:
            return {
                "success": False,
                "message": f"cluster_id={cluster_id} 未配置可用 hpcUrls",
            }

        scheduler_id = cluster_info.get("scheduler_id", "")
        if not scheduler_id:
            return {
                "success": False,
                "message": f"cluster_id={cluster_id} 未配置可用 scheduler_id",
            }

        file_result = self._query_file_content(
            hpc_url=hpc_urls[0],
            token=cluster_info["token"],
            workdir=workdir,
            filename=filename,
        )
        if not file_result:
            return {
                "success": False,
                "message": f"读取脚本文件失败: {workdir.rstrip('/')}/{filename}",
            }

        file_data = file_result.get("data", {})
        if file_result.get("status_code") != 200 or file_data.get("code") != "0":
            return {
                "success": False,
                "message": f"读取脚本文件失败: {file_data.get('msg', 'unknown error')}",
                "data": file_data,
            }

        script_content = self._extract_file_content(file_data)
        if not script_content.strip():
            return {
                "success": False,
                "message": f"脚本文件内容为空: {workdir.rstrip('/')}/{filename}",
                "data": file_data,
            }

        url = f"{hpc_urls[0]}/hpc/openapi/v2/apptemplates/BASIC/{appname}/job"
        payload = {
            "strJobManagerID": scheduler_id,
            "mapAppJobInfo": self._parse_slurm_script(script_content, workdir),
        }
        headers = {
            "Content-Type": "application/json",
            "token": cluster_info["token"],
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response_data = response.json()
        except Exception as exc:
            return {"success": False, "message": f"提交作业请求失败: {exc}"}

        if response.status_code != 200:
            return {
                "success": False,
                "message": f"提交作业失败，HTTP {response.status_code}",
                "data": response_data,
            }

        if response_data.get("code") != "0":
            return {
                "success": False,
                "message": f"提交作业失败: {response_data.get('msg', 'unknown error')}",
                "data": response_data,
            }

        return {
            "success": True,
            "message": "提交作业成功",
            "data": response_data,
        }

    def upload_file(
        self,
        cluster_id: str,
        local_file_path: str,
        remote_path: str,
        cover: str = "cover",
    ) -> Dict[str, Any]:
        cluster_map = self._build_cluster_map(cluster_id=cluster_id)
        cluster_info = cluster_map.get(str(cluster_id))
        if not cluster_info:
            return {
                "success": False,
                "message": f"未找到 cluster_id={cluster_id} 对应的集群信息",
            }

        efile_urls = cluster_info.get("efileUrls", [])
        if not efile_urls:
            return {
                "success": False,
                "message": f"cluster_id={cluster_id} 未配置可用 efileUrls",
            }

        token = cluster_info.get("token", "")
        if not token:
            return {
                "success": False,
                "message": f"cluster_id={cluster_id} 未配置可用 token",
            }

        if cover not in {"cover", "uncover"}:
            return {
                "success": False,
                "message": "cover 参数仅支持 cover 或 uncover",
            }

        file_path = Path(local_file_path).expanduser()
        if not file_path.is_file():
            return {
                "success": False,
                "message": f"本地文件不存在: {local_file_path}",
            }

        upload_failure: Optional[Dict[str, Any]] = None
        for efile_url in efile_urls:
            upload_result = self._upload_file_to_efile(
                efile_url=efile_url,
                token=token,
                remote_path=remote_path,
                local_file_path=file_path,
                cover=cover,
            )
            if not upload_result:
                continue

            upload_data = upload_result.get("data", {})
            if upload_result.get("status_code") == 200 and upload_data.get("code") == "0":
                return {
                    "success": True,
                    "message": upload_data.get("msg", "success"),
                    "data": upload_data.get("data", {}),
                }

            upload_failure = {
                "success": False,
                "message": f"上传文件失败: {upload_data.get('msg', 'unknown error')}",
                "data": upload_data,
                "request": upload_result.get("request", {}),
            }

        if upload_failure:
            return upload_failure

        return {
            "success": False,
            "message": f"上传文件失败: {local_file_path} -> {remote_path}",
        }

    def download_file(
        self,
        cluster_id: str,
        remote_path: str,
        local_path: Optional[str] = None,
        byte_range: Optional[str] = None,
    ) -> Dict[str, Any]:
        cluster_map = self._build_cluster_map(cluster_id=cluster_id)
        cluster_info = cluster_map.get(str(cluster_id))
        if not cluster_info:
            return {
                "success": False,
                "message": f"未找到 cluster_id={cluster_id} 对应的集群信息",
            }

        efile_urls = cluster_info.get("efileUrls", [])
        if not efile_urls:
            return {
                "success": False,
                "message": f"cluster_id={cluster_id} 未配置可用 efileUrls",
            }

        token = cluster_info.get("token", "")
        if not token:
            return {
                "success": False,
                "message": f"cluster_id={cluster_id} 未配置可用 token",
            }

        normalized_remote_path = remote_path.strip()
        if not normalized_remote_path:
            return {
                "success": False,
                "message": "remote_path 不能为空",
            }

        default_filename = PurePosixPath(normalized_remote_path.rstrip("/")).name or "download"
        target_path = Path(local_path or default_filename).expanduser()
        if str(local_path or "").endswith(("/", "\\")) or target_path.is_dir():
            target_path = target_path / default_filename

        download_failure: Optional[Dict[str, Any]] = None
        for efile_url in efile_urls:
            download_result = self._download_file_from_efile(
                efile_url=efile_url,
                token=token,
                remote_path=normalized_remote_path,
                local_file_path=target_path,
                byte_range=byte_range,
            )
            if not download_result:
                continue

            download_data = download_result.get("data", {})
            if (
                download_result.get("status_code") in {200, 206}
                and isinstance(download_data, dict)
                and "bytes" in download_data
            ):
                return {
                    "success": True,
                    "message": "下载文件成功",
                    "data": download_data,
                }

            download_failure = {
                "success": False,
                "message": f"下载文件失败: {download_data.get('msg', 'unknown error') if isinstance(download_data, dict) else 'unknown error'}",
                "data": download_data,
                "request": download_result.get("request", {}),
            }

        if download_failure:
            return download_failure

        return {
            "success": False,
            "message": f"下载文件失败: {remote_path} -> {target_path}",
        }
