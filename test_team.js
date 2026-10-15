const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const state={month:'2026-10',peopleFilters:{scope:'all',signal:'all',search:''}};
const people=[{id:'one',name:'One Person',title:'Lead',team:'Data',manager_id:'boss'},{id:'two',name:'Two Person',title:'Engineer',team:'Data',manager_id:'one'}];
const gs=[{id:'g1',active_version_id:'v1'},{id:'g2',active_version_id:'v2'},{id:'g3',active_version_id:null}];
const vs={g1:{owner_id:'one',title:'Quality'},g2:{owner_id:'two',title:'Tool'},g3:{owner_id:'two',title:'Draft'}};
const shared={id:'d1',owner_id:'one',health:'blocked'};
let allocations=[{worker_id:'one',month:'2026-10-01',allocation_pct:60},{worker_id:'one',month:'2026-10-01',allocation_pct:50},{worker_id:'one',month:'2026-11-01',allocation_pct:80}];
const ctx={data:{people},leader:'boss',ls:()=>state,goals:()=>gs,gv:g=>vs[g.id],activeAllocations:()=>allocations,activeDeliveries:()=>[shared],overviewDeliveryRisk:d=>d.health==='blocked',needsAttention:g=>g.id==='g1'||g.id==='g3',team:()=>'',act:()=>{},document:{addEventListener(){}},console};vm.createContext(ctx);vm.runInContext(fs.readFileSync(__dirname+'/team_ui.js','utf8'),ctx);
let m=ctx.teamPersonModel(people[0]);assert.equal(m.deliveries.length,1,'Same leaf returned through several ancestors counts once');assert.equal(m.workload,110,'Only selected month allocation totals');assert.equal(m.risks.length,1);assert.equal(m.goalRisks.length,1);assert.equal(m.attention,true);
m=ctx.teamPersonModel(people[1]);assert.equal(m.workload,null,'No allocation is unknown, not zero capacity');assert.equal(m.goalRisks.length,0,'Unapproved draft is not a delivery-risk claim');
allocations=[{worker_id:'two',month:'2026-10-01',allocation_pct:0}];assert.equal(ctx.teamPersonModel(people[1]).workload,0,'Explicit zero remains distinct from missing');
state.peopleFilters.scope='direct';assert.equal(ctx.teamPeopleModels().length,1);state.peopleFilters.scope='all';state.peopleFilters.search='Tool';assert.equal(ctx.teamPeopleModels()[0].person.id,'two');state.peopleFilters.search='';state.peopleFilters.signal='attention';assert.equal(ctx.teamPeopleModels().length,1);
console.log('PASS: unique assigned deliverables, selected-month workload, missing vs zero, approved risk counts, direct-report/search/attention filters.');

const h=ctx.teamHierarchy(people.map(ctx.teamPersonModel),'one');assert.deepEqual(Array.from(h.ordered,x=>[x.model.person.id,x.depth]),[['one',0],['two',1]]);assert.equal(h.unlinked.length,0);ctx.leader='one';state.peopleFilters={scope:'all',signal:'all',search:''};assert.equal(ctx.teamPeopleModels()[0].person.id,'one','Current user precedes attention sorting');const broken=ctx.teamHierarchy([{person:{id:'a',name:'A',manager_id:'b'}},{person:{id:'b',name:'B',manager_id:'a'}}],'a');assert.equal(broken.ordered.length,2,'Malformed cycle cannot repeat people');console.log('PASS: self first, manager-before-report traversal, depth and cycle protection.');
