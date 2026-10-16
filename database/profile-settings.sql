-- Private, bounded avatar thumbnails; originals and EXIF are never retained.
create table if not exists kaika_workshop.profiles (
 workspace_id uuid not null,
 person_id uuid not null,
 avatar_style integer not null default 0 check (avatar_style between 0 and 5),
 photo_data_url text check (photo_data_url is null or (length(photo_data_url)<=43000 and photo_data_url ~ '^data:image/jpeg;base64,[A-Za-z0-9+/]+=*$')),
 revision integer not null default 1,
 updated_at timestamptz not null default now(),
 primary key(workspace_id,person_id),
 foreign key(workspace_id,person_id) references kaika_workshop.people(workspace_id,id)
);
alter table kaika_workshop.profiles enable row level security;
revoke all on kaika_workshop.profiles from public,anon,authenticated;
create or replace function public.kaika_workshop_profile(p_hash text,p_action text,p_data jsonb default '{}') returns jsonb
language plpgsql security definer set search_path='' as $$
declare w uuid; a uuid; pid uuid; rev integer; prior kaika_workshop.commands%rowtype; result jsonb;
begin
 select workspace_id into w from kaika_workshop.capabilities where token_hash=p_hash and not revoked and expires_at>now();
 if w is null then raise sqlstate 'PT401' using message='Workshop connection expired or not authorized';end if;
 a=(p_data->>'leader_id')::uuid;
 if not exists(select 1 from kaika_workshop.people where workspace_id=w and id=a and coalesce((payload->>'source_active')::boolean,true)) then raise sqlstate 'PT403' using message='Unknown active persona';end if;
 if p_action='photos' then
  if jsonb_array_length(p_data->'person_ids')>24 then raise sqlstate 'PT400' using message='Too many profile images';end if;
  -- The recursive scope protects the private thumbnail lookup independently of UI filtering.
  if exists(with recursive scope(id) as (select a union select p.id from kaika_workshop.people p join scope s on (p.payload->>'manager_id')::uuid=s.id where p.workspace_id=w and coalesce((p.payload->>'source_active')::boolean,true)) select 1 from jsonb_array_elements_text(p_data->'person_ids') i where i::uuid not in(select id from scope)) then raise sqlstate 'PT403' using message='Profile is outside this leader scope';end if;
  return (select coalesce(jsonb_agg(jsonb_build_object('person_id',person_id,'revision',revision,'photo_data_url',photo_data_url)),'[]') from kaika_workshop.profiles where workspace_id=w and person_id in(select value::uuid from jsonb_array_elements_text(p_data->'person_ids')));
 elsif p_action='save' then
  pid=(p_data->>'person_id')::uuid;
  if pid is distinct from a then raise sqlstate 'PT403' using message='You can only customize your own profile';end if;
  perform 1 from kaika_workshop.workspaces where id=w for update;
  select * into prior from kaika_workshop.commands where workspace_id=w and mutation_id=(p_data->>'mutation_id')::uuid;
  if found then
   if prior.leader_id<>a or prior.request_hash<>p_data->>'request_hash' then raise sqlstate 'PT409' using message='Mutation identifier reused';end if;
   return prior.result;
  end if;
  select revision into rev from kaika_workshop.profiles where workspace_id=w and person_id=a;
  if coalesce(rev,0) is distinct from (p_data->>'expected_revision')::integer then raise sqlstate 'PT409' using message='Your profile changed. Reopen the editor before saving.';end if;
  insert into kaika_workshop.profiles(workspace_id,person_id,avatar_style,photo_data_url,revision)
   values(w,a,(p_data->>'avatar_style')::integer,p_data->>'photo_data_url',coalesce(rev,0)+1)
   on conflict(workspace_id,person_id) do update set avatar_style=excluded.avatar_style,photo_data_url=excluded.photo_data_url,revision=excluded.revision,updated_at=now();
  result=jsonb_build_object('person_id',a,'revision',coalesce(rev,0)+1);
  insert into kaika_workshop.commands(workspace_id,mutation_id,leader_id,request_hash,result) values(w,(p_data->>'mutation_id')::uuid,a,p_data->>'request_hash',result);
  return result;
 end if;
 raise exception 'Unsupported profile operation';
end $$;
revoke all on function public.kaika_workshop_profile(text,text,jsonb) from public,anon,authenticated;
grant execute on function public.kaika_workshop_profile(text,text,jsonb) to service_role;
-- Include only lightweight metadata in normal loads. Images are requested in scoped batches.
do $$ declare def text; begin
 def=pg_get_functiondef('public.kaika_workshop_store(text,text,jsonb)'::regprocedure);
 if position('''profiles''' in def)=0 then
  if position('''people'',(select' in def)=0 then raise exception 'Unexpected store definition';end if;
  def=replace(def,'''people'',(select','''profiles'',(select coalesce(jsonb_agg(jsonb_build_object(''person_id'',person_id,''avatar_style'',avatar_style,''profile_revision'',revision,''has_photo'',photo_data_url is not null)),''[]'') from kaika_workshop.profiles where workspace_id=w),''people'',(select');
  execute def;
 end if;
end $$;
