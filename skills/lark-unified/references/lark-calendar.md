# Lark-Calendar - Scheduling & Events

**Important**: Read `lark-shared` reference first for authentication and permission basics.

## Core Concepts

- **Calendar**: Personal or shared calendar
- **Event**: Meeting or appointment with attendees
- **Freebusy**: Busy/available time slots for user
- **Attendee**: Participant in event (RSVP status: accept, decline, tentative, no_reply)
- **Organizer**: Creator/owner of event

## Common Scenarios

### 1. Book an Event
```bash
lark-cli calendar +create --user ou_xxx --title "Team Sync" --start-time 2024-02-15T10:00:00 --end-time 2024-02-15T11:00:00 --attendees "user1@example.com" "user2@example.com"
```

### 2. Check Availability
```bash
lark-cli calendar +freebusy --user ou_xxx --start-time 2024-02-15T08:00:00 --end-time 2024-02-15T18:00:00
```

### 3. Suggest Meeting Times
```bash
lark-cli calendar +suggestion --user ou_xxx --duration 60 --start-time 2024-02-15 --end-time 2024-02-20 --attendees "user1@example.com" "user2@example.com"
```

### 4. View Today's Agenda
```bash
lark-cli calendar +agenda
```

## Common Shortcuts

| Shortcut | Description |
|----------|-------------|
| `+agenda` | Quick overview of today/upcoming events |
| `+create` | Create event and optionally invite attendees |
| `+freebusy` | Query user's busy/free times and RSVP status |
| `+suggestion` | Suggest meeting times based on attendees' availability |
| `+list` | List events in calendar |
| `+search` | Search events by keyword/organizer/attendee |

## API Resources

### calendars
- `list` — List user's calendars
- `get` — Get calendar details

### events
- `create` — Create event
- `list` — List events in calendar
- `search` — Search events
- `update` — Update event
- `delete` — Delete event
- `get` — Get event details

### freebusy
- `query` — Query user's free/busy times and RSVP status

### calendars.events.attendees
- `create` — Add attendee to event
- `delete` — Remove attendee

## Permission Table

| Method | Required Scope |
|--------|----------------|
| calendars.list | calendar:calendar:read |
| calendars.get | calendar:calendar:read |
| events.create | calendar:event:create |
| events.list | calendar:event:read |
| events.update | calendar:event:edit |
| events.delete | calendar:event:delete |
| freebusy.query | calendar:calendar:read |

