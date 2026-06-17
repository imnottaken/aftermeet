# Schema Notes

The MVP schema is intentionally minimal:

- `meetings` stores upload metadata and processing state.
- `transcripts` stores the final transcript text for a meeting.
- `action_items` stores extracted tasks from analysis.
- `decisions` stores extracted decisions from analysis.

Design choices:

- `transcripts.meeting_id` is `unique` because the MVP stores one canonical transcript per meeting.
- `action_items.status` is constrained to a small enum-like text set to keep it simple and queryable.
- Foreign keys use `on delete cascade` so deleting a meeting removes derived data cleanly.
- `updated_at` exists only on `meetings` because that is the main mutable parent record in the MVP.
- Indexes target the most likely access patterns: list meetings, load one meeting's children, filter action items by status, and inspect deadlines.

