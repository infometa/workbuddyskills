import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8')

csv_path = sys.argv[1]
df = pd.read_csv(csv_path, encoding='utf-8')
data = df[['content', 'engagement', 'content_url', 'channel_name', 'comment_id']].head(50)
for i, row in data.iterrows():
    content = str(row['content']).replace('\n', ' ')[:200]
    print(f"{i+1}. [{row['engagement']}] {row['channel_name']} | {content}")
