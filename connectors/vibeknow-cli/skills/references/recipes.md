# vibeknow-create Advanced Recipes

## Async Submit + Later Follow-up

Use `--async` when you want to submit and move on:

```bash
# Submit — returns immediately
output=$(vibeknow create --from report.pdf --async --output json)
task_id=$(echo "$output" | jq -r '.task_id')
session_id=$(echo "$output" | jq -r '.session_id')

# ... do other work ...

# Check status
vibeknow video status "$task_id" --session-id "$session_id" --output json

# Or block until done
vibeknow video wait "$task_id" --session-id "$session_id"
```

## Retry on Exit Code 4

Exit code 4 means the task failed but is retryable (e.g. transient backend error):

```bash
max_retries=3
for i in $(seq 1 $max_retries); do
  vibeknow create --from slides.pdf
  exit_code=$?
  [ "$exit_code" -eq 0 ] && break
  if [ "$exit_code" -eq 4 ]; then
    echo "Attempt $i failed (retryable), retrying..." >&2
    sleep $((i * 5))
  else
    echo "Failed with exit code $exit_code (not retryable)" >&2
    exit $exit_code
  fi
done
```

## Recover from Exit Code 6 (Stream Interrupted)

Exit code 6 means the SSE stream broke during a sync `create` or `video wait`. The task may still be running server-side. **Never re-submit** — use `wait` to reconnect:

```bash
# Sync create exits 6 — the task was submitted but we lost the stream.
# The task_id and session_id were printed before the stream started.
# Use them to reconnect:
vibeknow video wait "$task_id" --session-id "$session_id"
if [ $? -eq 6 ]; then
  sleep 10
  vibeknow video wait "$task_id" --session-id "$session_id"
fi
```

To make recovery easier, use `--async` to capture IDs before streaming:

```bash
vibeknow create --from slides.pdf --async --output json > /tmp/submit.json
task_id=$(jq -r '.task_id' /tmp/submit.json)
session_id=$(jq -r '.session_id' /tmp/submit.json)
vibeknow video wait "$task_id" --session-id "$session_id"
```

## Batch Create (Multiple Documents)

Submit multiple videos in parallel using `--async`, then collect results:

```bash
# Submit all
for file in docs/*.pdf; do
  vibeknow create --from "$file" --async --output json >> /tmp/tasks.jsonl
done

# Wait for each
while IFS= read -r line; do
  task_id=$(echo "$line" | jq -r '.task_id')
  session_id=$(echo "$line" | jq -r '.session_id')
  echo "Waiting for $task_id..."
  vibeknow video wait "$task_id" --session-id "$session_id"
done < /tmp/tasks.jsonl
```

## NDJSON Streaming with jq (Agent Pattern)

Parse events in real-time for programmatic control:

```bash
vibeknow create --from doc_abc --output ndjson 2>/dev/null | while IFS= read -r line; do
  event=$(echo "$line" | jq -r '.event')
  case "$event" in
    stage.started)
      stage=$(echo "$line" | jq -r '.stage')
      echo "Stage: $stage" >&2
      ;;
    stage.progress)
      pct=$(echo "$line" | jq -r '.percent')
      echo "Progress: $pct%" >&2
      ;;
    task.succeeded)
      echo "$line" | jq -r '.video_url'
      ;;
    task.failed)
      echo "$line" | jq -r '.error_message' >&2
      exit 1
      ;;
  esac
done
```

## Download with Custom Path

```bash
vibeknow video download t_xxx --session-id s_yyy --dest ./renders/final.mp4

# Overwrite existing file
vibeknow video download t_xxx --session-id s_yyy --dest ./renders/final.mp4 --overwrite
```

If download is interrupted, re-run the same command — HTTP Range resume is automatic.
