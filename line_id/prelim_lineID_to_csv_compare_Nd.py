import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from scipy.interpolate import interp1d
from scipy.special import voigt_profile
from scipy.optimize import curve_fit

plt.rcParams.update({'font.size': 12})

floc = '/home/tim/research/tes/calibratedTES_Dec2022' # dir with photonlists
theory_csv = '/home/tim/research/tes/theory/Pr.csv' # generated by 'theory_to_csv.py'
full_theory_dat = '/home/tim/research/tes/theory/Pr_3e12/'
efficiency_curve_file = '/home/tim/research/tes/TES_Efficiency_Dec2022.csv'
ddest = '/home/tim/research/tes/line_id' # dir to save the various outputs

date1 = '202212'
day1 = '21'
runnum1 = '0002'
statelist1 = ['K']

date2 = '202212'
day2 = '21'
runnum2 = '0002'
statelist2 = ['T']

minenergy = 780
maxenergy = 1900
binsize = 1

use_prev_fit = False
write_csv = True

sigma_guess = 2 # approx gaussian width [eV]
gamma_guess = .001 # approx gaussian width [eV]
up_bound_sigma = 10 # max gaussian width
up_bound_gamma = .001 # max lorentzian width
max_center_shift = 5 # distance the fitted line center can be from the data
max_amp_shift = np.inf # distance the fitted line amplitude can be from the data
shift = -16

Nd_lines = [1360.3,1203.88,843.6,839.6,1176.6,1171.9,1236.2,1241.0,1244.4,1522.2,1528.5,1546.0]
Pr_guess = [i*(59/60)**2+shift for i in Nd_lines]


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def voigt(x,center,A,sigma,gamma):
     out = voigt_profile(x-center, sigma, gamma)
     return (A*out)/np.max(out)

def multi_voigt(x, *params):
    sigma = params[0]
    gamma = params[1]
    #fwhm = 0.5346*gamma + (0.2166*(gamma**2)+sigma**2)**0.5 # doi.org/10.1016/0022-4073(77)90161-3
    y = np.zeros_like(x)
    for i in range(2,len(params),2):
        y = y + voigt(x,params[i],params[i+1],sigma,gamma)
    return y

bin_edges = np.arange(minenergy, maxenergy+binsize, binsize)
x = np.arange(minenergy, maxenergy+binsize, binsize/5)

file = f'{floc}/{date1}{day1}_{runnum1}'
data1 = np.loadtxt(f'{file}_{statelist1[0]}photonlist.csv', skiprows=1, delimiter=',')
if len(statelist1)>1:
    for state in statelist1[1:]:
        data1 = np.vstack((data1,np.loadtxt(f'{file}_{statelist1}photonlist.csv', skiprows=1, delimiter=',')))

file = f'{floc}/{date2}{day2}_{runnum2}'
data2 = np.loadtxt(f'{file}_{statelist2[0]}photonlist.csv', skiprows=1, delimiter=',')
if len(statelist2)>1:
    for state in statelist2[1:]:
        data1 = np.vstack((data2,np.loadtxt(f'{file}_{statelist2}photonlist.csv', skiprows=1, delimiter=',')))


counts1, _ = np.histogram(data1, bins=bin_edges)
counts2, _ = np.histogram(data2, bins=bin_edges)
bin_centers = bin_edges[:-1]+binsize/2

th_spectra = os.listdir(full_theory_dat)

theory_df = pd.read_csv(theory_csv)
#'Energy','Total_intesity','Charge','Lower_config','Lower_index','Lower_J','Upper_config','Upper_index','Upper_J','Intensity'

theory_df.drop(theory_df[(theory_df.Energy < minenergy) | (theory_df.Energy > maxenergy)].index, inplace=True)
theory_df = theory_df.nlargest(20, 'Intensity').reset_index()

theory = theory_df[['Energy','Intensity']].to_numpy()

det_eff = np.loadtxt(efficiency_curve_file,delimiter=',',skiprows=1)
eff_curve = interp1d(det_eff[:,0],det_eff[:,1],kind='cubic')

guess = np.empty(len(theory)*2+2)
low_bounds = np.empty(len(guess))
up_bounds = np.empty(len(guess))

# gaussian width
guess[0] = sigma_guess
low_bounds[0] = 0
up_bounds[0] = up_bound_sigma

# lorentzian width
guess[1] = gamma_guess
low_bounds[1] = 0
up_bounds[1] = up_bound_gamma

# centers
peaks = theory[:,0]
guess[2::2] = peaks
low_bounds[2::2] = [peak - max_center_shift for peak in peaks]
up_bounds[2::2] = [peak + max_center_shift for peak in peaks]

# amplitudes
amps = theory[:,1] * 1E3 * eff_curve(theory[:,0])
guess[3::2] = amps
low_bounds[3::2] = [amp - max_amp_shift for amp in amps]
low_bounds[3::2] = [0 if lb <0 else lb for lb in low_bounds[3::2]]
up_bounds[3::2] = [amp + max_amp_shift for amp in amps]

# prev_fit = True #initializing
# if use_prev_fit:
#     if os.path.isfile(f'{ddest}/fit_{date}{day}_{runnum}_{statelist}'):
#         popt = np.loadtxt(f'{ddest}/fit_{date}{day}_{runnum}_{statelist}', delimiter=',')
#         pcov = np.loadtxt(f'{ddest}/cov_{date}{day}_{runnum}_{statelist}', delimiter=',')
#     else:
#         prev_fit = False
# else:
#     prev_fit = False

# if prev_fit == False:
#     popt, pcov = curve_fit(multi_voigt, bin_centers, counts, guess, bounds=(low_bounds,up_bounds))
#     np.savetxt(f'{ddest}/fit_{date}{day}_{runnum}_{statelist}', popt, delimiter=',')
#     np.savetxt(f'{ddest}/cov_{date}{day}_{runnum}_{statelist}', pcov, delimiter=',')

# csv = pd.read_csv(f'{ddest}.csv', skiprows=2)

#uncertainties = np.sqrt(np.diag(pcov))

#out = pd.DataFrame(data=[popt[2::2],uncertainties[2::2],popt[3::2],uncertainties[3::2], popt[0]*np.ones(len(theory)),uncertainties[0]*np.ones(len(theory))]).T
#out.columns = ['Center', 'Center_uncertainty', 'Amplitude', 'Amp_uncertainty', 'Sigma', 'Sigma_uncertainty']

# out = pd.merge(theory_df.sort_values(by=['Energy'], ignore_index=True), out.sort_values(by=['Center'], ignore_index=True), left_index=True, right_index=True)
# out = out[['Energy','Total_intesity','Charge','Lower_config','Lower_index','Lower_J','Upper_config','Upper_index','Upper_J','Intensity','Energy','Center', 'Center_uncertainty', 'Amplitude', 'Amp_uncertainty', 'Sigma', 'Sigma_uncertainty']]
# print(out)
# out.to_csv(f'{ddest}/linelist_{date}{day}_{runnum}_{statelist}.csv')

# color = iter(cm.rainbow(np.linspace(0, 1, len(th_spectra))))
# for spectrum in th_spectra:
#     th = np.loadtxt(full_theory_dat+spectrum)
#     th = th[(th[:,0]>=minenergy) & (th[:,0]<=maxenergy)]
#     th[:,1] = th[:,1] * eff_curve(th[:,0])
#     th[:,1] = th[:,1]/np.max(th[:,1])*np.max(counts)
#     c = next(color)
#     plt.plot(th[:,0],th[:,1], label=spectrum, linewidth=1.5, color=c)

# for i in theory[:,0]:
#     plt.axvline(i, color='grey', linestyle='--', zorder=0)

# for i in out['Center']:
#     plt.axvline(i, color='black', linestyle='--', zorder=0)

for i in Pr_guess:
    plt.axvline(i, color='red', linestyle='--', zorder=0)

for i in Nd_lines:
    plt.axvline(i, color='blue', linestyle='--', zorder=0)


#plt.plot(x, multi_voigt(x, *popt), color='r', linestyle='--', zorder=10, label=f'Fitted ($\sigma=${popt[0]:.2f})')
#plt.plot(x,multi_voigt(x,*guess), zorder=6, label='Theory')
plt.plot(bin_centers,counts1,marker='.', zorder=5, label=f'{date1}{day1}_{runnum1}_{statelist1}', color='red')
plt.plot(bin_centers,counts2,marker='.', zorder=5, label=f'{date2}{day2}_{runnum2}_{statelist2}', color='blue')

plt.legend()
plt.xlabel('Energy [eV]')
plt.ylabel(f'Counts per {binsize} eV bin')
#plt.title(f'{date}{day}_{runnum}_{statelist}')
plt.show()