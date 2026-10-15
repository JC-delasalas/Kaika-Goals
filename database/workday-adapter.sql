-- Generic adapter only. Tenant-specific import mappings are deliberately excluded.

create table if not exists kaika_workshop.organization_sources(
 workspace_id uuid primary key references kaika_workshop.workspaces(id),
 tenant_id uuid not null, import_id uuid not null,
 foreign key(tenant_id,import_id) references kaika.import_runs(tenant_id,id),
 preferred_leader_id uuid not null, synced_at timestamptz not null default now(),
 source_as_of date not null, active_workers integer not null, excluded_inactive integer not null,
 quarantined_workers integer not null, unresolved_roots integer not null,
 effective_time_known boolean not null default false
);
alter table kaika_workshop.organization_sources enable row level security;
revoke all on kaika_workshop.organization_sources from public,anon,authenticated;
create table if not exists kaika_workshop.organization_transition_backups(
 workspace_id uuid not null references kaika_workshop.workspaces(id), transition text not null,
 entity text not null, entity_id uuid not null, payload jsonb not null,
 captured_at timestamptz not null default now(), primary key(workspace_id,transition,entity,entity_id)
);
alter table kaika_workshop.organization_transition_backups enable row level security;
revoke all on kaika_workshop.organization_transition_backups from public,anon,authenticated;
create table if not exists kaika_workshop.demo_identity_mapping(
 workspace_id uuid not null references kaika_workshop.workspaces(id), synthetic_person_id uuid not null,
 worker_id uuid not null, primary key(workspace_id,synthetic_person_id)
);
alter table kaika_workshop.demo_identity_mapping enable row level security;
revoke all on kaika_workshop.demo_identity_mapping from public,anon,authenticated;
-- Exact JSON values are remapped. Free-text evidence is preserved as original mock history.
create or replace function kaika_workshop.remap_demo_json(value jsonb,mapping jsonb)
returns jsonb language plpgsql immutable set search_path='' as $$
declare output jsonb;
begin
 case jsonb_typeof(value)
 when 'string' then return coalesce(mapping->(value#>>'{}'),value);
 when 'array' then select coalesce(jsonb_agg(kaika_workshop.remap_demo_json(e,mapping) order by n),'[]') into output from jsonb_array_elements(value) with ordinality a(e,n);return output;
 when 'object' then select coalesce(jsonb_object_agg(k,kaika_workshop.remap_demo_json(v,mapping)),'{}') into output from jsonb_each(value) a(k,v);return output;
 else return value;
 end case;
end $$;
revoke all on function kaika_workshop.remap_demo_json(jsonb,jsonb) from public,anon,authenticated;

-- Pinned, reconciled import: no name matching, no pro-forma organization, no HR write-back.
create or replace function kaika_workshop.refresh_workday_roster(w uuid)
returns integer language plpgsql security definer set search_path='' as $$
declare src kaika_workshop.organization_sources%rowtype; changed integer; inactive_count integer;
begin
 select * into strict src from kaika_workshop.organization_sources where workspace_id=w;
 perform 1 from kaika_workshop.workspaces where id=w for update;
 if not exists(select 1 from kaika.import_runs where id=src.import_id and tenant_id=src.tenant_id and status='reconciled') then raise exception 'A reconciled source import is required';end if;
 if exists(select worker_id from kaika.worker_assignments where tenant_id=src.tenant_id and import_id=src.import_id group by worker_id having count(*)>1) then raise exception 'Ambiguous worker assignments require reconciliation';end if;
 if exists(with recursive chain as(
  select worker_id,manager_id,array[worker_id] path,false cycle from kaika.worker_assignments where tenant_id=src.tenant_id and import_id=src.import_id and source_active and not coalesce(source_terminated,false)
  union all select c.worker_id,a.manager_id,c.path||a.worker_id,a.worker_id=any(c.path) from chain c join kaika.worker_assignments a on a.worker_id=c.manager_id and a.tenant_id=src.tenant_id and a.import_id=src.import_id where not c.cycle
 )select 1 from chain where cycle) then raise exception 'Workday manager cycle';end if;
 if exists(select 1 from kaika.worker_assignments a left join kaika.worker_assignments m on m.worker_id=a.manager_id and m.import_id=a.import_id and m.tenant_id=a.tenant_id and m.source_active and not coalesce(m.source_terminated,false) where a.import_id=src.import_id and a.tenant_id=src.tenant_id and a.source_active and not coalesce(a.source_terminated,false) and a.manager_id is not null and m.worker_id is null) then raise exception 'Active worker has an unavailable manager; reconcile before publishing';end if;
 insert into kaika_workshop.people(workspace_id,id,payload)
 select w,p.id,jsonb_build_object('id',p.id,'name',p.display_name,'title',a.business_title,'team',coalesce(o.name,'Unassigned organization'),'manager_id',a.manager_id,'org_id',a.org_id,'source_system','workday','source_worker_id',p.id,'source_import_id',src.import_id,'observed_at',a.observed_at,'source_active',true,'worker_type',a.worker_type,'source_fte',a.source_fte,'site_weekly_hours',a.site_weekly_hours,'capacity_verified',a.capacity_verified,'synthetic',false,'hierarchy_note',case when a.manager_id is null then 'Manager unresolved in the imported population; scope stops here.' else null end)
 from kaika.workers p join kaika.worker_assignments a on a.worker_id=p.id and a.tenant_id=p.tenant_id left join kaika.org_units o on o.id=a.org_id and o.tenant_id=a.tenant_id
 where p.tenant_id=src.tenant_id and a.import_id=src.import_id and a.source_active and not coalesce(a.source_terminated,false)
 on conflict(workspace_id,id) do update set payload=excluded.payload,updated_at=now() where kaika_workshop.people.payload is distinct from excluded.payload;
 get diagnostics changed=row_count;
 -- Preserve identity/history for leavers, but remove them from current switcher and assignment scopes.
 update kaika_workshop.people p set payload=p.payload||'{"source_active":false,"manager_id":null}'::jsonb,updated_at=now()
 where p.workspace_id=w and p.payload->>'source_system'='workday' and (p.payload->>'source_active')::boolean and not exists(select 1 from kaika.worker_assignments a where a.worker_id=p.id and a.tenant_id=src.tenant_id and a.import_id=src.import_id and a.source_active and not coalesce(a.source_terminated,false));
 get diagnostics inactive_count=row_count;
 if changed+inactive_count>0 then
 update kaika_workshop.workspaces set revision=revision+1 where id=w;
 update kaika_workshop.organization_sources set synced_at=now(),active_workers=(select count(*) from kaika_workshop.people where workspace_id=w and payload->>'source_system'='workday' and (payload->>'source_active')::boolean) where workspace_id=w;
 end if;
 return changed+inactive_count;
end $$;
revoke all on function kaika_workshop.refresh_workday_roster(uuid) from public,anon,authenticated;
