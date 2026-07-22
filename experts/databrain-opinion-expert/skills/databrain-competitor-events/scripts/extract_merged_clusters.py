import sys
import os
import pandas as pd
import json
import re

if len(sys.argv) < 6:
    print("Usage: python extract_merged_clusters.py <official_posts_csv_path> <post_comments_csv_path> <game_name> <raw_txt_path> <timestamp>")
    sys.exit(1)

OFFICIAL_POSTS_CSV_PATH = sys.argv[1]
POST_COMMENTS_CSV_PATH = sys.argv[2]
GAME_NAME = sys.argv[3]
RAW_TXT_PATH = sys.argv[4]
TIMESTAMP = sys.argv[5]

with open(RAW_TXT_PATH, "r", encoding="utf-8") as f:
    llm_output = f.read()

# 提取 Final Result JSON
final_mark = '### Final Result:'
final_res_part = llm_output.split(final_mark, 1)[1].strip()
final_res_part = re.sub(r'```(?:json)?\s*', '', final_res_part)
final_res_part = re.sub(r'```\s*$', '', final_res_part).strip()
res = json.loads(final_res_part)

# 读取官号主贴数据
official_posts_df = pd.read_csv(OFFICIAL_POSTS_CSV_PATH, encoding="utf-8")
# engagement在step 0 已经计算过了
# official_posts_df['engagement'] = (
#     official_posts_df.get('tweets_like', pd.Series(0, index=official_posts_df.index)).fillna(0) +
#     official_posts_df.get('tweets_reply', pd.Series(0, index=official_posts_df.index)).fillna(0) +
#     official_posts_df.get('tweets_retweet', pd.Series(0, index=official_posts_df.index)).fillna(0)
# ).astype(int)

# 读取官帖评论数据
all_comment_data_df = pd.read_csv(POST_COMMENTS_CSV_PATH, encoding="utf-8")
all_comment_data_df['comment_time'] = pd.to_datetime(all_comment_data_df['comment_time'], errors='coerce')


def _top_comments(df: pd.DataFrame, sentiment: int, n: int = 200) -> list[str]:
    """按 sentiment_rating 过滤，按 tweets_like 降序排序，取前 n 条 content。"""
    sub = df[df['sentiment_rating'] == sentiment].copy()
    sub = sub.sort_values('tweets_like', ascending=False, na_position='last')
    return sub['content'].dropna().head(n).tolist()


# 构建 cluster_summary_list
cluster_summary_list = []
for cluster in res:
    event_name = cluster['event_name']
    member_indices_1based = cluster['member_index_list']
    if isinstance(member_indices_1based, str):
        member_indices_1based = json.loads(member_indices_1based)
    member_indices_0based = [i - 1 for i in member_indices_1based]

    cluster_df = official_posts_df.iloc[member_indices_0based].copy()
    max_content_idx = cluster_df['content'].str.len().idxmax()
    highlight_row = cluster_df.loc[max_content_idx]
    total_engagement = cluster_df['engagement'].sum()

    all_comment_ids = []
    for val in cluster_df['comment_id']:
        if isinstance(val, list):
            all_comment_ids.extend(val)
        else:
            all_comment_ids.append(val)

    # 从全量数据中取该 cluster 主贴下的评论
    cluster_comment_id_list = cluster_df['comment_id'].tolist()
    cluster_post_comments_df = all_comment_data_df[
        all_comment_data_df['comment_parent_id'].isin(cluster_comment_id_list)
    ]

    cluster_summary_list.append({
        'event_name': event_name,
        'highlight_content': highlight_row['content'],
        'total_engagement': int(total_engagement),

        'tweets_view_lists': cluster_df['tweets_view'].tolist(),
        'tweets_like_lists': cluster_df['tweets_like'].tolist(),
        'tweets_reply_lists': cluster_df['tweets_reply'].tolist(),
        'tweets_retweet_lists': cluster_df['tweets_retweet'].tolist(),
        'engagement_lists': cluster_df['engagement'].tolist(),

        'content_url_lists': cluster_df['content_url'].tolist(),
        'all_comment_ids': all_comment_ids,
        'positive_sentiment_comment_no': int((cluster_post_comments_df['sentiment_rating'] == 5).sum()),
        'negative_sentiment_comment_no': int((cluster_post_comments_df['sentiment_rating'] == 1).sum()),
        'neutral_sentiment_comment_no':  int((cluster_post_comments_df['sentiment_rating'] == 3).sum()),
        'positive_sentiment_comments': _top_comments(cluster_post_comments_df, sentiment=5),
        'negative_sentiment_comments': _top_comments(cluster_post_comments_df, sentiment=1),
        'neutral_sentiment_comments':  _top_comments(cluster_post_comments_df, sentiment=3),
    })

cluster_summary_list.sort(key=lambda x: x['total_engagement'], reverse=True)
cluster_summary_list = cluster_summary_list[:5]

safe_name = GAME_NAME.replace(' ', '_').replace(':', '')
os.makedirs("cache", exist_ok=True)
output_path = f"cache/_cluster_summary_{safe_name}_{TIMESTAMP}.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(cluster_summary_list, f, ensure_ascii=False, indent=2)

print(f"Saved: {output_path}")
print(f"Total clusters: {len(cluster_summary_list)}")
for c in cluster_summary_list:
    pos = len(c['positive_sentiment_comments'])
    neg = len(c['negative_sentiment_comments'])
    neu = len(c['neutral_sentiment_comments'])
    print(f"  - {c['event_name']} (engagement: {c['total_engagement']}, comments: +{pos}/~{neu}/-{neg})")
