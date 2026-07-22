import json
import sys
import os

if len(sys.argv) < 5:
    print("Usage: python save_online_search.py <input_json_path> <search_result_path> <game_name> <timestamp>")
    sys.exit(1)

input_json_path = sys.argv[1]
search_result_path = sys.argv[2]
game_name = sys.argv[3]
timestamp = sys.argv[4]


safe_name = game_name.replace(" ", "_").replace(":", "")
os.makedirs("cache", exist_ok=True)

input_path = input_json_path

llm_path = search_result_path
output_path = f"cache/_online_search_{safe_name}_{timestamp}.json"

with open(input_path, "r", encoding="utf-8") as f:
    input_data = json.load(f)

with open(llm_path, "r", encoding="utf-8") as f:
    llm_results = json.load(f)

for event, llm_out in zip(input_data, llm_results):
    event.update(llm_out)  # event_name 被覆盖，其余字段追加

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(input_data, f, ensure_ascii=False, indent=2)

print(f"保存成功：{output_path}，共 {len(input_data)} 个事件")