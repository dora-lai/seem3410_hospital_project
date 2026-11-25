# Model specification (frozen before results)
Decision: lowest illustrative scheduled cost among 2, 3, 4 doctors meeting E[run P90 doctor wait] <=15 minutes. Baseline 2; one pooled doctor queue; priority 3 > 2 > 1, FCFS within class; consultations non-preemptive. Pharmacy pooled FCFS with one counter, two only as sensitivity. Infinite waiting rooms. Each patient visits both stages once.

Boundary: arrival -> priority doctor queue -> consultation -> FCFS pharmacy -> departure. No breaks, abandonment, rejection, travel, registration, appointments, routing, feedback or finite buffers. All records are synthetic Kaggle outputs, not hospital observations. No claim of real-system validation.

Empty at t=0; exactly 200 arrivals, drain every patient; 240 minutes is peak boundary, not closing time. No warm-up deletion. Doctors remain available until drain even after illustrative 1080-minute schedule. Outcomes are never censored at schedule end.

Primary: fresh empirical inputs; original baseline replay is separate benchmark; piecewise Poisson is structural sensitivity. Fixed within each policy comparison: patient inputs, priority discipline, pharmacy and peak rule. Configurable decisions and assumptions in config.py; policies differ only by doctors in main experiment. See metrics.md, assumptions.md and des_pseudocode.md.
