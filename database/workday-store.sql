CREATE OR REPLACE FUNCTION public.kaika_workshop_store(p_hash text, p_action text, p_data jsonb DEFAULT '{}'::jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare w uuid; rev bigint; t text; item jsonb; db jsonb='{}'; people jsonb; prev kaika_workshop.commands%rowtype; a uuid; mid uuid;
begin
 select workspace_id into w from kaika_workshop.capabilities where token_hash=p_hash and not revoked and expires_at>now();
 if w is null then raise sqlstate 'PT401' using message='Workshop connection expired or not authorized';end if;
 select revision into rev from kaika_workshop.workspaces where id=w for update;
 if p_action='load' then

select db||jsonb_build_object('goals',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.goals where workspace_id=w;
select db||jsonb_build_object('versions',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.versions where workspace_id=w;
select db||jsonb_build_object('deliverables',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.deliverables where workspace_id=w;
select db||jsonb_build_object('checkpoints',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.checkpoints where workspace_id=w;
select db||jsonb_build_object('measures',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.measures where workspace_id=w;
select db||jsonb_build_object('readings',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.readings where workspace_id=w;
select db||jsonb_build_object('evidence',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.evidence where workspace_id=w;
select db||jsonb_build_object('acceptances',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.acceptances where workspace_id=w;
select db||jsonb_build_object('allocations',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.allocations where workspace_id=w;
select db||jsonb_build_object('approvals',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.approvals where workspace_id=w;
select db||jsonb_build_object('checkins',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.checkins where workspace_id=w;
select db||jsonb_build_object('portfolios',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.portfolios where workspace_id=w;
select db||jsonb_build_object('portfolio_goals',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.portfolio_goals where workspace_id=w;
select db||jsonb_build_object('questions',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.questions where workspace_id=w;
select db||jsonb_build_object('decisions',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.decisions where workspace_id=w;
select db||jsonb_build_object('reviews',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.reviews where workspace_id=w;
select db||jsonb_build_object('saved_views',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.saved_views where workspace_id=w;
select db||jsonb_build_object('reflections',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.reflections where workspace_id=w;
select db||jsonb_build_object('replies',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.replies where workspace_id=w;
select db||jsonb_build_object('followups',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.followups where workspace_id=w;
select db||jsonb_build_object('kpis',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.kpis where workspace_id=w;
select db||jsonb_build_object('kpi_readings',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.kpi_readings where workspace_id=w;
select db||jsonb_build_object('support_requests',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.support_requests where workspace_id=w;
select db||jsonb_build_object('strategies',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.strategies where workspace_id=w;
select db||jsonb_build_object('pillars',coalesce(jsonb_agg(payload order by id),'[]')) into db from kaika_workshop.pillars where workspace_id=w;
return jsonb_build_object('revision',rev,'workspace_id',w,'db',db,'people',(select coalesce(jsonb_agg(payload order by id),'[]') from kaika_workshop.people where workspace_id=w),'as_of',(select as_of from kaika_workshop.workspaces where id=w),'scenario',(select scenario from kaika_workshop.workspaces where id=w),'organization',(select (to_jsonb(s)-'tenant_id'-'workspace_id')||jsonb_build_object('source','workday','mock_activity',true) from kaika_workshop.organization_sources s where s.workspace_id=w));
 elsif p_action='commit' then
 mid=(p_data->>'mutation_id')::uuid;a=(p_data->>'leader_id')::uuid;
 select * into prev from kaika_workshop.commands where workspace_id=w and mutation_id=mid;
 if found then
  if prev.request_hash<>p_data->>'request_hash' or prev.leader_id is distinct from a then raise sqlstate 'PT409' using message='Mutation identifier reused';end if;
  return jsonb_build_object('revision',rev,'result',prev.result,'replayed',true);
 end if;
 if not exists(select 1 from kaika_workshop.people where workspace_id=w and id=a) then raise sqlstate 'PT403' using message='Unknown workshop persona';end if;
 if rev<>(p_data->>'revision')::bigint then raise sqlstate 'PT409' using message='Workspace changed. Refresh and retry; your changes were not committed.';end if;

for t in select jsonb_object_keys(p_data->'changes') loop
 if not t=any(array['goals','versions','deliverables','checkpoints','measures','readings','evidence','acceptances','allocations','approvals','checkins','portfolios','portfolio_goals','questions','decisions','reviews','saved_views','reflections','replies','followups','kpis','kpi_readings','support_requests','strategies','pillars']) then raise exception 'Unknown entity';end if;

for item in select jsonb_array_elements(coalesce(p_data->'changes'->t->'remove','[]')) loop
 execute format('delete from kaika_workshop.%I where workspace_id=$1 and id=$2',t) using w,(item#>>'{}')::uuid;
end loop;
for item in select jsonb_array_elements(coalesce(p_data->'changes'->t->'upsert','[]')) loop
 execute format('insert into kaika_workshop.%I(workspace_id,id,payload) values($1,$2,$3) on conflict(workspace_id,id) do update set payload=excluded.payload,updated_at=now()',t) using w,(item->>'id')::uuid,item;
end loop;
end loop;
-- Integrity is checked over the committed relational graph, not trusted UI labels.
if exists(select 1 from kaika_workshop.deliverables d join kaika_workshop.versions v on v.workspace_id=w and v.id=d.version_id join kaika_workshop.goals g on g.workspace_id=w and g.id=v.goal_id where d.workspace_id=w and g.node_kind<>'workstream') then raise exception 'Deliverables must attach to workstreams';end if;
if exists(with recursive tree as (select id,parent_id,array[id] path,false cycle from kaika_workshop.goals where workspace_id=w union all select g.id,g.parent_id,t.path||g.id,g.id=any(t.path) from tree t join kaika_workshop.goals g on g.workspace_id=w and g.id=t.parent_id where not t.cycle) select 1 from tree where cycle) then raise exception 'Hierarchy cycle';end if;
if exists(select 1 from kaika_workshop.evidence e where e.workspace_id=w and e.upload_state='complete' and not exists(select 1 from storage.objects o where o.bucket_id='kaika-deliverable-evidence' and o.name=e.object_path and (o.metadata->>'size')::bigint=e.byte_size)) then raise exception 'Completed evidence requires a matching private Storage object';end if;
insert into kaika_workshop.commands(workspace_id,mutation_id,leader_id,request_hash,result) values(w,mid,a,p_data->>'request_hash',p_data->'result');
update kaika_workshop.workspaces set revision=revision+1 where id=w returning revision into rev;
return jsonb_build_object('revision',rev,'result',p_data->'result');
elsif p_action='lookup' then
 select * into prev from kaika_workshop.commands where workspace_id=w and mutation_id=(p_data->>'mutation_id')::uuid;
 if not found then return null;end if;
 if prev.request_hash<>p_data->>'request_hash' or prev.leader_id is distinct from (p_data->>'leader_id')::uuid then raise sqlstate 'PT409' using message='Mutation identifier reused';end if;
 return jsonb_build_object('result',prev.result);
elsif p_action='upload_context' then
return (select jsonb_build_object('workspace_id',w,'deliverable',d.payload,'version',v.payload,'goal',g.payload,'checkpoints',(select coalesce(jsonb_agg(c.payload),'[]') from kaika_workshop.checkpoints c where c.workspace_id=w and c.deliverable_id=d.id)) from kaika_workshop.deliverables d join kaika_workshop.versions v on v.workspace_id=w and v.id=d.version_id join kaika_workshop.goals g on g.workspace_id=w and g.id=v.goal_id where d.workspace_id=w and d.id=(p_data->>'deliverable_id')::uuid);
elsif p_action='file' then
return (select payload from kaika_workshop.evidence where workspace_id=w and id=(p_data->>'evidence_id')::uuid);
end if;
raise exception 'Unsupported workshop operation';
end $function$
