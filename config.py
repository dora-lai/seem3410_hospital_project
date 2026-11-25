"""Provisional assumptions fixed before experiments. Units: minutes, cost units."""
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parent
@dataclass(frozen=True)
class Config:
    root_seed:int=3410
    confirmation_seed:int=93410
    replications:int=50
    n_patients:int=200
    doctors:tuple=(2,3,4)
    pharmacy_counters:int=1
    peak_limit:float=240.
    target:float=15.
    targets:tuple=(10.,15.,20.,30.)
    horizon:float=1080.
    doctor_wage:float=100.
    wage_factors:tuple=(.5,1.,1.5,2.)
    overtime_premiums:tuple=(1.,1.5,2.)
    arrival_factors:tuple=(.9,1.1)
    doctor_service_factors:tuple=(.9,1.1)
    pharmacy_service_factor:float=1.1
    primary_model:str='empirical'
    quantile_method:str='linear'
    time_decimals:int=9
    tolerance:float=1e-8
    baseline_scenario:str='Baseline_2Doc_240Peak'
    team:tuple=(('Lai Sin Hang','1155213900'),('Lee Ka Tung','1155212062'))
    source_url:str='https://www.kaggle.com/datasets/juneminazuki/hospital-queue-and-patient-flow-simulation'
    def digest(self):
        return hashlib.sha256(json.dumps(asdict(self),sort_keys=True).encode()).hexdigest()
CFG=Config()
