import numpy as np
import scipy.constants as con

Ee=2
Ei=100

ve = lambda Ee: np.sqrt(2*Ee*con.electron_volt/(con.electron_mass))
vi = lambda Ei: np.sqrt(2*Ei*con.electron_volt/(con.atomic_mass*195))

veff = lambda vp: np.sqrt(vi(Ei)**2+2*vp*vi(Ei)+ve(Ee)**2)

dt=np.abs(1.6*(1/veff(ve)-1/veff(-ve)))*1e6

Eeff = lambda vp: con.electron_mass*(vi(Ei)**2+2*vp*vi(Ei)+ve(Ee)**2)/(2*con.electron_volt)
