#!/usr/bin/env python3
"""
伏笔追踪器 (Plot Tracker)
功能：自动记录、检查伏笔，避免前后矛盾。
"""
import json
from pathlib import Path
from datetime import datetime

WORK_DIR = Path("/app/working/customized_skills/novel_writer")
PLOT_FILE = WORK_DIR / "examples" / "plot_threads.json"

class PlotTracker:
    def __init__(self):
        self.plot_file = PLOT_FILE
        self.threads = self._load_threads()

    def _load_threads(self) -> list:
        if self.plot_file.exists():
            with open(self.plot_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_threads(self):
        with open(self.plot_file, 'w', encoding='utf-8') as f:
            json.dump(self.threads, f, ensure_ascii=False, indent=2)

    def add_thread(self, chapter: int, title: str, description: str, status: str = "open"):
        """添加伏笔线索"""
        thread = {
            "id": len(self.threads) + 1,
            "chapter_opened": chapter,
            "title": title,
            "description": description,
            "status": status,  # open, developing, closed, abandoned
            "chapter_closed": None,
            "created_at": datetime.now().isoformat()
        }
        self.threads.append(thread)
        self._save_threads()
        print(f"✅ 伏笔已添加：{title} (第{chapter}章)")

    def close_thread(self, thread_id: int, chapter: int, resolution: str):
        """关闭伏笔线索"""
        for thread in self.threads:
            if thread["id"] == thread_id:
                thread["status"] = "closed"
                thread["chapter_closed"] = chapter
                thread["resolution"] = resolution
                self._save_threads()
                print(f"✅ 伏笔已关闭：{thread['title']} (第{chapter}章)")
                return
        print(f"❌ 未找到伏笔ID: {thread_id}")

    def list_threads(self, status: str = None):
        """列出所有伏笔"""
        print("\n📋 伏笔追踪表")
        print("-" * 60)
        for thread in self.threads:
            if status and thread["status"] != status:
                continue
            icon = "🔴" if thread["status"] == "open" else "🟡" if thread["status"] == "developing" else "🟢" if thread["status"] == "closed" else "⚪"
            print(f"{icon} ID:{thread['id']} | 第{thread['chapter_opened']}章开启 | {thread['title']}")
            print(f"   描述：{thread['description']}")
            if thread["status"] == "closed":
                print(f"   结局：{thread.get('resolution', 'N/A')} (第{thread['chapter_closed']}章)")
            print("-" * 60)

    def check_unresolved(self, current_chapter: int):
        """检查未关闭的伏笔"""
        unresolved = [t for t in self.threads if t["status"] in ["open", "developing"]]
        if unresolved:
            print(f"\n⚠️ 警告：当前第{current_chapter}章，仍有 {len(unresolved)} 个未关闭伏笔！")
            for t in unresolved:
                print(f"   - {t['title']} (第{t['chapter_opened']}章开启)")
        else:
            print(f"\n✅ 当前第{current_chapter}章，所有伏笔已处理完毕！")

# 演示
if __name__ == "__main__":
    tracker = PlotTracker()
    tracker.add_thread(1, "神秘钥匙", "主角在第一章捡到一把旧钥匙，不知用途。")
    tracker.add_thread(3, "失踪的妹妹", "主角的妹妹在第三章失踪，线索中断。")
    tracker.list_threads()
    tracker.close_thread(1, 10, "钥匙打开了宝藏，发现妹妹留下的线索。")
    tracker.list_threads()
    tracker.check_unresolved(10)
