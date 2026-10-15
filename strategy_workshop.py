"""Invented but internally consistent strategy workshop. No Workday records."""
import hashlib

def people(f):
 from fixture_server import uid
 additions=[('iris','Iris Lim','Data Engineer','bea','Data & Analytics','data'),('niko','Niko Ramos','BI Lead','ada','Data & Analytics','data'),('lina','Lina Garcia','BI Analyst','niko','Data & Analytics','data'),('leo','Leo Mendoza','Customer Operations Lead','dan','Customer Experience','customer'),('mia','Mia Flores','Customer Operations Specialist','leo','Customer Experience','customer')]
 for key,name,title,manager,team,org in additions:
  if any(p['id']==uid(key) for p in f.people):continue
  f.people.append(dict(id=uid(key),name=name,title=title,manager_id=uid(manager),team=team,org_id=uid(org),worker_type='Employee',source_fte=1,site_weekly_hours=40,capacity_verified=False,observed_at='2026-10-01',synthetic=True))

def seed(f):
 from fixture_server import uid
 people(f)
 f.db['strategies']=[dict(id=uid('strategy-2028'),title='Trusted decisions. Simpler work. Better customer experiences.',description='By 2028, make reliable data and efficient services a daily advantage for every team and customer.',period='2026–2028',synthetic=True)]
 pillars=[('trust','Trusted enterprise data','Make critical data reliable, explainable and owned.'),('efficiency','Productive teams and simpler work','Give time back to teams through repeatable, automated reporting.'),('customer','Customer confidence','Make onboarding predictable and easy for customers.')]
 f.db['pillars']=[dict(id=uid('pillar-'+k),strategy_id=uid('strategy-2028'),title=t,description=d,synthetic=True) for k,t,d in pillars]
 specs=[
 ('quality','Raise critical-data quality from 72% to 95%','ada',None,'trust',('Critical records passing validation','%',72,95,84,'Weekly audit of the same 1,000 critical customer and finance records.')),
 ('monitoring','Launch automated quality monitoring','bea','quality','trust',None),
 ('evidence','Publish reconciled validation evidence','ana','monitoring','trust',None),
 ('checks','Deploy checks for 12 priority datasets','iris','monitoring','trust',None),
 ('ownership','Establish accountable data ownership','ada','quality','trust',None),
 ('reporting','Reduce monthly reporting effort from 80 to 48 hours','ada',None,'efficiency',('Monthly effort for the eight leadership reports','hours',80,48,64,'Monthly time log for the same eight reports; excludes one-time development effort.')),
 ('automation','Automate the leadership reporting cycle','niko','reporting','efficiency',None),
 ('operating','Adopt the new reporting operating model','ada','reporting','efficiency',None),
 ('onboarding','Reduce customer onboarding from 10 to 6 days','dan',None,'customer',('Median onboarding lead time','days',10,6,8,'Last 30 completed standard onboardings; excludes enterprise custom integrations.')),
 ('handoffs','Simplify onboarding handoffs','leo','onboarding','customer',None),
 ('promise','Approve the onboarding service promise','dan','onboarding','customer',None)]
 versions={};goals={}
 for key,title,owner,parent,pillar,metric in specs:
  g=f.new_goal(uid(owner),title,'department' if not parent else 'team',goals[parent]['id'] if parent else None);v=f.db['versions'][-1]
  g.update(id=uid('strategy-'+key),hierarchy_model='workstream-delivery',node_kind='workstream' if parent else 'objective',origin='inherited' if parent else 'initiated',assignment_state='accepted' if parent else None);v.update(id=uid('strategy-'+key+'-v1'),goal_id=g['id'],state='submitted',success_basis='outcome' if metric else 'delivery',starts_on='2026-10-01',ends_on='2026-12-18',pillar=next(t for k,t,d in pillars if k==pillar),pillar_id=uid('pillar-'+pillar),priority='vital' if not parent else 'fuel',category='Customer intimacy' if pillar=='customer' else 'Efficiency' if pillar=='efficiency' else 'Capability',description={'quality':'Improve the accuracy and completeness of the agreed critical records. Monitoring implementation supports this outcome, but does not by itself prove data quality improved.','reporting':'Automate the eight recurring leadership reports and remove duplicate preparation. Preserve reconciled totals and independent sign-off.','onboarding':'Reduce avoidable handoffs for standard customer onboarding without increasing rework or missing compliance checks.'}.get(key,'Deliver the agreed workstream through the named team. Complete the evidence and acceptance conditions at the end of each branch.'))
  parent_owner=versions[parent]['owner_id'] if parent else None
  if parent_owner and parent_owner!=uid(owner):v['approver_id']=parent_owner;g.update(assigned_by=parent_owner,accepted_at='2026-10-02T09:00:00Z')
  v['approver_name']=next(p['name'] for p in f.people if p['id']==v['approver_id']);g['active_version_id']=v['id'];goals[key]=g;versions[key]=v
  f.db['approvals'].append(dict(id=uid(key+'-strategy-approval'),version_id=v['id'],decision='approved',approver_id=v['approver_id'],reason='Synthetic workshop baseline approved with named ownership, dates, measurement and acceptance criteria.',decided_at='2026-10-03T09:00:00Z'))
  if metric:
   title,unit,baseline,target,value,source=metric;mid=uid(key+'-strategy-measure')
   f.db['measures'].append(dict(id=mid,version_id=v['id'],title=title,unit=unit,direction='increase' if target>baseline else 'decrease',baseline=baseline,target=target,weight=100,source_definition=source))
   f.db['readings'].append(dict(id=uid(mid+'reading'),measure_id=mid,value=value,observed_at='2026-10-26T10:00:00Z',evidence_note='Synthetic workshop observation. '+source))
 deliveries=[
 ('evidence','Issue the baseline quality audit','ana',3,'complete','2026-10-16','Reconcile the agreed 1,000-record sample; document accuracy and completeness checks, exceptions and denominator.'),
 ('evidence','Publish the October exception register','ana',2,'awaiting_review','2026-10-30','List every failed rule, assigned remediation owner, severity and verified disposition; reviewer confirms no unassigned critical exception.'),
 ('checks','Deploy validation checks for 12 datasets','iris',8,'blocked','2026-11-13','Run 12 production-equivalent test suites; retain execution logs and evidence of restricted-source approval.'),
 ('ownership','Approve the critical-data owner register','ada',2,'complete','2026-10-16','Name one accountable owner and steward for each of the 12 datasets; all owners acknowledge their responsibility.'),
 ('ownership','Run the steward remediation workshop','bea',3,'not_started','2026-11-06','All 12 stewards practise triage using a sample incident and sign off the escalation guide.'),
 ('automation','Release the reconciled reporting pipeline','lina',6,'in_progress','2026-11-20','Reproduce all eight reports; reconcile totals to the approved source and log each transformation.'),
 ('automation','Complete the reporting handover','niko',2,'at_risk','2026-11-27','Run two supported cycles; document rollback, operating ownership and response times with signed handover.'),
 ('operating','Retire duplicate report preparation','ada',2,'not_started','2026-12-04','Eight report owners adopt the single agreed reporting workflow; obsolete schedules are disabled and archived.'),
 ('handoffs','Launch the onboarding checklist','mia',4,'complete','2026-10-16','Trial the checklist on ten synthetic customer cases; every handoff has a named owner and required information.'),
 ('handoffs','Validate the first 30 onboarding cases','leo',3,'in_progress','2026-11-20','Measure start-to-ready time and rework for 30 standard cases; all exception causes are classified.'),
 ('promise','Publish the six-day service commitment','dan',2,'not_started','2026-12-04','Service owners approve the standard-case definition, six-day promise and exception escalation before publication.')]
 for index,(key,title,owner,effort,signal,due,dod) in enumerate(deliveries):
  v=versions[key];did=uid('strategy-delivery-'+str(index));reviewer=v['approver_id'];assert reviewer!=uid(owner)
  d=dict(id=did,version_id=v['id'],title=title,owner_id=uid(owner),starts_on='2026-11-02' if signal=='not_started' else '2026-10-01',due_on=due,definition_of_done=dod,effort_days=effort,demo_signal=signal,status_reason='Restricted-source approval is still pending.' if signal=='blocked' else 'Handover depends on the final pipeline trial.' if signal=='at_risk' else '')
  f.db['deliverables'].append(d)
  for j,(weight,cp_title) in enumerate([(40,'Design and test scope accepted'),(60,'Final output and evidence accepted')]):
   cid=uid(did+'checkpoint'+str(j));criteria=('Reviewer verifies the agreed scope, examples and test design. ' if j==0 else 'Reviewer verifies final results against the definition of done. ')+dod
   f.db['checkpoints'].append(dict(id=cid,deliverable_id=did,title=cp_title,weight=weight,due_on=due,reviewer_id=reviewer,acceptance_criteria=criteria))
   accepted=signal=='complete' or signal in ['in_progress','blocked','at_risk'] and j==0
   if accepted or signal=='awaiting_review':
    eid=uid(cid+'file');blob=('SYNTHETIC WORKSHOP EVIDENCE\n'+title+'\n'+cp_title+'\n'+criteria+'\nSample only; no real customer or employee records.').encode();f.files[eid]=blob
    f.db['evidence'].append(dict(id=eid,deliverable_id=did,checkpoint_id=cid,original_name='workshop-evidence-'+str(index+1)+'-'+str(j+1)+'.txt',mime_type='text/plain',byte_size=len(blob),sha256=hashlib.sha256(blob).hexdigest(),upload_state='complete',scan_state='pending',created_at='2026-10-26T09:00:00Z',uploaded_by=uid(owner)))
    if accepted:f.db['acceptances'].append(dict(id=uid(cid+'acceptance'),deliverable_id=did,checkpoint_id=cid,evidence_id=eid,reviewer_id=reviewer,accepted=True,file_safety_acknowledged=True,reason='Synthetic independent review: evidence meets the agreed checkpoint criteria.',decided_at='2026-10-26T10:00:00Z'))
  for month in ['2026-10-01','2026-11-01']:
   # Person/month commitments are owned by the execution workstream, not copied to parents.
   if not any(a['version_id']==v['id'] and a['worker_id']==uid(owner) and a['month']==month for a in f.db['allocations']):f.db['allocations'].append(dict(id=uid(did+month+'allocation'),version_id=v['id'],worker_id=uid(owner),month=month,allocation_pct=20))
 kpis=[('quality','Critical datasets with an accountable steward','%',100,83,'above','Signed owner register across 12 datasets.'),('monitoring','Alert detection time','minutes',30,18,'below','Weekly synthetic alert test, median of 12 datasets.'),('reporting','Leadership reports delivered on time','%',95,88,'above','Eight-report schedule; on-time count divided by expected deliveries.'),('onboarding','Onboarding rework rate','%',5,4,'below','Reopened cases divided by the last 30 completed standard onboardings.')]
 for key,title,unit,target,value,direction,source in kpis:
  kid=uid('strategy-kpi-'+key);f.db['kpis'].append(dict(id=kid,version_id=versions[key]['id'],title=title,unit=unit,target=target,direction=direction,source=source));f.db['kpi_readings'].append(dict(id=uid(kid+'reading'),kpi_id=kid,value=value,observed_at='2026-10-26T11:00:00Z',evidence_note='Synthetic workshop measurement. '+source))
 for owner,title,keys in [('ada','Trusted data and productive reporting',['quality','reporting']),('dan','Customer onboarding transformation',['onboarding'])]:
  pid=uid('strategy-portfolio-'+owner);f.db['portfolios'].append(dict(id=pid,owner_id=uid(owner),title=title,description='Director portfolio of the accountable objectives. Supporting relationships do not add delivery weight.'));f.db['portfolio_goals'].extend(dict(portfolio_id=pid,goal_id=goals[k]['id']) for k in keys)
 f.db['questions'].append(dict(id=uid('strategy-question'),goal_id=goals['checks']['id'],question='When will restricted-source access be approved?',asked_by=uid('bea'),assigned_to=uid('iris'),resolved_at=None))
 f.db['decisions'].append(dict(id=uid('strategy-decision'),goal_id=goals['quality']['id'],decision='Hold the 1,000-record quality audit population constant.',rationale='Separate quality improvement from changes in the denominator.',decided_by=uid('ada'),decided_at='2026-10-26T09:00:00Z'))
 # An explicit shared request is stored inside the goal details, not a map node.
 import support_domain
 r=support_domain.handle(f,uid('ada'),'support_create',dict(goal_id=goals['quality']['id'],owner_id=uid('dan'),title='Confirm the customer-field definitions',context='Agree the meanings of customer start date, service-ready date and primary contact for the shared validation rules.',criteria='Provide an agreed definition and two synthetic examples for each of the three fields.',due_on='2026-11-06'))
 # Dan links the goal he owns, not a subordinate's private goal.
 support_domain.handle(f,uid('dan'),'support_accept',dict(id=r['id'],revision=0,text='Customer Operations accepts the scope and will share the six examples by 6 November.',delivery_goal_id=goals['onboarding']['id']))
