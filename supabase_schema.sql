-- Run this in your Supabase project's SQL Editor (left sidebar -> SQL
-- Editor -> New query). Covers three tables this version of the app
-- uses: user_projects (Cloud Database Save/Load), drawings_registry
-- (Drawing Upload Hub), and logo_library (saved logo choices).
--
-- IMPORTANT - read this before running: since this version has no real
-- login (just a self-reported "Your Name / Email" text field), there is
-- no auth.uid() to restrict access by. That means Row Level Security
-- as used in the earlier OTP-login version doesn't apply here - anyone
-- with your Supabase anon key (which is public-ish by design, it's what
-- ships inside the app) can technically read/write any row in these
-- tables directly via the API, not just through the app's own UI. For a
-- small trusted internal team this is a reasonable, deliberate tradeoff
-- (matches what was asked for - simplicity over strict access control) -
-- just worth knowing plainly rather than assuming it's private.

create table if not exists user_projects (
    id uuid primary key default gen_random_uuid(),
    project_name text not null unique,
    user_email text not null,
    design_data jsonb not null,
    created_at timestamptz default now(),
    updated_at timestamptz default now()
);

create table if not exists drawings_registry (
    id uuid primary key default gen_random_uuid(),
    project_name text not null,
    uploaded_by text not null,
    file_name text not null,
    file_url text not null,
    created_at timestamptz default now()
);

-- Saved logo choices - a small library so a logo you've uploaded once
-- can be picked again later instead of re-uploading every session.
create table if not exists logo_library (
    id uuid primary key default gen_random_uuid(),
    label text not null unique,
    file_url text not null,
    uploaded_by text,
    created_at timestamptz default now()
);

-- Keep updated_at current automatically on user_projects.
create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists user_projects_set_updated_at on user_projects;
create trigger user_projects_set_updated_at
    before update on user_projects
    for each row
    execute function set_updated_at();

-- RLS is deliberately left OFF on all tables (see the note above) -
-- if you later want per-user isolation enforced by the database itself
-- rather than just app-level convention, that needs real Supabase Auth
-- (login) wired back in, which is a bigger change than this schema.
