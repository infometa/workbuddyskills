"""
upload-files.py 单元测试

覆盖范围：
- Bug 4: asyncio.gather 缺少 return_exceptions=True（部分失败时其他结果不丢失）
- Bug 5: upload_file_async 中同步阻塞读文件（改为 run_in_executor 异步读取）
"""

import asyncio
import time
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

# 将脚本目录加入 sys.path
import sys
import os
import importlib.util

# upload-files.py 文件名含连字符，无法直接 import，使用 importlib 动态加载
_script_dir = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "upload_files",
    os.path.join(_script_dir, "upload-files.py"),
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["upload_files"] = _mod
_spec.loader.exec_module(_mod)

from upload_files import LexiangUploader, UploadTask, UploadSession


# ─────────────────────────────────────────────
# 辅助工厂
# ─────────────────────────────────────────────

def make_task(name: str = "test.md") -> UploadTask:
    return UploadTask(
        local_path=f"/tmp/{name}",
        file_name=name,
        parent_entry_id="entry-001",
        mime_type="text/markdown",
        file_size=1024,
        content_hash="abc123",
    )


def make_session(name: str = "test.md", upload_url: str = "http://example.com/upload") -> UploadSession:
    return UploadSession(
        session_id=f"sess-{name}",
        upload_url=upload_url,
        task=make_task(name),
    )


# ─────────────────────────────────────────────
# Bug 4: gather return_exceptions=True
# ─────────────────────────────────────────────

class TestExecuteParallelUploads:
    """测试 execute_parallel_uploads 的异常处理行为（Bug 4）"""

    @pytest.mark.asyncio
    async def test_all_success_returns_all_results(self):
        """全部成功时，返回所有 (session, True) 结果"""
        uploader = LexiangUploader(parallel=3)
        sessions = [make_session(f"file{i}.md", f"http://ok.com/{i}") for i in range(3)]

        async def mock_upload(url, path, mime):
            return True

        with patch.object(uploader, "upload_file_async", side_effect=mock_upload):
            results = await uploader.execute_parallel_uploads(sessions)

        assert len(results) == 3
        for session, success in results:
            assert success is True

    @pytest.mark.asyncio
    async def test_partial_failure_does_not_lose_other_results(self):
        """部分失败时，其他成功结果不丢失（Bug 4 核心验证）"""
        uploader = LexiangUploader(parallel=3)
        sessions = [
            make_session("ok1.md",   "http://ok.com/1"),
            make_session("fail.md",  "http://fail.com/2"),
            make_session("ok2.md",   "http://ok.com/3"),
        ]

        async def mock_upload(url, path, mime):
            if "fail" in url:
                raise RuntimeError("模拟上传失败")
            return True

        with patch.object(uploader, "upload_file_async", side_effect=mock_upload):
            results = await uploader.execute_parallel_uploads(sessions)

        # 三个结果都应该返回，不能因为一个失败而丢失其他
        assert len(results) == 3

        ok1_result   = next(r for r in results if r[0].task.file_name == "ok1.md")
        fail_result  = next(r for r in results if r[0].task.file_name == "fail.md")
        ok2_result   = next(r for r in results if r[0].task.file_name == "ok2.md")

        assert ok1_result[1]  is True,  "ok1.md 应该成功"
        assert ok2_result[1]  is True,  "ok2.md 应该成功"
        assert fail_result[1] is False, "fail.md 应该失败"

    @pytest.mark.asyncio
    async def test_failed_session_error_is_recorded(self):
        """失败的任务，错误信息应记录到 task.error"""
        uploader = LexiangUploader(parallel=2)
        sessions = [make_session("fail.md", "http://fail.com")]

        async def mock_upload(url, path, mime):
            raise ConnectionError("网络超时")

        with patch.object(uploader, "upload_file_async", side_effect=mock_upload):
            results = await uploader.execute_parallel_uploads(sessions)

        session, success = results[0]
        assert success is False
        assert "网络超时" in session.task.error

    @pytest.mark.asyncio
    async def test_all_fail_returns_all_false(self):
        """全部失败时，返回所有 (session, False) 结果，不抛异常"""
        uploader = LexiangUploader(parallel=2)
        sessions = [make_session(f"fail{i}.md") for i in range(3)]

        async def mock_upload(url, path, mime):
            raise RuntimeError("全部失败")

        with patch.object(uploader, "upload_file_async", side_effect=mock_upload):
            # 修复前：这里会直接抛出 RuntimeError
            results = await uploader.execute_parallel_uploads(sessions)

        assert len(results) == 3
        for _, success in results:
            assert success is False


# ─────────────────────────────────────────────
# Bug 5: 异步读文件不阻塞事件循环
# ─────────────────────────────────────────────

class TestUploadFileAsync:
    """测试 upload_file_async 不阻塞事件循环（Bug 5）"""

    @pytest.mark.asyncio
    async def test_parallel_uploads_are_concurrent(self, tmp_path):
        """并行上传时，两个任务应真正并发执行，总耗时接近单个任务耗时"""
        f1 = tmp_path / "a.md"
        f2 = tmp_path / "b.md"
        f1.write_bytes(b"x" * 1024)
        f2.write_bytes(b"x" * 1024)

        DELAY = 0.15  # 模拟每个上传耗时 150ms

        uploader = LexiangUploader(parallel=2)

        # mock_resp 是 async with session.put(...) as response 里的 response
        mock_resp = MagicMock()
        mock_resp.status = 200

        # mock_put_ctx 是 session.put(...) 返回的异步上下文管理器
        mock_put_ctx = MagicMock()
        mock_put_ctx.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_put_ctx.__aexit__ = AsyncMock(return_value=False)

        # session.put 是普通方法（非 coroutine），返回异步上下文管理器
        # 同时在 __aenter__ 里注入延迟，模拟网络耗时
        async def slow_aenter(*args, **kwargs):
            await asyncio.sleep(DELAY)
            return mock_resp
        mock_put_ctx.__aenter__ = slow_aenter

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.put = MagicMock(return_value=mock_put_ctx)

        start = time.monotonic()
        with patch("aiohttp.ClientSession", return_value=mock_session):
            await asyncio.gather(
                uploader.upload_file_async("http://x.com/1", str(f1), "text/markdown"),
                uploader.upload_file_async("http://x.com/2", str(f2), "text/markdown"),
            )
        elapsed = time.monotonic() - start

        # 真正并发：耗时应接近 DELAY 而非 2*DELAY
        assert elapsed < DELAY * 1.8, (
            f"上传疑似被串行化，耗时 {elapsed:.2f}s，预期 < {DELAY * 1.8:.2f}s"
        )

    @pytest.mark.asyncio
    async def test_file_read_uses_executor(self, tmp_path):
        """文件读取应通过 run_in_executor 执行，不直接调用同步 open()"""
        test_file = tmp_path / "test.md"
        test_file.write_bytes(b"hello world")

        uploader = LexiangUploader()
        executor_called = []

        original_run_in_executor = asyncio.get_event_loop().run_in_executor

        async def patched_run_in_executor(executor, func, *args):
            executor_called.append(func)
            return await original_run_in_executor(executor, func, *args)

        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_session.put = MagicMock(return_value=mock_resp)

        loop = asyncio.get_event_loop()
        with patch.object(loop, "run_in_executor", side_effect=patched_run_in_executor):
            with patch("aiohttp.ClientSession", return_value=mock_session):
                await uploader.upload_file_async(
                    "http://x.com/upload", str(test_file), "text/markdown"
                )

        # 应该至少有一次 run_in_executor 调用（用于读文件）
        assert len(executor_called) >= 1, "文件读取应通过 run_in_executor 异步执行"

    @pytest.mark.asyncio
    async def test_fallback_sync_uses_executor(self, tmp_path):
        """无 aiohttp 时，降级路径也应通过 run_in_executor 执行，不直接阻塞"""
        test_file = tmp_path / "test.md"
        test_file.write_bytes(b"hello")

        uploader = LexiangUploader()
        executor_called = []

        original_run_in_executor = asyncio.get_event_loop().run_in_executor

        async def patched_run_in_executor(executor, func, *args):
            executor_called.append(True)
            return await original_run_in_executor(executor, func, *args)

        def mock_upload_sync(url, path, mime):
            return True

        loop = asyncio.get_event_loop()
        with patch("upload_files.HAS_AIOHTTP", False):
            with patch.object(uploader, "upload_file_sync", side_effect=mock_upload_sync):
                with patch.object(loop, "run_in_executor", side_effect=patched_run_in_executor):
                    await uploader.upload_file_async(
                        "http://x.com/upload", str(test_file), "text/markdown"
                    )

        assert len(executor_called) >= 1, "降级路径也应通过 run_in_executor 执行"


# ─────────────────────────────────────────────
# 其他基础功能测试
# ─────────────────────────────────────────────

class TestGenerateUploadPlan:
    """测试上传计划生成"""

    def test_plan_contains_all_steps(self):
        """每个文件应生成 3 个步骤：申请、上传、确认"""
        uploader = LexiangUploader()
        tasks = [make_task("a.md"), make_task("b.md")]
        plan = uploader.generate_upload_plan(tasks)

        assert plan["total_files"] == 2
        assert len(plan["steps"]) == 6  # 每个文件 3 步

    def test_plan_total_size(self):
        """计划中的总大小应等于所有文件大小之和"""
        uploader = LexiangUploader()
        tasks = [make_task("a.md"), make_task("b.md")]
        plan = uploader.generate_upload_plan(tasks)

        assert plan["total_size"] == 2048  # 每个 task file_size=1024


class TestScanFolder:
    """测试文件夹扫描"""

    def test_scan_filters_by_extension(self, tmp_path):
        """扫描时应按扩展名过滤"""
        (tmp_path / "doc.md").write_text("# hello")
        (tmp_path / "image.png").write_bytes(b"\x89PNG")
        (tmp_path / "note.txt").write_text("note")

        uploader = LexiangUploader()
        tasks = uploader.scan_folder(str(tmp_path), "entry-001", extensions=[".md"])

        assert len(tasks) == 1
        assert tasks[0].file_name == "doc.md"

    def test_scan_ignores_patterns(self, tmp_path):
        """扫描时应忽略指定模式的路径"""
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "pkg.md").write_text("pkg")
        (tmp_path / "readme.md").write_text("readme")

        uploader = LexiangUploader()
        tasks = uploader.scan_folder(str(tmp_path), "entry-001", extensions=[".md"])

        assert len(tasks) == 1
        assert tasks[0].file_name == "readme.md"
