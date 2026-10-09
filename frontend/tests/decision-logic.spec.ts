import {test,expect} from '@playwright/test';
import {decisionRows,rankDecisions} from '../src/decisions';
function option(id:number,shortage:number,waste:number,work:number,upperWork=work,upperWaste=waste){return {alternative:id,name:'O'+id,metrics:{shortage:{mean:shortage,high:shortage},waste:{mean:waste,high:upperWaste},work:{mean:work,high:upperWork}}};}
test('Una mejora de continuidad que viola límites queda fuera',()=>{
 const rows=decisionRows([option(0,10,1,30),option(1,5,4,20),option(2,8,1.5,25)],2,35,true);
 expect(rankDecisions(rows.filter(r=>r.feasible))[0].alternative).toBe(2);
 expect(rows[1].feasible).toBe(false);expect(rows[1].violations).toContain('Supera desperdicio');
});
test('Empates numéricos permiten elegir el compromiso entre pérdida y trabajo',()=>{
 const rows=decisionRows([option(0,10,1,30),option(1,10+1e-12,.5,40)],2,50,true);
 expect(rankDecisions(rows,'work')[0].alternative).toBe(0);
 expect(rankDecisions(rows,'waste')[0].alternative).toBe(1);
});
test('El filtro conservador requiere el rango y rechaza sobrecarga',()=>{
 const missing=option(2,2,.5,10);missing.metrics.work.high=null as any;
 const rows=decisionRows([option(0,10,1,30,45),option(1,5,1,25,30),missing],2,35,true);
 expect(rows[0].feasible).toBe(false);expect(rows[1].feasible).toBe(true);expect(rows[2].feasible).toBe(false);
 expect(decisionRows([missing],2,35,false)[0].feasible).toBe(true);
});
