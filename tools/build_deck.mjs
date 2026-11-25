// Optional Codex runtime rebuild. Set RUNTIME_NODE_MODULES, PRESENTATION_SKILL_DIR and RUNTIME_PYTHON; make @oai/artifact-tool available through node_modules.
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';
const skillDir=process.env.PRESENTATION_SKILL_DIR;
if(!skillDir)throw new Error('Set PRESENTATION_SKILL_DIR to the installed presentation skill');
const {finalizePresentation,applyPresentationChartFont}=await import(path.join(skillDir,'container_tools/artifact_tool_utils.mjs'));
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const data=JSON.parse(await fs.readFile(path.join(root,'outputs/tables/deck_data.json'),'utf8'));
const p=Presentation.create({slideSize:{width:1280,height:720}});
const blue='#0072B2',navy='#173753',orange='#D55E00',muted='#4B5A68';
const specs=[];
function text(s,x,y,w,h,value,size=28,color=navy,bold=false){
 const a=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=value;a.text.style={typeface:'Arial',fontSize:size,color,bold};return a;
}
function slide(title,seconds,presenter,notes){
 const s=p.slides.add();s.background.fill='#FFFFFF';text(s,60,34,1160,76,title,42,navy,true);
 text(s,60,668,1040,28,'SEEM3410  |  Synthetic outpatient clinic  |  '+presenter,18,muted);text(s,1180,668,50,28,String(p.slides.items.length),18,muted);
 s.speakerNotes.text=`Presenter: ${presenter}. Planned time: ${seconds} seconds.\n${notes}\nSources: supplied hospital proposal; SEEM3410 Week 1–6 notes; executed CSVs in outputs/tables and outputs/experiments. Dataset link: https://www.kaggle.com/datasets/juneminazuki/hospital-queue-and-patient-flow-simulation`;
 specs.push({title,seconds,presenter,notes});return s;
}
function table(s,rows,x,y,w,h,colWidths){
 const t=s.tables.add({rows:rows.length,columns:rows[0].length,left:x,top:y,width:w,height:h,columnWidths:colWidths,values:rows});
 for(let i=0;i<rows.length;i++)for(let j=0;j<rows[0].length;j++){
   const c=t.getCell(i,j);c.text.style={typeface:'Arial',fontSize:23,color:navy,bold:i===0};c.fill=i===0?'#EAF2F7':'#FFFFFF';
 }
 return t;
}
function chart(s,categories,series,x,y,w,h,ytitle){
 const c=s.charts.add('line',{position:{left:x,top:y,width:w,height:h},categories,series,lineOptions:{smooth:false},hasLegend:series.length>1,
 xAxis:{title:{text:'Doctors',textStyle:{fontSize:22}},textStyle:{fontSize:20},numberFormatCode:'0'},yAxis:{title:{text:ytitle,textStyle:{fontSize:22}},textStyle:{fontSize:20},numberFormatCode:'0',min:0},legend:{position:'bottom',textStyle:{fontSize:20}},chartFill:'#FFFFFF'});
 applyPresentationChartFont(c,{fontFamily:'Arial'});return c;
}
let s=slide('Doctor staffing in an outpatient clinic',60,'Lai Sin Hang','State the question and the finite synthetic scope. The primary metric averages within-run P90s, each over all 200 patients. The illustrative target is 15 minutes. The baseline is two doctors; compare three and four. Do not present these as actual hospital days.');
text(s,60,170,1140,125,'Which staffing level meets a 15-minute\ndoctor-wait target at the lowest cost?',47,navy,true);
text(s,60,345,1120,125,'2, 3 or 4 doctors\nPrimary measure: mean of run-level P90 waits',32,blue);
text(s,60,540,1100,65,data.team.map(x=>`${x[0]}  ${x[1]}`).join('   |   '),25,muted);
s=slide('Synthetic data and input calibration',90,'Lai Sin Hang','Explain 60,000 records: six scenarios, 50 runs and 200 patients. Only baseline inputs calibrate fresh generation; all scenarios verify source reconstruction. Estimate empirical PMFs because supports are small. Previous-clock gap conditioning is an assumption. The fitted two Poisson rates approximate time variation, but not the discrete variability. Fixed-200 truncation affects late exposure.');
text(s,60,130,1150,58,'60,000 records  •  6 scenarios  •  50 runs × 200 patients',31,blue,true);
table(s,[['Input','Empirical model / fitted mean'],['Arrivals','Two gap PMFs; previous clock ≤240 / later'],...data.input_table.slice(2,5).map(r=>[r[0],r[1]])],60,210,1150,330,[250,900]);
text(s,60,575,1120,65,'Estimated inputs are synthetic; target, wages and schedule are assumptions',25,muted);
s=slide('Model flow and event logic',80,'Lai Sin Hang','Walk through the two stages. Priority 3 is highest and consultations cannot be interrupted. Doctor FEL uses time/event rank/sequence and the waiting heap uses clinical class/arrival/ID. Pharmacy is a separate exact availability calendar because there is no blocking feedback. Terminate after every patient departs, not after 240 minutes.');
text(s,60,145,1140,105,'Arrival → priority doctor queue → consultation\n→ FCFS pharmacy → departure',35,blue,true);
text(s,60,305,1110,210,'Priority: 3 > 2 > 1; FCFS within class\nConsultations are non-preemptive\nEmpty start; exactly 200 patients; drain all queues\n240 minutes is the peak boundary',31);
text(s,60,565,1110,58,'Doctor FEL + independent downstream availability calendar',26,muted);
s=slide('Model verification',70,'Lai Sin Hang',`The hand trace produces A,C,D,B consultation order, with departures 15,22,17,19. All 60,000 source records replay exactly for both waits and total time. Explain why this is compatibility with synthetic data, not actual hospital validation. The automated suite currently records ${data.test_count} tests; run invariants check every experiment. The numerical clock resolution prevents fractional arithmetic from changing intended ties.`);
table(s,data.verification.map((r,i)=>i===3?['Hospital sojourn',...r.slice(1)]:r),60,145,1150,250,[410,200,270,270]);
text(s,60,440,1120,100,`${data.test_count} automated tests + invariants in every executed run\nHand trace, queue order, capacity, conservation and drain`,30,blue,true);
text(s,60,575,1110,60,'Exact replay verifies source compatibility; clinical validation remains open',26,muted);
s=slide('Matched experiments and uncertainty',70,'Lee Ka Tung','Explain SeedSequence root3410 and four independent mechanism streams. Reuse the exact input table across staffing policies, with matching hashes. Across replications, inputs are independent. Fresh root93410 confirms separately. CI uses 50 run-level values, not 10,000 independent patients. Paired difference is new-reference; negative reduces waits. These CIs quantify Monte Carlo uncertainty conditional on calibrated inputs.');
text(s,60,145,1120,230,'50 fresh empirical replications per policy\nSame patient table for 2, 3 and 4 doctors within each run\nSeparate original-trace replay benchmark\nFresh confirmation seed: 93410',32,blue,true);
text(s,60,430,1120,150,'95% CI = mean ± t × sample SD / √50\nPaired difference: proposed staffing − reference\nKeep pooled P90, run attainment and service level separate',29);
s=slide(`${data.choice} doctors meet the primary mean target`,100,'Lee Ka Tung',`Primary fresh empirical results are shown with 95% t intervals in the table. With three doctors P90 is ${data.p90_ci[1]}, compared with ${data.p90_ci[0]} under two. Scheduled costs are ${data.cost.join(', ')} units. Paired 3-2 effect: ${data.paired}. Original-input replay for three: ${data.replay}; independent confirmation: ${data.confirmation}. ${Math.round(100*data.attainment)}% of runs meet the target, while mean patient service level is ${(100*data.service_level).toFixed(2)}%. A zero observed four-doctor P90 does not guarantee zero wait for all possible inputs.`);
chart(s,['2','3','4'],[{name:'Fresh empirical',values:data.p90,fill:blue},{name:'15-min target',values:[15,15,15],fill:orange}],60,145,610,365,'Mean run P90 (min)');
table(s,[['Doctors','P90 mean [95% CI]'],...data.p90_ci.map((v,i)=>[String(i+2),v])],710,165,500,255,[130,370]);
text(s,710,455,500,120,`${Math.round(100*data.attainment)}% run attainment\n${(100*data.service_level).toFixed(2)}% mean patient service level`,29,blue,true);
text(s,60,590,1120,45,'Scheduled cost: '+data.cost.map((v,i)=>`${i+2} doctors = ${v.toLocaleString()}`).join('   |   ')+' units',25,muted);
s=slide('The choice changes under input uncertainty',80,'Lee Ka Tung','Show separate one-factor changes. Faster arrivals compress gaps for the same 200 patients; doctor_slow scales consultation duration by1.1. Both require four doctors at 15 minutes. The continuous Poisson base has greater gap variability and also selects four. Do not assume this alternative is truer. Thresholds10/15/20/30 are evaluated without rerunning DES. Pharmacy-counter sensitivity affects downstream waits, not the one-way doctor queue.');
const selected=data.sensitivities.filter((r,i)=>i===0 || /base|arrivals fast|doctor slow/.test(r[0]));
table(s,selected.map((r,i)=>r.map((x,j)=>i===0&&j===3?'Choice':String(x).replaceAll('\n',' '))),60,145,1150,370,[365,300,300,185]);
text(s,60,555,1120,60,`Empirical base supports ${data.choice} doctors; stressed and Poisson cases support ${data.poisson_choice}`,29,blue,true);
text(s,60,620,1120,28,'P90 in minutes; choice = lowest cost with upper 95% CI ≤15 minutes',20,muted);
s=slide('Recommendation and next evidence',50,'Lee Ka Tung',data.brief+' Explain that the team must confirm synthetic-data acceptability, metric, cost and disclosure; actual data should precede a real clinical staffing change. Close within ten minutes, leaving Q&A outside the talk.');
text(s,60,150,1120,175,`Provisional policy: ${data.choice} doctors\nUse when the calibrated empirical pattern applies`,42,blue,true);
text(s,60,360,1120,200,`Review 4 doctors if demand or consultation times increase\nPoisson-arrival alternative selects ${data.poisson_choice} doctors\nCollect actual timing records before operational adoption\nPrincipal limitation: entirely synthetic calibration data`,30);
await fs.writeFile(path.join(root,'outputs/tables/deck_outline.json'),JSON.stringify(specs,null,2));
await fs.mkdir(path.join(root,'outputs/reproducibility/slide_render'),{recursive:true});
for(const [i,s] of p.slides.items.entries()){
 const blob=await p.export({slide:s,format:'png',scale:1});
 await fs.writeFile(path.join(root,`outputs/reproducibility/slide_render/slide-${i+1}.png`),new Uint8Array(await blob.arrayBuffer()));
}
await fs.mkdir(path.join(root,'.build/deck'),{recursive:true});
const candidate=path.join(root,'.build/deck/candidate.pptx');await (await PresentationFile.exportPptx(p)).save(candidate);
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:process.env.PRESENTATION_OUTPUT||path.join(root,'submission/presentation_rebuilt.pptx'),
 pythonExecutable:process.env.RUNTIME_PYTHON||'python3',
 integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[2,4,6,7].flatMap(n=>['--require-native-table-slide',String(n)])],
 requiredNativeTableOwnerSlides:[2,4,6,7],requiredNativeChartOwnerSlides:[6],explicitTotalSlideCount:8,
 materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
 receiptPath:path.join(root,'outputs/reproducibility/presentation_rebuilt.validation.json')});
console.log(JSON.stringify(result));
