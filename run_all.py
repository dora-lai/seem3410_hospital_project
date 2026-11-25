"""One-command, ordered pipeline. The full settings are the default."""
import argparse,json,shutil,subprocess,sys,time,traceback
from dataclasses import asdict
import pandas as pd
from config import ROOT,CFG
from src.common import status,write_json,save,filehash

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--no-package',action='store_true');args=parser.parse_args()
    if args.smoke:
        from src.des import simulate,verify_invariants
        from tests.test_des import hand
        from src.inputs import base_draws
        q,_=simulate(hand(),1);verify_invariants(q,1,1);a,_=base_draws(CFG.root_seed,2,10);assert (a[0]!=a[1]).any()
        write_json({'smoke':'PASS','patients':4,'hand_final_departure':q.PharmacyEnd.max()},'outputs/reproducibility/smoke.json');print('Smoke test PASS');return
    start=time.perf_counter();rawhash=filehash(ROOT/'data/raw/archive.zip')
    out=ROOT/'outputs'
    if out.exists():shutil.rmtree(out)
    out.mkdir();(ROOT/'CHECKLIST_STATUS.md').unlink(missing_ok=True)
    log=[]
    def stage(text):
        line=f'{time.perf_counter()-start:.2f}s {text}';print(line,flush=True);log.append(line)
        p=out/'reproducibility/run_log.txt';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('\n'.join(log)+'\n')
    write_json(asdict(CFG),'outputs/reproducibility/configuration.json')
    try:
        stage('0-1 Source review and frozen model specification')
        assert (ROOT/'docs/sources/SEEM3410_CODEX_MASTER_CHECKLIST.md').exists()
        status(['0'],'docs/source_review.md; docs/sources; raw archive SHA256 in audit','source review before implementation',issue='No starter supplied; license/generator documentation unavailable')
        save(pd.DataFrame([{'policy':f'{c} doctors','doctors':c,'pharmacy':CFG.pharmacy_counters,'fixed':'same inputs, priority3>2>1, FCFS pharmacy,200patients'} for c in CFG.doctors]),'tables/policies.csv')
        from src.plots import system_flow
        system_flow()
        status(['1.1','1.2','1.3'],'config.py; docs/model_spec.md; docs/metrics.md; policies.csv; outputs/figures/system_flow.svg generated before calibration')
        stage('2 Audit/calibration');from src.calibration import calibrate,capacity
        d,b,m=calibrate();stage('3 Analytical capacity checks');capacity(m)
        stage('4-5 DES unit tests and all-source reconstruction')
        test=subprocess.run([sys.executable,'-m','pytest','-q'],cwd=ROOT,text=True,capture_output=True)
        p=out/'verification/pytest.txt';p.parent.mkdir(exist_ok=True);p.write_text(test.stdout+'\n'+test.stderr)
        assert test.returncode==0,test.stdout+test.stderr
        from src.verification import verification
        verification(d)
        stage('6 Generate random inputs and verify matched streams')
        from src.experiments import generate_inputs,main_experiments,confirmation,sensitivities
        from src.analysis import analyze_main,analyze_confirmation,analyze_sensitivity,costs
        draws,conf,tables=generate_inputs(m)
        stage('7 Main fresh and replay experiments');r,p=main_experiments(b,tables)
        source=d.groupby(['Scenario','RunID','NumDoctors','PeakLimit']).DocWaitTime.quantile(.9,interpolation='linear').reset_index(name='run_p90')
        source=source.groupby(['Scenario','NumDoctors','PeakLimit']).run_p90.agg(['mean','std','count']).reset_index();source['comparison']='source scenarios have distinct inputs; distributional context only';save(source,'verification/scenario_distributional_comparison.csv')
        stage('8 Run-level inference and fresh confirmation');s,paired,ta=analyze_main(r,p)
        cr,cp=confirmation(tables);cs=analyze_confirmation(cr,cp)
        stage('9 Sensitivity and factorial interaction');sr,sp=sensitivities(m,draws,r,p);ss,dec=analyze_sensitivity(sr,sp)
        stage('10 Costs and computed recommendation');costs(pd.concat([r[r.experiment=='replay'],cr,sr]),pd.concat([s[s.experiment=='replay'],cs,ss]))
        stage('11 Figures/tables/seven-section report');from src.plots import plots
        from src.report import report
        plots();report()
        stage('12 Presentation materials and acceptance gates');from src.presentation import presentation
        from src.package import acceptance,environment,deterministic_hashes,manifest,package,write_review
        presentation();status(['12.2'],'README.md; requirements.txt; docs/course_mapping.md; docs/assumptions.md')
        acceptance();assert rawhash==filehash(ROOT/'data/raw/archive.zip')
        write_json(environment(start),'outputs/reproducibility/environment.json');write_json(deterministic_hashes(),'outputs/reproducibility/deterministic_hashes.json')
        if args.no_package:
            write_review();manifest();stage('Full computation completed (--no-package)')
        else:
            stage('Testing full workflow from extracted ZIP');receipt=package(start);stage('Extracted run and deterministic hash checks PASS: '+json.dumps(receipt))
            # Final ZIP includes final log and manifest after extraction.
            from src.package import make_zip
            manifest();make_zip()
    except Exception:
        stage('FAIL; dependent work stopped');(out/'reproducibility/failure.txt').write_text(traceback.format_exc());status(['active gate'],'outputs/reproducibility/failure.txt',state='FAIL',issue='See traceback; fix and rerun full workflow');raise

if __name__=='__main__':main()
