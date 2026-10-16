const fs=require('fs'),vm=require('vm'),assert=require('node:assert/strict');
const ctx={console,Date,Intl,Map,act:()=>{},document:{addEventListener(){}}};vm.createContext(ctx);vm.runInContext(fs.readFileSync('summary_quarters.js','utf8'),ctx);
const q=ctx.captureQuarter('2026-03-31T16:00:00Z');assert.equal(ctx.quarterLabel(q),'Q2 2026');
const series=[{id:'old',saved:true,captured:'2026-01-01T01:00:00Z',model:{score:20}},{id:'new',saved:true,captured:'2026-03-30T01:00:00Z',model:{score:80}},{id:'q3',saved:true,captured:'2026-07-02T01:00:00Z',model:{score:50}},{id:'current',saved:false,model:{score:72}}];
const points=ctx.quarterlySeries(series,'2026-10-16T01:00:00Z',4);assert.equal(points.length,4);assert.equal(points[0].saved.id,'new');assert.equal(points[0].saved.model.score,80);assert.equal(points[1].saved,null);assert.equal(points[3].saved,null);assert.equal(points[3].live.id,'current');assert.equal(series[0].model.score,20);
const empty=ctx.quarterlySeries([series[3]],'2026-10-16T01:00:00Z',4);assert.equal(empty.filter(p=>p.saved).length,0);assert.equal(ctx.captureQuarter('invalid'),null);
console.log('PASS quarterly capture boundary, latest capture not averaging, missing-quarter gaps, live separation, no historical fabrication.');
