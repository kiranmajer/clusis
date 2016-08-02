import numpy as np
import math
from matplotlib.mlab import normpdf
import matplotlib.pyplot as plt
import matplotlib as mpl
import os.path
'''
TODO:

use more numpy stuff!
'''

kPattern = [[38.9637069, 0.932581], [39.96399867, 0.000117], [40.96182597, 0.067302]]
liPattern=[[6.0151222999999998, 0.075899999999999995], [7.0160039999999997, 0.92410000000000003]]
h2oPattern=[[18.0105646863, 0.99756999999999996], [19.0147815642, 0.00038000000000000002], [20.0148104642, 0.0020500000000000002]]


def calc_iso_dist(atomPattern, atomCount=20, threshold=0.01, rounding=2):
    finalPattern = []
    internalThreshold = threshold/100.
    
    for i in range(atomCount):
        currentPattern = {}
        
        # if pattern is empty (first atom) add current atom pattern
        if not finalPattern:
            finalPattern = atomPattern
            finalPattern.sort()
            continue
        
        # add atom to each peak of final pattern
        for peak in finalPattern:
            
            # skip peak under relevant abundance threshold
            if peak[1] < internalThreshold:
                continue
            
            # add each isotope of current atom to peak
            for isotope in atomPattern:
                mass = peak[0] + isotope[0]
                abundance = peak[1] * isotope[1]
                
                # add abundance to stored peak or add new peak
                mass = round(mass, rounding)
                if mass in currentPattern:
                    currentPattern[mass] += abundance
                else:
                    currentPattern[mass] = abundance
        
        # replace final pattern by current
        finalPattern = []
        for mass, abundance in currentPattern.items():
            finalPattern.append([mass, abundance])
        finalPattern.sort()
            
        # normalize pattern
        finalPattern = _normalize(finalPattern)        
                
    # discard peaks below threshold
    filteredPeaks = []
    for peak in finalPattern:
        if peak[1] >= threshold:
            filteredPeaks.append(peak)
    finalPattern = filteredPeaks
    # add fit parameter for scaling isotope mountain height
    pname = 'I{0}'.format(atomCount)
    finalPatternFit = [row+[pname] for row in finalPattern]        
        
    return finalPattern, finalPatternFit



def build_pattern_function(patternlist, sigma, X='X'):
    Y='gauss({3}, {0}, {2}, {1})'.format(patternlist[0][0], patternlist[0][1], sigma, X)
    for peak in patternlist[1:]:
        Y = Y + ' + gauss({3}, {0}, {2}, {1})'.format(peak[0], peak[1], sigma, X)
    return Y


def build_pattern_function_fit(patternlist, sigma, X='X'):
    Y='gauss({3}, {0}, {2}, {1}*{4})'.format(patternlist[0][0], patternlist[0][1], sigma, X, patternlist[0][2])
    for peak in patternlist[1:]:
        Y = Y + ' + gauss({3}, {0}, {2}, {1}*{4})'.format(peak[0], peak[1], sigma, X, peak[2])
    return Y


def gauss(x, mu, sigma, A=1):
    '''
    Return function values of a normal distribution as array.
    @param x: array of x values
    @param mu:
    @param sigma:
    @param A: amplitude
    '''
    y = A*sigma*np.sqrt(2*np.pi)*normpdf(x, mu, sigma)
    return y


def m_to_tof(m_amu, t_ref, t_offset, m_ref=193.96, timeunit=1e-6):
    return ((t_ref - t_offset)*np.sqrt(m_amu/m_ref) + t_offset)/timeunit


def sigma(R, m):
    '''
    Calculates the sigma s of gaussion fct. dependend on (center) mass
    and resolution R=m/dm, when FWHM=2*sqrt(2*math.log(2))*s
    '''
    s = m/(2*math.sqrt(2*math.log(2))*R)
    return s


def sim_ms(isoPattern, startsize, endsize, sigma, dopants=None):
    '''
    Calculates mass spectrum from a given isotopic distribution 
    @param isoPattern:
    @param startsize:
    @param endsize:
    @param sigma:
    dopants: tupels (mass, peak intensity)
    '''
    xrange = 10001 # should be adapted to fit data file
    sizerange = range(startsize, endsize+1)
    peaklist = []
    for size in sizerange:
        peaklist = peaklist + calc_iso_dist(isoPattern, size, 0.001, 3)[0]
    peaklist = np.array(peaklist)
    if dopants:
        for dopant in dopants:
            peaklist_dopant = (peaklist+(dopant[0], 0))*(1, dopant[1])
            peaklist = np.concatenate((peaklist, peaklist_dopant))
    
    X = np.linspace(peaklist[0][0]-1, peaklist[-1][0]+1, xrange)
    Y = np.array(eval(build_pattern_function(peaklist, sigma)))
     
    return X, Y, peaklist


def sim_tof(peaklist, t_ref, t_off, sigma):
    xrange = 10001
    tof_peaklist = np.array([m_to_tof(peaklist[:,0], t_ref, t_off),
                             peaklist[:,1]]).transpose()
    X_tof = np.linspace(tof_peaklist[0][0], tof_peaklist[-1][0], xrange)
    Y_tof = np.array(eval(build_pattern_function(tof_peaklist, sigma)))
    
    return  X_tof, Y_tof, tof_peaklist


def fit_tof(peaklist, t_ref, t_off, sigma, X_tof):
    #xrange = 10001
    X_tof=X_tof/1e-6
    tof_peaklist = np.array([m_to_tof(peaklist[:,0], t_ref, t_off),
                             peaklist[:,1]]).transpose()
    #X_tof = np.linspace(tof_peaklist[0][0], tof_peaklist[-1][0], xrange)
    Y_tof = np.array(eval(build_pattern_function(tof_peaklist, sigma, 'X_tof')))
    
    return  X_tof, Y_tof, tof_peaklist


def err_func(p,peaklist,sigma, ref_ms):
    Y_sim = fit_tof(peaklist, p[0], p[1], sigma, ref_ms.data['spectra'][2])[1]
    return Y_sim/np.amax(Y_sim)*np.amax(ref_ms.data['spectra'][0]) - ref_ms.data['spectra'][0]



def _normalize(data):
    """Normalize data."""
    
    # get maximum Y
    maximum = data[0][1]
    for item in data:
        if item[1] > maximum:
            maximum = item[1]
    
    # normalize data data
    for x in range(len(data)):
        data[x][1] /= maximum
    
    return data


def plot_ms(iso_pattern, center_mass, dm, res, dopants=None, unit='# of atoms', pdf=None, size=[20,14]):
    #clear plots
    plt.close('all')
    # calc center of mass
    s = 0
    for p in iso_pattern:
        s += p[0]*p[1]
        
    # calc distribution for each resolution
    res = list(res)
    plt_data = []
    for r in res:
        x,y,pl=sim_ms(iso_pattern, center_mass-dm, center_mass+dm, sigma(r, center_mass*iso_pattern[0][0]), dopants)
        plt_data.append([x, y])
        
    # plot
    idx = 0
    for l in plt_data:
        if idx == 0:
            plt.plot(l[0]/s, l[1], color='blue', lw=1.5)
        else:
            plt.plot(l[0]/s, l[1]/l[1].max()*plt_data[0][1].max()*1, color='DimGray', lw=0.5)
            
        idx += 1
    
    plt.axis([center_mass-dm+1.5, center_mass+dm-1.5, 0, plt_data[0][1].max()*1.1])
    ax = plt.gca()
    #ax.set_xlim(center_mass-dm+1.5, center_mass+dm-1.5)    
    ax.set_xlabel('cluster mass ({})'.format(unit))
    ax.yaxis.set_major_locator(mpl.ticker.NullLocator())
    plt.grid()
    
    if pdf:
        fname = os.path.join(os.path.expanduser('~'), pdf+'.pdf')
        w = size[0]/2.54
        h = size[1]/2.54
        fig = plt.gcf()
        fig.set_size_inches(w,h)
        fig.savefig(fname, bbox_inches='tight')
    else:
        plt.show()
    
    
    