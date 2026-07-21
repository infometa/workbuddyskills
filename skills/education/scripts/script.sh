#!/usr/bin/env bash
set -euo pipefail

###############################################################################
# education/scripts/script.sh — Study plan generator, quiz maker, flashcards,
# progress tracker, scheduler, and review list builder.
###############################################################################

DATA_DIR="${HOME}/.education"
PROGRESS_FILE="${DATA_DIR}/progress.json"

ensure_data_dir() {
  mkdir -p "${DATA_DIR}"
  if [[ ! -f "${PROGRESS_FILE}" ]]; then
    echo '{}' > "${PROGRESS_FILE}"
  fi
}

# ─── plan ────────────────────────────────────────────────────────────────────

cmd_plan() {
  local topic="" weeks=4 level="beginner" output="text"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --weeks)  weeks="$2"; shift 2 ;;
      --level)  level="$2"; shift 2 ;;
      --output) output="$2"; shift 2 ;;
      -*)       echo "Unknown flag: $1" >&2; return 1 ;;
      *)        topic="$1"; shift ;;
    esac
  done

  if [[ -z "${topic}" ]]; then
    echo "Usage: script.sh plan <topic> [--weeks N] [--level beginner|intermediate|advanced] [--output json|text]" >&2
    return 1
  fi

  local hours_per_week
  case "${level}" in
    beginner)     hours_per_week=5  ;;
    intermediate) hours_per_week=8  ;;
    advanced)     hours_per_week=12 ;;
    *)            echo "Invalid level: ${level}" >&2; return 1 ;;
  esac

  if [[ "${output}" == "json" ]]; then
    echo "{"
    echo "  \"topic\": \"${topic}\","
    echo "  \"level\": \"${level}\","
    echo "  \"weeks\": ${weeks},"
    echo "  \"hours_per_week\": ${hours_per_week},"
    echo "  \"total_hours\": $(( weeks * hours_per_week )),"
    echo "  \"plan\": ["
    for (( w=1; w<=weeks; w++ )); do
      local comma=","
      [[ ${w} -eq ${weeks} ]] && comma=""
      echo "    {\"week\": ${w}, \"focus\": \"Week ${w} — ${topic} block ${w}\", \"hours\": ${hours_per_week}}${comma}"
    done
    echo "  ]"
    echo "}"
  else
    echo "=== Study Plan: ${topic} ==="
    echo "Level: ${level} | Duration: ${weeks} weeks | ${hours_per_week}h/week | Total: $(( weeks * hours_per_week ))h"
    echo ""
    for (( w=1; w<=weeks; w++ )); do
      echo "  Week ${w}: ${topic} — block ${w} (${hours_per_week}h)"
    done
    echo ""
    echo "Tip: Run 'script.sh schedule ${topic}' to create daily time blocks."
  fi
}

# ─── quiz ────────────────────────────────────────────────────────────────────

cmd_quiz() {
  local topic="" count=5 qtype="mcq" difficulty="medium"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --count)      count="$2"; shift 2 ;;
      --type)       qtype="$2"; shift 2 ;;
      --difficulty) difficulty="$2"; shift 2 ;;
      -*)           echo "Unknown flag: $1" >&2; return 1 ;;
      *)            topic="$1"; shift ;;
    esac
  done

  if [[ -z "${topic}" ]]; then
    echo "Usage: script.sh quiz <topic> [--count N] [--type mcq|truefalse|short] [--difficulty easy|medium|hard]" >&2
    return 1
  fi

  echo "=== Quiz: ${topic} ==="
  echo "Type: ${qtype} | Difficulty: ${difficulty} | Questions: ${count}"
  echo ""

  for (( i=1; i<=count; i++ )); do
    echo "Q${i}. [${qtype}] [${difficulty}] Question about ${topic} — concept ${i}"
    case "${qtype}" in
      mcq)
        echo "    A) Option A"
        echo "    B) Option B"
        echo "    C) Option C"
        echo "    D) Option D"
        ;;
      truefalse)
        echo "    [ ] True   [ ] False"
        ;;
      short)
        echo "    Answer: _______________"
        ;;
    esac
    echo ""
  done

  echo "Generated ${count} ${qtype} questions at ${difficulty} difficulty."
}

# ─── flashcard ───────────────────────────────────────────────────────────────

cmd_flashcard() {
  local topic="" count=10 format="plain"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --count)  count="$2"; shift 2 ;;
      --format) format="$2"; shift 2 ;;
      -*)       echo "Unknown flag: $1" >&2; return 1 ;;
      *)        topic="$1"; shift ;;
    esac
  done

  if [[ -z "${topic}" ]]; then
    echo "Usage: script.sh flashcard <topic> [--count N] [--format plain|csv|json]" >&2
    return 1
  fi

  case "${format}" in
    csv)
      echo "front,back"
      for (( i=1; i<=count; i++ )); do
        echo "\"${topic} concept ${i}\",\"Definition/explanation for concept ${i}\""
      done
      ;;
    json)
      echo "["
      for (( i=1; i<=count; i++ )); do
        local comma=","
        [[ ${i} -eq ${count} ]] && comma=""
        echo "  {\"front\": \"${topic} concept ${i}\", \"back\": \"Definition for concept ${i}\"}${comma}"
      done
      echo "]"
      ;;
    plain|*)
      echo "=== Flashcards: ${topic} (${count} cards) ==="
      echo ""
      for (( i=1; i<=count; i++ )); do
        echo "Card ${i}:"
        echo "  Front: ${topic} — concept ${i}"
        echo "  Back:  Definition/explanation for concept ${i}"
        echo ""
      done
      ;;
  esac
}

# ─── progress ────────────────────────────────────────────────────────────────

cmd_progress() {
  ensure_data_dir
  local topic="" mark="" reset=false

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --topic) topic="$2"; shift 2 ;;
      --mark)  mark="$2"; shift 2 ;;
      --reset) reset=true; shift ;;
      -*)      echo "Unknown flag: $1" >&2; return 1 ;;
      *)       topic="$1"; shift ;;
    esac
  done

  if [[ "${reset}" == true ]]; then
    if [[ -n "${topic}" ]]; then
      local tmp
      tmp=$(PROGRESS_FILE="$PROGRESS_FILE" TOPIC="$topic" python3 << 'PYEOF'
import json, sys, os
progress_file = os.environ["PROGRESS_FILE"]
topic = os.environ["TOPIC"]
d = json.load(open(progress_file))
d.pop(topic, None)
json.dump(d, sys.stdout, indent=2)
PYEOF
)
      echo "${tmp}" > "${PROGRESS_FILE}"
      echo "Progress reset for topic: ${topic}"
    else
      echo '{}' > "${PROGRESS_FILE}"
      echo "All progress reset."
    fi
    return 0
  fi

  if [[ -n "${mark}" && -n "${topic}" ]]; then
    local tmp
    tmp=$(PROGRESS_FILE="$PROGRESS_FILE" TOPIC="$topic" MARK="$mark" python3 << 'PYEOF'
import json, sys, datetime, os
progress_file = os.environ["PROGRESS_FILE"]
topic = os.environ["TOPIC"]
mark = os.environ["MARK"]
d = json.load(open(progress_file))
if topic not in d:
    d[topic] = {'milestones': [], 'started': str(datetime.date.today())}
d[topic]['milestones'].append({'name': mark, 'date': str(datetime.date.today())})
json.dump(d, sys.stdout, indent=2)
PYEOF
)
    echo "${tmp}" > "${PROGRESS_FILE}"
    echo "Marked milestone '${mark}' for topic '${topic}'."
    return 0
  fi

  # Show progress
  if [[ -n "${topic}" ]]; then
    PROGRESS_FILE="$PROGRESS_FILE" TOPIC="$topic" python3 << 'PYEOF'
import json, os
progress_file = os.environ["PROGRESS_FILE"]
topic = os.environ["TOPIC"]
d = json.load(open(progress_file))
t = d.get(topic)
if not t:
    print(f'No progress recorded for: {topic}')
else:
    print(f'=== Progress: {topic} ===')
    print(f'Started: {t.get("started", "unknown")}')
    ms = t.get('milestones', [])
    print(f'Milestones: {len(ms)}')
    for m in ms:
        print(f'  ✓ {m["name"]} ({m["date"]})')
PYEOF
  else
    PROGRESS_FILE="$PROGRESS_FILE" python3 << 'PYEOF'
import json, os
progress_file = os.environ["PROGRESS_FILE"]
d = json.load(open(progress_file))
if not d:
    print('No progress recorded yet.')
else:
    for topic, info in d.items():
        ms = info.get('milestones', [])
        print(f'{topic}: {len(ms)} milestones (started {info.get("started", "?")})')
PYEOF
  fi
}

# ─── schedule ────────────────────────────────────────────────────────────────

cmd_schedule() {
  local topic="" hours_per_day=2 days=7 start_date=""

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --hours-per-day) hours_per_day="$2"; shift 2 ;;
      --days)          days="$2"; shift 2 ;;
      --start)         start_date="$2"; shift 2 ;;
      -*)              echo "Unknown flag: $1" >&2; return 1 ;;
      *)               topic="$1"; shift ;;
    esac
  done

  if [[ -z "${topic}" ]]; then
    echo "Usage: script.sh schedule <topic> [--hours-per-day N] [--days N] [--start YYYY-MM-DD]" >&2
    return 1
  fi

  if [[ -z "${start_date}" ]]; then
    start_date=$(date +%Y-%m-%d)
  fi

  echo "=== Study Schedule: ${topic} ==="
  echo "Start: ${start_date} | ${days} days | ${hours_per_day}h/day | Total: $(( days * hours_per_day ))h"
  echo ""

  START_DATE="$start_date" DAYS="$days" TOPIC="$topic" HOURS_PER_DAY="$hours_per_day" python3 << 'PYEOF'
import datetime, os
start_date = os.environ["START_DATE"]
days = int(os.environ["DAYS"])
topic = os.environ["TOPIC"]
hours_per_day = os.environ["HOURS_PER_DAY"]
start = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
for i in range(days):
    d = start + datetime.timedelta(days=i)
    weekday = d.strftime('%A')
    print(f'  {d} ({weekday}): {topic} — {hours_per_day}h study block')
PYEOF
  echo ""
  echo "Total study time: $(( days * hours_per_day )) hours over ${days} days."
}

# ─── review ──────────────────────────────────────────────────────────────────

cmd_review() {
  ensure_data_dir
  local topic="" scope="all" format="checklist"

  while [[ $# -gt 0 ]]; do
    case "$1" in
      --scope)  scope="$2"; shift 2 ;;
      --format) format="$2"; shift 2 ;;
      -*)       echo "Unknown flag: $1" >&2; return 1 ;;
      *)        topic="$1"; shift ;;
    esac
  done

  if [[ -z "${topic}" ]]; then
    echo "Usage: script.sh review <topic> [--scope all|weak|recent] [--format checklist|summary]" >&2
    return 1
  fi

  echo "=== Review: ${topic} ==="
  echo "Scope: ${scope} | Format: ${format}"
  echo ""

  # Check if progress exists for this topic
  local milestone_count
  milestone_count=$(PROGRESS_FILE="$PROGRESS_FILE" TOPIC="$topic" python3 << 'PYEOF'
import json, os
progress_file = os.environ["PROGRESS_FILE"]
topic = os.environ["TOPIC"]
d = json.load(open(progress_file))
t = d.get(topic, {})
print(len(t.get('milestones', [])))
PYEOF
  2>/dev/null || echo "0")

  if [[ "${format}" == "summary" ]]; then
    echo "Topic: ${topic}"
    echo "Milestones completed: ${milestone_count}"
    echo "Review scope: ${scope}"
    echo ""
    echo "Summary: Review all ${scope} areas of ${topic}."
    if [[ "${scope}" == "weak" ]]; then
      echo "Focus on areas with fewer milestones or longer gaps."
    elif [[ "${scope}" == "recent" ]]; then
      echo "Focus on the most recently studied material."
    fi
  else
    echo "Review Checklist for ${topic} (${scope}):"
    echo ""
    echo "  [ ] Review core concepts"
    echo "  [ ] Practice key problems"
    echo "  [ ] Re-read notes"
    echo "  [ ] Test with flashcards (run: script.sh flashcard ${topic})"
    echo "  [ ] Take a quiz (run: script.sh quiz ${topic})"
    if [[ "${milestone_count}" -gt 0 ]]; then
      echo "  [ ] Review ${milestone_count} completed milestones"
    fi
    if [[ "${scope}" == "weak" ]]; then
      echo "  [ ] Identify and drill weak points"
    fi
  fi
}

# ─── help ────────────────────────────────────────────────────────────────────

cmd_help() {
  cat <<'EOF'
education — Study plan generator, quiz maker, flashcards, and progress tracker.

Commands:
  plan       Generate a structured learning plan for a topic
  quiz       Generate quiz questions on a topic
  flashcard  Generate flashcards for key concepts
  progress   Track and display learning progress
  schedule   Create a study schedule with daily time blocks
  review     Generate a review checklist from completed topics
  help       Show this help message

Examples:
  script.sh plan python --weeks 6 --level intermediate
  script.sh quiz math --count 10 --type mcq --difficulty hard
  script.sh flashcard biology --count 20 --format csv
  script.sh progress --topic python --mark "finished chapter 3"
  script.sh schedule history --hours-per-day 1 --days 14
  script.sh review chemistry --scope weak --format checklist
EOF
}

# ─── main dispatch ───────────────────────────────────────────────────────────

main() {
  if [[ $# -lt 1 ]]; then
    cmd_help
    exit 1
  fi

  local command="$1"
  shift

  case "${command}" in
    plan)      cmd_plan "$@" ;;
    quiz)      cmd_quiz "$@" ;;
    flashcard) cmd_flashcard "$@" ;;
    progress)  cmd_progress "$@" ;;
    schedule)  cmd_schedule "$@" ;;
    review)    cmd_review "$@" ;;
    help|--help|-h) cmd_help ;;
    *)
      echo "Unknown command: ${command}" >&2
      echo "Run 'script.sh help' for usage." >&2
      exit 1
      ;;
  esac
}

main "$@"
