"""Outcome attainment is measured change, never inferred from delivered work."""
import math, datetime

def outcome(x,g,as_of):
 measures=[m for m in x['measures'] if m['version_id']==g['active_version_id']]
 version=next((v for v in x['versions'] if v['id']==g['active_version_id']),{})
 if version.get('success_basis','outcome')=='delivery':return dict(goal_id=g['id'],outcome_pct=None,measurement_state='not_applicable',details=[],target_met=False)
 days={'daily':1,'weekly':7,'monthly':31}.get(version.get('cadence'),7)
 details=[]
 for m in measures:
  readings=sorted([r for r in x['readings'] if r['measure_id']==m['id'] and r['observed_at'][:10]<=as_of],key=lambda r:(r['observed_at'],r.get('recorded_at',r['observed_at'])))
  r=readings[-1] if readings else None
  b,t=float(m['baseline']),float(m['target']);valid=(t>b if m.get('direction')=='increase' else t<b if m.get('direction')=='decrease' else False)
  raw=100*(float(r['value'])-b)/(t-b) if r and valid else None
  stale=bool(r and (datetime.date.fromisoformat(as_of)-datetime.date.fromisoformat(r['observed_at'][:10])).days>days)
  details.append(dict(measure_id=m['id'],title=m['title'],baseline=b,target=t,value=float(r['value']) if r else None,unit=m['unit'],weight=m['weight'],raw_pct=raw,attainment_pct=max(0,min(100,raw)) if raw is not None else None,observed_at=r['observed_at'] if r else None,evidence_note=r.get('evidence_note') if r else None,state='invalid' if not valid else 'not_measured' if not r else 'stale' if stale else 'current'))
 valid_weights=bool(measures) and all(float(m['weight'])>0 for m in measures) and abs(sum(float(m['weight']) for m in measures)-100)<0.001
 complete=valid_weights and all(d['attainment_pct'] is not None for d in details)
 pct=round(sum(d['attainment_pct']*float(d['weight'])/100 for d in details),2) if complete else None
 if complete and pct==100 and any(d['raw_pct']<100 for d in details):pct=99.99
 fresh=complete and all(d['state']=='current' for d in details)
 state='not_measured' if not details or any(d['state']=='not_measured' for d in details) else 'invalid' if not complete else 'stale' if not fresh else 'target_met' if pct==100 else 'below_baseline' if any(d['raw_pct']<0 for d in details) else 'no_improvement' if pct==0 else 'improving'
 return dict(goal_id=g['id'],outcome_pct=pct,measurement_state=state,details=details,target_met=bool(fresh and all(d['raw_pct']>=100 for d in details)))

def record_reading(f,leader,p,g):
 from demo_mutations import require
 from fixture_server import now
 import uuid
 v=next((v for v in f.db['versions'] if v['id']==g['active_version_id']),None)
 require(v is not None and v['owner_id']==leader,'Only the approved goal owner can record an observation.',403)
 require(v.get('success_basis','outcome')=='outcome','Delivery-based goals complete through accepted checkpoints; outcome readings do not apply.')
 m=next((m for m in f.db['measures'] if m['id']==p.get('measure_id') and m['version_id']==v['id']),None)
 require(m is not None,'Measure must belong to the active goal version.')
 try:value=float(p['value'])
 except (KeyError,ValueError,TypeError):value=float('nan')
 require(math.isfinite(value),'Enter a finite observed value.')
 require(m['unit']!='%' or 0<=value<=100,'Percentage observations must be between 0 and 100.')
 require(len(str(p.get('evidence_note','')).strip())>=20,'Describe the measurement source, population and result (at least 20 characters).')
 date=p.get('observed_on') or f.as_of
 try:datetime.date.fromisoformat(date)
 except (ValueError,TypeError):require(False,'Enter a valid observation date.')
 require(v['starts_on']<=date<=f.as_of,'Observation must be within the goal period and not in the future.')
 f.db['readings'].append(dict(id=str(uuid.uuid4()),measure_id=m['id'],value=value,evidence_note=p['evidence_note'].strip(),observed_at=date+'T12:00:00Z',recorded_at=now(),recorded_by=leader))
