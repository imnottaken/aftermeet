-- AfterMeet MVP initial schema
-- Designed for a single-user-context application without organizations or multi-tenancy.

create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table if not exists public.meetings (
  id uuid primary key default gen_random_uuid(),
  title text,
  original_filename text not null,
  transcript_status text not null default 'pending',
  uploaded_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.transcripts (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid not null unique references public.meetings(id) on delete cascade,
  transcript_text text not null,
  language_detected text,
  duration_seconds integer,
  created_at timestamptz not null default now()
);

create table if not exists public.action_items (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid not null references public.meetings(id) on delete cascade,
  assignee_name text,
  task_description text not null,
  deadline timestamptz,
  status text not null default 'pending',
  created_at timestamptz not null default now()
);

create table if not exists public.decisions (
  id uuid primary key default gen_random_uuid(),
  meeting_id uuid not null references public.meetings(id) on delete cascade,
  decision_text text not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_meetings_transcript_status
  on public.meetings (transcript_status);

create index if not exists idx_meetings_created_at
  on public.meetings (created_at desc);

create index if not exists idx_transcripts_meeting_id
  on public.transcripts (meeting_id);

create index if not exists idx_action_items_meeting_id
  on public.action_items (meeting_id);

create index if not exists idx_action_items_status
  on public.action_items (status);

create index if not exists idx_action_items_deadline
  on public.action_items (deadline);

create index if not exists idx_decisions_meeting_id
  on public.decisions (meeting_id);

drop trigger if exists trg_meetings_updated_at on public.meetings;
create trigger trg_meetings_updated_at
before update on public.meetings
for each row
execute function public.set_updated_at();
