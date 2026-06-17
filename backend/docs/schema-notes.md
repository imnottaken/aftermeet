# Schema Notes

The MVP schema is intentionally minimal:

- `meetings` stores upload metadata and processing state.
- `transcripts` stores the final transcript text for a meeting.
- `action_items` stores extracted tasks from analysis.
- `decisions` stores extracted decisions from analysis.

Design choices:

- `transcripts.meeting_id` is `unique` because the MVP stores one canonical transcript per meeting.
- Foreign keys use `on delete cascade` so deleting a meeting removes derived data cleanly.
- `updated_at` exists only on `meetings` because that is the main mutable parent record in the MVP.
- `title` is nullable so the app can create a meeting record immediately even when the source file has no obvious name.
- `action_items.deadline` is `timestamptz` so the system can preserve exact deadlines when the LLM or user provides them.
- Indexes target the most likely access patterns: list meetings, load one meeting's children, filter action items by status, and inspect deadlines.

Index rationale:

- `idx_meetings_transcript_status`: speeds up status-based polling and dashboard views.
- `idx_meetings_created_at`: speeds up recent-meetings ordering.
- `idx_transcripts_meeting_id`: speeds up transcript lookup for a meeting.
- `idx_action_items_meeting_id`: speeds up loading action items for one meeting.
- `idx_action_items_status`: speeds up filtering pending or completed tasks.
- `idx_action_items_deadline`: speeds up deadline-based sorting and filtering.
- `idx_decisions_meeting_id`: speeds up loading decisions for one meeting.
