"""Synthetic workshop scenarios only. Never imported by the live gateway."""
import datetime,uuid,hashlib
AS_OF='2026-10-27'
PRESETS={'strategy':'Strategy workshop · complete hierarchy','delivery_walkthrough':'Delivery-based walkthrough','walkthrough':'Editable walkthrough','mixed':'Complete data · mixed statuses','partial':'Partially filled plans','empty':'Empty workspace','finished':'All work completed'}
def seed(f,preset):
 from fixture_server import uid
 if preset not in PRESETS:raise ValueError('Unknown scenario')
 f.people=[p for p in f.people if p['id'] in {uid(k) for k in ['ada','bea','ana','dan','sam']}]
 f.scenario=preset;f.as_of=AS_OF
 f.db={k:[] for k in f.db};f.files={};f.done={}
 if preset=='strategy':
  from strategy_workshop import seed as seed_strategy
  seed_strategy(f);return
 if preset=='empty':return
 def goal(key,title,state,delivery_states,owner='ada'):
  g=f.new_goal(uid(owner),title,'department' if owner in ['ada','dan'] else 'team',None);v=f.db['versions'][-1]
  g['id']=uid(preset+'-'+key);v['goal_id']=g['id'];v['id']=uid(preset+'-'+key+'-v1')
  v['pillar']='Data trust' if key in ['quality','complete','risk','overdue','walkthrough'] else 'Delivery enablement'
  v.update(description='Workshop scenario: '+title+'. The owner agrees the scope, measurement source, resources and acceptance evidence before delivery.',starts_on='2026-10-01',ends_on='2026-11-30',state='draft' if state=='draft' else 'submitted')
  if state in ['approved','returned']:
   f.db['approvals'].append(dict(id=uid(key+'-approval'),version_id=v['id'],decision=state,reason='Synthetic planning review: '+('baseline accepted' if state=='approved' else 'Specify an independent source and complete the effort estimate.'),approver_id=v['approver_id'],decided_at='2026-10-26T09:00:00Z'))
  if state=='approved':g['active_version_id']=v['id']
  m=dict(id=uid(preset+key+'metric'),version_id=v['id'],title='Quality validation pass rate',unit='%',direction='increase',baseline=60,target=95,weight=100,source_definition='Weekly independent quality audit across 20 agreed datasets.')
  f.db['measures'].append(m)
  for i,ds in enumerate(delivery_states):
   d=dict(id=uid(preset+key+'d'+str(i)),version_id=v['id'],title={'complete':'Publish the accepted validation report','in_progress':'Implement the monitoring rules','blocked':'Connect the restricted source feed','at_risk':'Validate the exception coverage','overdue':'Resolve the expired acceptance findings','not_started':'Roll out the agreed playbook','awaiting_review':'Submit the monitoring evidence package','unknown':'Confirm source ownership and delivery scope','draft':'Define the monitoring work package'}[ds],owner_id=uid(owner),due_on='2026-10-23' if ds=='overdue' else '2026-11-20',starts_on='2026-11-02' if ds=='not_started' else '2026-10-01',definition_of_done='Independent reviewer verifies all 20 checks, reconciles exceptions and accepts the attached evidence.',effort_days=[3,5][i%2],demo_signal=ds)
   f.db['deliverables'].append(d)
   for j,w in enumerate([40,60]):
    c=dict(id=uid(d['id']+str(j)),deliverable_id=d['id'],title=['Validation design accepted','Final results accepted'][j],weight=w,due_on=d['due_on'],acceptance_criteria='Verify the documented checks, expected results and exception register.',reviewer_id=v['approver_id'])
    f.db['checkpoints'].append(c)
    accepted=state=='approved' and (ds=='complete' or ds in ['in_progress','at_risk','blocked','overdue'] and j==0)
    if accepted or ds=='awaiting_review':
     eid=uid(c['id']+'evidence');content=('SYNTHETIC WORKSHOP EVIDENCE\n'+title+'\n'+d['title']+'\n'+c['title']+'\n20 checks documented. This file demonstrates the review flow only.\n').encode()
     f.files[eid]=content
     f.db['evidence'].append(dict(id=eid,deliverable_id=d['id'],checkpoint_id=c['id'],original_name='validation-'+str(i+1)+'-'+str(j+1)+'.txt',mime_type='text/plain',byte_size=len(content),sha256=hashlib.sha256(content).hexdigest(),scan_state='pending',upload_state='complete',created_at='2026-10-26T08:00:00Z',uploaded_by=uid(owner)))
     if accepted:f.db['acceptances'].append(dict(id=uid(c['id']+'accept'),checkpoint_id=c['id'],deliverable_id=d['id'],evidence_id=eid,accepted=True,reviewer_id=v['approver_id'],reason='Synthetic evidence manually reviewed against agreed criteria.',file_safety_acknowledged=True,decided_at='2026-10-26T09:00:00Z'))
  if state=='approved' and 'unknown' not in delivery_states:
   val=95 if all(s=='complete' for s in delivery_states) else 60 if all(s=='not_started' for s in delivery_states) else 75
   f.db['readings'].append(dict(id=uid(key+'reading'),measure_id=m['id'],value=val,observed_at='2026-10-26T10:00:00Z',evidence_note='Synthetic audit observation, 20 agreed datasets.'))
   risk='blocked' if 'blocked' in delivery_states else 'at_risk' if any(s in ['at_risk','overdue'] for s in delivery_states) else 'on_track'
   reason={'blocked':'Source access is blocked. A decision from the system owner is needed.','at_risk':'The exception coverage or due checkpoint needs attention. See the delivery rows below.','on_track':'Latest checkpoint evidence reviewed; remaining work is scheduled.'}[risk]
   if all(s=='not_started' for s in delivery_states):reason='Baseline approved. Delivery starts on 2 November; no acceptance credit yet.'
   if all(s=='awaiting_review' for s in delivery_states):reason='Evidence submitted. The designated reviewer has not accepted the checkpoints yet.'
   if all(s=='complete' for s in delivery_states):reason='All deliverables accepted and the outcome target reached.'
   f.db['checkins'].append(dict(id=uid(key+'checkin'),goal_id=g['id'],author_id=uid(owner),health=risk,reason=reason,eta=v['ends_on'],created_at='2026-10-26T10:00:00Z',source='seed'))
  if key in ['quality','complete','progress']:
   kid=uid(preset+key+'kpi');f.db['kpis'].append(dict(id=kid,version_id=v['id'],title='Audit processing cost per run',unit='USD',direction='below',target=200,source='Synthetic finance cost report; fixed audit scope.'))
   f.db['kpi_readings'].append(dict(id=uid(kid+'r'),kpi_id=kid,value=185 if key!='progress' else 215,observed_at='2026-10-26T12:00:00Z',evidence_note='Synthetic report COST-026.'))
  f.db['allocations'].append(dict(id=uid(key+'allocation'),version_id=v['id'],worker_id=uid(owner),month='2026-10-01',allocation_pct=5))
  return g,v
 if preset in ['walkthrough','delivery_walkthrough']:
  g,v=goal('walkthrough','Improve dataset quality from 60% to 95%','approved',['in_progress','in_progress'],'bea')
  f.db['evidence']=[];f.db['acceptances']=[];f.files={}
  f.db['deliverables'][0]['title']='Agree the validation design'
  f.db['deliverables'][1]['title']='Deliver the monitoring implementation'
  f.db['readings']=[]
  f.db['checkins']=[]
  for d in f.db['deliverables']:
   d['definition_of_done']='Reviewer verifies the agreed design or implemented monitoring functionality against its test cases. This acceptance does not certify the weekly dataset quality outcome.'
  for c in f.db['checkpoints']:
   c['acceptance_criteria']='Verify the design or implementation test evidence and resolve functional defects. Record dataset quality results separately in Success measures.'
  if preset=='delivery_walkthrough':
   v.update(success_basis='delivery',title='Launch the approved monitoring service')
   f.db['measures']=[]
  v['description']='Improve the weekly quality audit from 12 of 20 datasets passing (60%) to 19 of 20 (95%). Deliver the validation design and monitoring implementation, then measure whether quality actually improves. Delivery acceptance alone does not establish the result.'
  if preset=='delivery_walkthrough':v['description']='Success is delivering an accepted validation design and working monitoring service. All agreed functional checkpoints need evidence and independent acceptance. No KPI improvement is required for this goal.'
 elif preset=='partial':
  g,v=goal('draft','Define the customer data baseline','draft',['draft'])
  v['description']='';f.db['measures']=[];f.db['allocations']=[]
  f.db['deliverables'][0].update(effort_days=None,definition_of_done='')
  f.db['checkpoints']=[]
  goal('unknown','Confirm ownership of data quality','approved',['unknown'],owner='bea')
 elif preset=='finished':
  for k,t,o in [('quality','Improve quality validation to 95%','ada'),('monitor','Launch the monitoring service','bea'),('adoption','Complete the team enablement','ada')]:goal(k,t,'approved',['complete','complete'],o)
 else:
  rows=[
   ('complete','Improve quality validation to 95%','approved',['complete','complete'],'ada'),
   ('progress','Launch the monitoring service','approved',['complete','in_progress'],'bea'),
   ('risk','Expand validation coverage','approved',['at_risk','in_progress'],'ada'),
   ('blocked','Connect finance data securely','approved',['complete','blocked'],'ada'),
   ('overdue','Close the audit findings','approved',['overdue','in_progress'],'bea'),
   ('planned','Roll out the quality playbook','approved',['not_started','not_started'],'ada'),
   ('review','Publish the monitoring evidence','approved',['awaiting_review','awaiting_review'],'bea'),
   ('unknown','Establish source accountability','approved',['unknown'],'ada'),
   ('draft','Reduce recurring support effort','draft',['draft'],'ada'),
   ('submitted','Agree the next quarter roadmap','submitted',['draft','draft'],'bea'),
   ('returned','Define the adoption baseline','returned',['draft'],'bea')]
  for args in rows:goal(*args)
 # A peer director's records remain excluded from Ada's view.
 goal('peer','Improve customer onboarding','approved',['in_progress','not_started'],'dan')
 visible=[g for g in f.db['goals'] if next(v for v in f.db['versions'] if v['goal_id']==g['id'])['owner_id']!=uid('dan')]
 if preset!='partial':
  pid=uid(preset+'portfolio');f.db['portfolios'].append(dict(id=pid,title='Data quality programme',description='Workshop portfolio across Data & Analytics.',owner_id=uid('ada')))
  f.db['portfolio_goals']=[dict(portfolio_id=pid,goal_id=g['id']) for g in visible]
  gid=visible[0]['id']
  f.db['questions'].append(dict(id=uid('demo-question'),goal_id=gid,question='Who signs off the final validation scope?',asked_by=uid('ada'),assigned_to=uid('bea'),resolved_at='2026-10-26T10:00:00Z' if preset=='finished' else None))
  f.db['decisions'].append(dict(id=uid('demo-decision'),goal_id=gid,decision='Use 20 agreed datasets for the acceptance baseline.',rationale='Keep the outcome denominator consistent across teams.',decided_at='2026-10-26T09:00:00Z'))
  f.db['reviews'].append(dict(id=uid('demo-review'),facilitator_id=uid('ada'),title='27 October workshop review',published_at='2026-10-26T11:00:00Z',snapshot={'text':'Synthetic review snapshot. Validation baseline agreed; inspect current objective and deliverable status before making a new decision.'}))

def delivery_metric(x,d,as_of,active):
 cps=[c for c in x['checkpoints'] if c['deliverable_id']==d['id']]
 accepted=[]
 for c in cps:
  a=sorted([a for a in x['acceptances'] if a['checkpoint_id']==c['id']],key=lambda a:a['decided_at'])
  if a and a[-1]['accepted']:accepted.append(c)
 pct=sum(c['weight'] for c in accepted)
 overdue=sum(c['due_on']<as_of and c not in accepted for c in cps)
 signal=d.get('demo_signal','in_progress')
 if d['version_id'] not in active:h='draft';pct=None
 elif not cps or not d.get('effort_days'):h='unknown'
 elif pct==100:h='complete'
 elif signal=='unknown':h='unknown'
 elif signal=='blocked':h='blocked'
 elif overdue:h='overdue'
 elif signal=='at_risk':h='at_risk'
 elif any(any(e['deliverable_id']==d['id'] and e['upload_state']=='complete' and (not e['checkpoint_id'] or e['checkpoint_id']==c['id']) and not any(a['checkpoint_id']==c['id'] and a['evidence_id']==e['id'] for a in x['acceptances']) for e in x['evidence']) for c in cps if c not in accepted):h='awaiting_review'
 elif signal=='not_started':h='not_started'
 else:h='in_progress'
 if h=='unknown':pct=None
 return dict(deliverable_id=d['id'],accepted_pct=pct,overdue_checkpoints=overdue,calculated_health=h)

def derive(x,as_of):
 x['delivery_progress']=[];x['progress']=[];x['outcomes']=[]
 active={g['active_version_id'] for g in x['goals'] if g['active_version_id']}
 x['delivery_progress']=[delivery_metric(x,d,as_of,active) for d in x['deliverables']]
 for g in x['goals']:
  branch={g['id']}
  while True:
   expanded=branch|{child['id'] for child in x['goals'] if child['parent_id'] in branch}
   if expanded==branch:break
   branch=expanded
  branch_goals=[child for child in x['goals'] if child['id'] in branch]
  versions={child['active_version_id'] for child in branch_goals if child['active_version_id']}
  ds=[d for d in x['deliverables'] if d['version_id'] in versions]
  ps=[p for p in x['delivery_progress'] if p['deliverable_id'] in {d['id'] for d in ds}]
  total=sum(d.get('effort_days') or 0 for d in ds)
  pct=round(sum((d.get('effort_days') or 0)*(next(p['accepted_pct'] for p in ps if p['deliverable_id']==d['id']) or 0) for d in ds)/total,2) if total else None
  states={p['calculated_health'] for p in ps}
  h='unknown' if not ds or 'unknown' in states else 'complete' if states=={'complete'} else 'blocked' if 'blocked' in states else 'at_risk' if states&{'overdue','at_risk'} else 'not_started' if states=={'not_started'} else 'awaiting_review' if states=={'awaiting_review'} else 'on_track'
  if any(not child['active_version_id'] for child in branch_goals):h='unknown'
  manual=next((c for c in sorted(x['checkins'],key=lambda c:c['created_at'],reverse=True) if c['goal_id']==g['id'] and c.get('source')!='seed'),None)
  if h!='complete' and manual and manual['health'] in ['blocked','at_risk']:h=manual['health'] if h!='blocked' else h
  if h=='unknown':pct=None
  causes=[d['title']+(': '+d['status_reason'] if d.get('status_reason') else '') for d in ds if next(p['calculated_health'] for p in ps if p['deliverable_id']==d['id']) in ['blocked','at_risk','overdue','unknown','awaiting_review']]
  reason='All delivery checkpoints accepted.' if h=='complete' else '; '.join(causes) if causes else 'Delivery status and progress are recalculated from the current checkpoints.'
  x['progress'].append(dict(root_id=g['id'],delivery_pct=pct,calculated_health=h,reason=reason,effort_days=total))
  from outcome_metrics import outcome
  o=outcome(x,g,as_of);x['outcomes'].append(o)
  version=next((v for v in x['versions'] if v['id']==g['active_version_id']),{})
  delivery_based=version.get('success_basis','outcome')=='delivery'
  objective_state=('achieved' if h=='complete' else h) if delivery_based else 'achieved' if h=='complete' and o['target_met'] else 'outcome_pending' if h=='complete' else 'target_met_delivery_open' if o['target_met'] else h
  if version.get('success_basis')=='metric':
   objective_state='unknown' if not g.get('active_version_id') or o['measurement_state'] in ['not_measured','invalid'] else 'achieved' if o['target_met'] else 'at_risk' if o['measurement_state']=='stale' or version.get('ends_on','9999')<as_of else 'on_track'
   if objective_state!='achieved' and manual and manual['health'] in ['blocked','at_risk']:objective_state=manual['health']
   x['progress'][-1]['calculated_health']=objective_state
   x['progress'][-1]['reason']='Current approved metric targets are met.' if o['target_met'] else 'A current observation is required.' if o['measurement_state'] in ['not_measured','stale','invalid'] else 'Measured improvement has not yet reached the approved target.'
  x['progress'][-1]['objective_state']=objective_state
  if objective_state=='outcome_pending':x['progress'][-1]['reason']='Delivery accepted; '+('outcome has not been measured.' if o['outcome_pct'] is None else 'refresh the overdue outcome observation.' if o['measurement_state']=='stale' else 'the measured outcome is still below target. Review the remaining gap.')
  elif objective_state=='achieved' and version.get('success_basis')!='metric':x['progress'][-1]['reason']='All agreed deliverables accepted. This delivery-based goal has achieved its approved success criteria.' if delivery_based else 'All delivery checkpoints accepted and current outcome observations meet the approved targets.'
  x['progress'][-1]['success_basis']=version.get('success_basis','outcome')
 return x


def upgrade_walkthrough(f):
 """Repair only the old synthetic walkthrough definition; retain user decisions and observations."""
 if f.scenario!='walkthrough':return
 from fixture_server import uid
 v=next((v for v in f.db['versions'] if v['goal_id']==uid('walkthrough-walkthrough') and v['title']=='Launch the monitoring service'),None)
 if not v:return
 v['title']='Improve dataset quality from 60% to 95%'
 v['description']='Improve the weekly quality audit from 12 of 20 datasets passing (60%) to 19 of 20 (95%). Accepted design and monitoring implementation are delivery milestones; repeat the audit to establish the outcome.'
 seed_id=uid('walkthroughreading')
 f.db['readings']=[r for r in f.db['readings'] if not (r['id']==seed_id and r.get('evidence_note')=='Synthetic audit observation, 20 agreed datasets.')]
 for d in f.db['deliverables']:
  if d['version_id']==v['id']:d['definition_of_done']='Reviewer verifies the agreed design or implemented monitoring functionality against its test cases. Record weekly dataset quality observations separately.'
