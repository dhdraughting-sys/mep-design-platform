-- Run this in your Supabase project's SQL Editor (left sidebar -> SQL Editor -> New query)
-- before using the cloud save/load feature. Safe to run once; re-running
-- is harmless since "if not exists" / "or replace" guard every statement.

create table if not exists projects (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references auth.users(id) not null,
    project_name text not null,
    data jsonb not null,
    created_at timestamptz default now(),
    updated_at timestamptz default now(),
    unique (user_id, project_name)
);

-- Row Level Security: without this, ANY logged-in user could read or
-- overwrite anyone else's saved projects. This restricts every operation
-- to rows where the project's user_id matches whoever is currently
-- authenticated (auth.uid()).
alter table projects enable row level security;

drop policy if exists "Users can view their own projects" on projects;
create policy "Users can view their own projects"
    on projects for select
    using (auth.uid() = user_id);

drop policy if exists "Users can insert their own projects" on projects;
create policy "Users can insert their own projects"
    on projects for insert
    with check (auth.uid() = user_id);

drop policy if exists "Users can update their own projects" on projects;
create policy "Users can update their own projects"
    on projects for update
    using (auth.uid() = user_id);

drop policy if exists "Users can delete their own projects" on projects;
create policy "Users can delete their own projects"
    on projects for delete
    using (auth.uid() = user_id);

-- Keep updated_at current automatically whenever a row changes.
create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

drop trigger if exists projects_set_updated_at on projects;
create trigger projects_set_updated_at
    before update on projects
    for each row
    execute function set_updated_at();
