import sys
import pandas as pd

if len(sys.argv) < 3:
    print("Usage: python preprocess_and_preview.py <official_posts_csv_path> <game_name>")
    sys.exit(1)

OFFICIAL_POSTS_CSV_PATH = sys.argv[1]
GAME_NAME = sys.argv[2]

official_posts_df = pd.read_csv(OFFICIAL_POSTS_CSV_PATH, encoding="utf-8")

# # 先按engagement进行倒排
# official_posts_df["engagement"] = (official_posts_df["tweets_like"].clip(lower=0).fillna(0) + official_posts_df["tweets_reply"].clip(lower=0).fillna(0) + official_posts_df["tweets_retweet"].clip(lower=0).fillna(0))
# sorted_official_posts_df = official_posts_df.sort_values(by=['engagement'], ascending=False).reset_index(drop=True)
            

# 先过滤出官方帖子的部分
game_top_content = official_posts_df['content'].tolist()[:50]
game_top_content = [ele.replace("\n", " ") for ele in game_top_content]

input_post_str = "\n".join(f"{idx+1}. {ele}" for idx, ele in enumerate(game_top_content))

print(f"GAME_NAME={GAME_NAME}")
print(f"POST_COUNT={len(game_top_content)}")
print("===POSTS_START===")
print(input_post_str)
print("===POSTS_END===")
