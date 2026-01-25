import numpy as np
from matplotlib import pyplot as plt
from . import sblib as sb
import warnings
from . import anglesLib


def timeseriesPUV(p, u, v, t, waterDepth, gaugeDepth):
    """The goal with this function is to create time series anaylysis work flow
         runs welch method fft with 512 record segments, with 1/4 overlabpand 5 freq bin band averaging
    
    corrects pressure spectra to surface spectra using pressure response function
    
     below parameters and makes them into magical wave data

    Args:
      p: pressure in cm
      u: u velocities
      v: v velocities
      t: time stamp
      waterDepth: positive in meters
      gaugeDepth: negative in meters
      frequency: spectra
      a1: interped to np.arange(0.04, 0.5, 0.0075)
      b1: interped to np.arange(0.04, 0.5, 0.0075)
      a2: interped to np.arange(0.04, 0.5, 0.0075)
      b2: interped to np.arange(0.04, 0.5, 0.0075)

    Returns:
      param frequency spectra

    """
    from scipy.signal import welch, csd

    Fsamp = 1 / np.median(np.diff(t))  # sample frequency (not period)
    nseg = 512  # 512
    overlap = nseg / 4
    bave = 5  # number of spectral bands to average (taken from kent)

    # Calculate spectra in each componant
    # x is north, y is east in kents code (used for  a's b's)
    pDemeaned = (p - np.mean(p)) / 100  # demean pressure and convert to meters
    [f1, Sp] = welch(x=pDemeaned, window='hanning', fs=Fsamp, nperseg=nseg, noverlap=overlap, nfft=None,
                     return_onesided=True, detrend='linear')
    [f1, Su] = welch(x=u, window='hanning', fs=Fsamp, nperseg=nseg, noverlap=overlap, nfft=None, return_onesided=True,
                     detrend='linear')
    [f1, Sv] = welch(x=v, window='hanning', fs=Fsamp, nperseg=nseg, noverlap=overlap, nfft=None, return_onesided=True,
                     detrend='linear')
    # create cross spectral power across the 3
    [_, CrossPU] = csd(y=pDemeaned, x=u, fs=Fsamp, nperseg=nseg, noverlap=overlap, return_onesided=True,
                        window='hann')
    [_, CrossPV] = csd(y=pDemeaned, x=v, fs=Fsamp, nperseg=nseg, noverlap=overlap, return_onesided=True,
                        window='hann')
    [f1, CrossUV] = csd(y=v, x=u, fs=Fsamp, nperseg=nseg, noverlap=overlap, return_onesided=True,
                        window='hann')
    ## now Do some frequency band Averaging
    # first remove first index of array  "remove DC compoonents"
    f1 = f1[1:]
    Sp = np.real(Sp[1:])
    Su = np.real(Su[1:])
    Sv = np.real(Sv[1:])
    CrossPU = CrossPU[1:]
    CrossPV = CrossPV[1:]
    CrossUV = CrossUV[1:]
    # correcting Pressure spectra to surface spectra
    L, _, _ = dispersion(waterDepth, T=1 / f1)
    prF = prFunc(L, waterDepth, gaugeDepth)  #
    Sp = Sp / prF ** 2  # getting surface corrected energy spectrum

    #  Beginning to Setup For Band Averaging
    dk = int(np.floor(bave / 2))

    # band averaging
    freq, SpAve, SuAve, SvAve, CrossPUave, CrossPVave, CrossUVave = [], [], [], [], [], [], []
    for kk in range(dk + 1, len(Sp) - dk, bave):
        avgIdxs = np.linspace(kk - dk, kk + dk, num=int((kk + dk) - (kk - dk) + 1), endpoint=True, dtype=int)
        freq.append(f1[int(kk)])                            # taking the first frequency for the bin label
        # bin averaging frequency spectra across bave frequency bins
        SpAve.append(np.sum(Sp[avgIdxs]) / (bave+1))
        SuAve.append(np.sum(Su[avgIdxs]) / (bave+1))
        SvAve.append(np.sum(Sv[avgIdxs]) / (bave+1))
        # bin averaging cross correlations
        CrossPUave.append(np.sum(CrossPU[avgIdxs]) / (bave+1))  # Press - FRF X
        CrossPVave.append(np.sum(CrossPV[avgIdxs]) / (bave+1))  # Press - FRF Y
        CrossUVave.append(np.sum(CrossUV[avgIdxs]) / (bave+1))  # FRF X - FRF Y
    # convert back to Numpy array
    freq = np.array(freq)
    SpAve = np.array(SpAve)
    SuAve = np.array(SuAve)
    SvAve = np.array(SvAve)
    CrossPUave = np.array(CrossPUave)
    CrossPVave = np.array(CrossPVave)
    CrossUVave = np.array(CrossUVave)

    # Extracting as and bs
    a1 = np.imag(CrossPUave) / np.sqrt(SpAve * (SuAve + SvAve))
    b1 = -np.imag(CrossPVave) / np.sqrt(SpAve * (SuAve + SvAve))
    a2 = (SuAve - SvAve) / (SvAve + SuAve)
    b2 = -2 * np.real(CrossUVave) / (SvAve + SuAve)

    wfreq = np.arange(0.04, 0.5, 0.0075)  # frequencies to interp to
    wDeg = np.arange(0, 360, 5)
    # interpolating to reasonable frequency banding
    import scipy.interpolate as interp
    f = interp.interp1d(freq, a1, kind='linear')
    a1interp = f(wfreq)
    f = interp.interp1d(freq, a2, kind='linear')
    a2interp = f(wfreq)
    f = interp.interp1d(freq, b1, kind='linear')
    b1interp = f(wfreq)
    f = interp.interp1d(freq, b2, kind='linear')
    b2interp = f(wfreq)
    f = interp.interp1d(freq, SpAve, kind='linear')
    fspec = f(wfreq)

    # mlmSpec = mlm(freqs=freq, dirs=np.arange(0,360,5), c11=SpAve, c22=SuAve, c33=SvAve, c23=np.real(CrossUVave), q12=np.imag(CrossPUave), q13=np.imag(CrossPVave))

    return fspec, a1interp, b1interp, a2interp, b2interp

def UrsellNumber(Tp, Hs, depth):
    """calculates ursell number """
    L, _, _ = dispersion(depth, Tp)
    return Hs*L**2/(depth**3)

def qkhfs(w, h):
    """Quick iterative calculation of kh in gravity-wave dispersion relationship
            kh = qkhfs(w, h )

    References:
        Orbital velocities from kh are accurate to 3e-12 !
            RL Soulsby (2006) \"Simplified calculation of wave orbital velocities\"
            HR Wallingford Report TR 155, February 2006
            Eqns. 12a - 14

    Args:
      w: angular wave frequency = 2*pi/T where T = wave period [1/s]
      h: water depth [m]
    

    Returns:
        kh - wavenumber * depth [ ]
    """
    g = 9.81
    x = w ** 2.0 * h / g
    y = np.sqrt(x) * (x < 1.) + x * (x >= 1.)
    # is this appalling code faster than a loop in Python? It is in Matlab.
    t = np.tanh(y)
    y = y - ((y * t - x) / (t + y * (1.0 - t ** 2.0)))
    t = np.tanh(y)
    y = y - ((y * t - x) / (t + y * (1.0 - t ** 2.0)))
    t = np.tanh(y)
    y = y - ((y * t - x) / (t + y * (1.0 - t ** 2.0)))
    kh = y

    warnings.warn("Function gkhfs() may perform similarly to function dispersion().", UserWarning)

    return kh

def HPchop_spec(spec, dirbin, angadj=0, corrected=1):
    """This function chops a spectra into half plane, assuming already shore normal waves,
    it will remove half of the spectra not incident to shore

    NOTE: THIS FUNCTION DOES NOT FLIP THE ANGLE CONVENTION FROM CARTESIAN TO GEOGRAPHIC
    USE GEO2GRID SPEC ROTATE FOR THIS

      ASSUMPTIONS:
        waves are already shore normal
        follows MET convention (angles measured in the from direction)

    Args:
      spec: 2D directional spectra (record count x frq x direction )
      dirbin: associated directions with the spectra
      angadj: rotation angle to make 0 shorenormal angle in deg true north of shore perpendicular
            MET convention (shore->sea)THE PORTION OF THE SPECTRA traveling opposite this
            will be removed (Default value = 0)
      corrected (bool):  corrected = True for input being between 0:360
                        corrected = False for input containing negative values
                        (Default value = True)

    Returns:
        newspec:    new Half plane spectra

        newdirband: direction bands associated with Halfplane spectra

    Notes:
        if angadj ==0 directions are output as Shore Normal
        if angadj !=0 directions are output as True North

    """
    dirbin = np.array(dirbin)
    # if angadj != 0:
    #     dirbin = angle_correct(dirbin - angadj)
    if angadj < 0:  # if a
        # rotating dirbin if need be
        dirbin = anglesLib.angle_correct(dirbin - angadj)
    elif angadj > 0:
        dirbin = dirbin - angadj

    zeroidx = abs(np.array(dirbin)).argmin()  # index of zero degrees
    deltadeg = np.abs(np.median(np.diff(dirbin)))
    ## number of bins on either side of zero non inclusive of zero (only in HP)
    nbins = int(((360 / 4) - 1) / deltadeg)

    if zeroidx + nbins > len(dirbin):  # if the zero + nbins wraps
        mmidx = zeroidx + nbins - len(dirbin)  # how many wrapped (extra)
        mlist = np.concatenate((list(range(zeroidx, len(dirbin))), list(range(0, mmidx + 1))))
    else:
        mlist = list(range(zeroidx, zeroidx + nbins + 1))  # indicies of new zero to the max on this side of zero
    if zeroidx == 0:
        zzidx = abs(zeroidx - nbins)  # how many wrap
        zlist = list(range(np.size(dirbin) - zzidx, np.size(dirbin)))
    elif zeroidx - nbins < 0:  # if the lower bound of the hp wraps
        zzidx = abs(zeroidx - nbins)  # extra (wrap points)
        zlist = np.concatenate((list(range(np.size(dirbin) - zzidx, np.size(dirbin))), list(range(0, zeroidx))))
    else:
        zlist = list(range(zeroidx - nbins, zeroidx))
    # create newly halfed direction bands and new spectra
    newdirband = np.concatenate([dirbin[zlist], dirbin[mlist]],
                                axis=0)  # pulling proper angle bins together (with shore perp centered
    # newspec = np.zeros([np.size(spec, axis=0), np.size(spec, axis=1), np.size(newdirband)])  # initializing
    newspec = np.concatenate([spec[:, :, zlist], spec[:, :, mlist]], axis=2)  # pulling proper spec data

    if angadj != 0 and corrected == 1:
        newdirband = anglesLib.angle_correct(newdirband + angadj)
    elif corrected == 1:
        newdirband = anglesLib.angle_correct(newdirband)

    return newspec, newdirband

def makeMLMspecFromAsBs(a0, a1, b1, a2, b2, waterDepth, freqs, dirs):
    """from a's and b's make the 2D frequency direction spectra
    translated from matlab from kent hathaway, by spicer bak
    (could be improved, verified)

    Args:
      a0: frequency spectrum
      a1: 1st fouier coeffieicnt componant
      b1: 1st fouier coefficient componant
      a2: 2nd fouier coefficient componant
      b2: 2nd fouier coefficient componant
      waterDepth: water depth [m]
      param freqs: frequencies
      dirs: directions

    Returns:
      array [t, freq, dir]
      an array of 2dimensional frequency direction spectra

    """
    waveFreqBins = freqs
    waveDirBins = dirs

    L, _, _ = dispersion(waterDepth, 1 / waveFreqBins)  # calculating wave number
    xk = 2 * np.pi / L  # calculating wave number over depth
    ak = 1 / np.tanh(xk * 250)
    c11 = a0
    c22 = 0.5 * (1 + a2) * (ak ** 2) * a0  #  Cnn
    c33 = 0.5 * (1 - a2) * (ak ** 2) * a0  #  Cww
    c23 = 0.5 * b2 * (ak ** 2) * a0        #  Cnw
    q12 = a1 * ak * a0                     #  Qvn
    q13 = b1 * ak * a0                     #  Qvw
    spec = mlm(waveFreqBins, waveDirBins, c11, c22, c33, c23, q12, q13)

    return spec

def mlm(freqs, dirs, c11, c22, c33, c23, q12, q13):
    """From kent hathaway's code translated from fortran, chuck long -> hanson mlm.m

    Maxumum Likelihood Method (MLM) directional wave analysis

    Reference:
       J. Oltman-Shay & R.T. Guza, A Data-Adaptive Ocean Wave Directional
       Spectrum Estimator for Pitch and Roll Type Measurements, Journal
       of Physical Oceanography, Vol. 14, pp. 1800-1810, 1984.

    TODO: could be improved (verified)

    Args:
      freq: frequencies
      dirs: direction bins
      c11: cross spectrum of 1st channel - pressure (or welch specturm)
      c22: cross spectrum of 2nd channel - u        (or welch specturm)
      c33: cross spectrum of 3rd channel - v        (or welch specturm)
      c23: real part of cross spectrum of 2nd and 3rd channel u v
      q12: imaginary part of 1st and 2nd channel (p u)
      q13: imaginary part of 1st and 3rd channel (p v)
      freqs: returns: 2D directional spectrum using MLM method (non-iterative)
            IN  per RADIAN UNITS  -> must be converted back to degrees

    Returns:
      2D directional spectrum using MLM method (non-iterative)
      IN  per RADIAN UNITS  -> must be converted back to degrees

    """
    # calculating sin/cos terms from direction angles
    angRad = np.deg2rad(dirs);  # directions in radians (for sin/cos calcs)
    ainc = np.median(np.abs(np.diff(dirs)))  # delta degrees of directions
    sint = np.sin(angRad);
    cost = np.cos(angRad);
    sin2t = np.sin(2. * angRad);
    cos2t = np.cos(2. * angRad);

    dsprdMLM = np.ones((len(freqs), len(dirs)))  # pre allocated space for spectra out
    eftMLM = np.ones((len(freqs), len(dirs)))
    for n1 in range(0, len(freqs)):
        # find spectral values below energy threshold
        if c11[n1] < 1e-5:
            dsprdMLM[n1, :] = 0.0
        else:
            # 1.1 wave number from spectra
            xk = np.sqrt((c22[n1] + c33[n1]) / c11[n1])
            d = c11[n1] * c22[n1] * c33[n1] - c11[n1] * c23[n1] ** 2 - q12[n1] ** 2 * c33[n1] \
                - q13[n1] ** 2 * c22[n1] + 2 * q12[n1] * q13[n1] * c23[n1]
            tmp = 2 * (c22[n1] * c33[n1] - c23[n1] ** 2) / d

            a0 = tmp + (c11[n1] * c22[n1] + c11[n1] * c33[n1] - q12[n1] ** 2 - q13[n1] ** 2) * xk ** 2 / d
            a1 = -2 * (q12[n1] * c33[n1] - q13[n1] * c23[n1]) * xk / d
            b1 = 2 * (q12[n1] * c23[n1] - q13[n1] * c22[n1]) * xk / d
            a2 = 0.5 * (c11[n1] * c33[n1] - c11[n1] * c22[n1] - q13[n1] ** 2 + q12[n1] ** 2) * xk ** 2 / d
            b2 = -(c11[n1] * c23[n1] - q12[n1] * q13[n1]) * xk ** 2 / d
            # 1.2 Directional Spread
            denom = 0.5 * a0 + a1 * cost + b1 * sint + a2 * cos2t + b2 * sin2t;
            # mn = min(denom)
            # if mn <= 6:
            #    denom = denom - mn + 6
            # dd2[n1] = denom
            # dd[n1] = d
            dsprdMLM[n1, :] = np.abs(1 / denom)
            asum = np.sum(dsprdMLM[n1, :])
            #
            # 2.0 Normalize directional spreading function to unity
            #    NOTE: put back the 1/rad units!!!
            asum = asum * ainc
            dsprdMLM[n1, :] = dsprdMLM[n1, :] / asum
    ## 3.0 Generate The 2D spectrum
    for fcount in range(0, len(freqs)):
        eftMLM[fcount, :] = c11[fcount] * dsprdMLM[fcount, :]

    return eftMLM

def prFunc( L, d, z):
    """Surface correction for pressure data.  if working with an energy
    spectrum DIVIDE by the returned prf**2

    Args:
      L: wave length  (column)  (m)
      d: water depth     ( positve scalar)  (m)
      z: gage location below surface (negative) (m)

    Returns:
      Pressure Response (column) of length freqeuencys

    """
    maxCorrectionFactor = 10
    # checks
    assert len(np.unique(
        z)) == 1, 'pressure response function cannot handle varying depth right now, shouldn''t be hard to modify'
    assert d > 0, 'water depth must be positive (meters)'
    if np.size(z) == 1:
        z = np.array(z)
    elif len(z) > 1:
        z = np.array(z)[0]
    assert z < 0, 'gauge location must be negative (meters)'
    # ## # now calcs
    arg1 = np.cosh(2 * np.pi * (d + z) / L);
    arg2 = np.cosh(2 * np.pi * (d) / L);
    prf = arg1 / arg2
    # limit the amount
    if (prf <= 1 / maxCorrectionFactor).any():
        print('correcting extreme attenuation')
        prf[np.argwhere(prf <= 1 / maxCorrectionFactor)] = 1

    return prf

def dispersion( h, T):
    """Linear Dispersion Relationship
    omega^2 = gk tanh kh
    approximation and iterative method taken from

    References:
        ib svendsen: "introduction to nearshore hydrodynamics" p 68

    Args:
      h: this is depth in meters
      T: this is wave period in seconds

    Returns:
      L: wave Length estimate
      c: wave speed estimate
      n: group/ wave speed ratio


    """
    assert (np.array(h) > 0).all(), 'Water depth must be >0, positive downward convention'
    # set vars
    g = 9.8  # gravity
    residThresh = 0.0001  # threshold for convergence  # hold to 3 decimal places
    omega = 2 * np.pi / T  # wave orbital frequency
    kh_guess = omega ** 2 * h / g  # inital guess at kh
    kh_next = 0  # initalization value
    while (np.abs(kh_next - kh_guess) > residThresh).any():
        kh_next = ((omega ** 2 * h) / g) * 1 / np.tanh(kh_guess)  # used 1/tanh instead of coth
        kh_guess = ((omega ** 2 * h) / g) * 1 / np.tanh(kh_next)  # used 1/tanh instead of coth

    k = kh_guess / h  # calculate wave number
    L = 2 * np.pi / k  # calculate wave length
    c = omega / k  # calculate wave speed
    n = 0.5 * (1 + (2 * k * h) / np.sinh(2 * k * h))  # group/ wave speed ratio

    warnings.warn("Function dispersion() may perform similarly to function gkhfs().", UserWarning)

    return L, c, n

def timeSeriesAnalysis1D(time, eta, **kwargs):
    """process 1D timeserise analysis, function will demean data by default.  It can operate on
    2D spatial surface elevation data, but will only do 1D analysis (not puv/2D directional waves)
    for frequency band averaging, will label with band center

    Args:
        time: time (datetime object)
        eta: surface timeseries

        **kwargs:
            'windowLength': window length for FFT, units are minutes (Default = 10 min)
            'overlap': overlap of windows for FFT, units are percentage of window length (Default=0.75)
            'bandAvg': number of bands to average over
            'timeAx' (int): a number defining which axis in eta is time (Default = 0)
            'returnSetup' (bool): will calculate and return setup (last postion)  (Default = False)

    Returns:
        fspec (array): array of power spectra, dimensioned by [space, frequency]
        frqOut (array): array of frequencys associated with fspec

    Raises:
        Warnings if not all bands are processed (depending on size of freqeuency bands as output by FFT
            and band averaging chosen, function will neglect last few (high frequency) bands

    TODO:
        can add surface correction for pressure data

    """
    from scipy.signal import welch
    import warnings
    import datetime as DT
    assert isinstance(time, np.ndarray), 'Must be input as an array'
    assert isinstance(time[0], DT.datetime), 'time must be in datetime'
    ## kwargs below
    nPerSeg = kwargs.get('WindowLength', 10)  # window length (10 minutes in seconds)
    overlapPercentage = kwargs.get('overlap', 3 / 4)  # 75% overlap per segment
    bandAvg = kwargs.get('bandAvg', 6)  # average 6 bands
    myAx = kwargs.get('timeAx', 0)  # time dimension of eta
    overlap = nPerSeg * overlapPercentage
    ## preprocessing steps
    etaDemeaned = np.nan_to_num(eta - np.mean(eta, axis=0))

    # etaDemeaned = np.ma.masked_array(etaD, mask=np.isnan(eta).data, fill_value=-999)   # demean surface time series
    assert eta.shape[myAx] == time.shape[0], "axis selected for eta doesn't match time"
    freqSample = 1/np.median(np.diff(time)).total_seconds()

    freqsW, fspecW = welch(x=etaDemeaned, window='hanning', fs=freqSample, nperseg=nPerSeg*60, noverlap=overlap,
                           nfft=None, return_onesided=True, detrend='linear', axis=myAx)
    # remove first index of array (DC components)--?
    freqW = freqsW[1:]
    fspecW = fspecW[1:]
    ## TODO: add surface correction here

    # initalize for band averaging
    # dk = np.floor(bandAvg/2).astype(int)  # how far to look on either side of band of interest
    frqOut, fspec = [], []
    for kk in range(0, len(freqsW) - bandAvg, bandAvg):
        avgIdxs = np.linspace(kk, kk + bandAvg - 1, num=bandAvg).astype(int)
        frqOut.append(freqW[avgIdxs].sum(axis=myAx) / bandAvg)  # taking average of freq for label (band centered label)
        fspec.append(fspecW[avgIdxs].sum(axis=myAx) / bandAvg)
    if max(avgIdxs) < len(freqW):  # provide warning that we're not capturing all energy
        warnings.warn('neglected {} freq bands (at highest frequency)'.format(len(freqW) - max(avgIdxs)))

    frqOut = np.array(frqOut).T
    fspec = np.array(fspec).T
    # output as
    fspec = np.ma.masked_array(fspec, mask=np.tile((fspec == 0).all(axis=1), (frqOut.size, 1)).T)
    return fspec, frqOut

def stats1D(fspec, frqbins, lowFreq=0.05, highFreq=0.5):
    """Calculates bulk statistics from a 1 dimentional spectra, calculated as inclusive with
        high/low frequency cuttoff

    Args:
      fspec: frequency spectra
      frqbins: frequency bins associated with the 1d spectra
      lowFreq: low frequency cut off for analysis (Default value = 0.05)
      highFreq: high frequency cutoff for analysis (Default value = 0.5)

    Returns:
      a dictionary with statistics
         'Hmo':   Significant wave height

         'Tp':   Period of the peak energy in the frequency spectra, (1/Fp).  AKA Tpd, not to be
             confused with parabolic fit to spectral period

         'Tm':    Tm02   Mean spectral period (Tm0,2, from moments 0 & 2), sqrt(m0/m2)

         'Tave':  Tm01   Average period, frequency sprectra weighted, from first moment (Tm0,1)

         'sprdF':  Freq-spec spread (m0*m4 - m2^2)/(m0*m4)  (one definition)

         'Tm10': Mean Absolute wave Period from -1 moment

         'meta': expanded variable name/descriptions

    """
    assert fspec.shape[-1] == len(frqbins), '1D stats need a 1 d spectra'
    if highFreq is None:
        highFreq = np.max(frqbins)
    if lowFreq is None:
        lowFreq = np.min(frqbins)
    frqbins = np.array(frqbins)

    df = np.diff(np.append(frqbins[0], frqbins), n=1)

    # truncating spectra as useful
    idx = np.argwhere((frqbins >= lowFreq) & (frqbins <= highFreq)).squeeze()

    m0 = np.sum(fspec[:, idx] * df[idx], axis=1)  # 0th momment
    m1 = np.sum(fspec[:, idx] * df[idx] * frqbins[idx], axis=1)  # 1st moment
    m2 = np.sum(fspec[:, idx] * df[idx] * frqbins[idx] ** 2, axis=1)  # 2nd moment
    # m3 = np.sum(fspec[:, idx] * df[idx] * frqbins[idx] ** 3, axis=1)  # 3rd moment
    m4 = np.sum(fspec[:, idx] * df[idx] * frqbins[idx] ** 4, axis=1)  # 4th moment
    m11 = np.sum(fspec[:, idx] * df[idx] * frqbins[idx] ** -1, axis=1)  # negitive one moment
    # wave height
    Hm0 = 4 * np.sqrt(m0)

    ipf = fspec.argmax(axis=1)  # indix of max frequency
    Tp = 1 / frqbins[ipf]  # peak period
    Tm02 = np.sqrt(m0 / m2)  # mean period
    Tm01 = m0 / m1  # average period - cmparible to TS Tm
    Tm10 = m11 / m0
    sprdF = (m0 * m4 - m2 ** 2) / (m0 * m4)

    meta = 'Tp - peak period, Tm - mean period, Tave - average period, comparable to Time series mean period, sprdF - frequency spread, sprdD - directional spread'
    stats = {'Hm0': Hm0,
             'Tp': Tp,
             'Tm': Tm02,
             'Tave': Tm01,
             'sprdF': sprdF,
             'Tm10': Tm10,
             'meta': meta}

    return stats

def waveStat(spec, frqbins, dirbins, lowFreq=0.05, highFreq=0.5):
    """this function will calculate the bulk statistics from 2D directional energy spectrum, to get directional
    properties, the a's/b's are generated from the 2D directional spectra input.

    defaults to 0.05 hz to 0.5 hz frequency for the statistics
    
    Code Translated by Spicer Bak from: fd2BulkStats.m written by Kent Hathaway, and adapted in python


    Args:
      spec (array):  this is a 2d spectral inputshaped by [time, freq, dir]

      frqbins: Frequency vector (not assumed constant)

      dirbins: an array of direction bins associated with the 2d spec

      lowFreq: low frequency cutoff for the spectral stat's calculation (Default value = 0.05)

      highFreq: high frequency cutoff for the spectral stat's calculation (Default value = 0.5)

    Returns:
      dictionary
           'Hmo':   Significant wave height

           'Tp':   Period of the peak energy in the frequency spectra, (1/Fp).  AKA Tpd, not to be
                confused with parabolic fit to spectral period

           'Tm':   -- Tm02   Mean spectral period (Tm0,2, from moments 0 & 2), sqrt(m0/m2)

           'Tave':  -- Tm01   Average period, frequency sprectra weighted, from first moment (Tm0,1)

           'Tm10': Mean Absolute wave Period from -1 moment

           'sprdF':  Freq-spec spread (m0*m4 - m2^2)/(m0*m4)  (one definition)

           'Dp':   Peak direction at the peak frequency

           'Dm':   Mean wave direction - vector averaged mean direction, see below
                (http://wis.usace.army.mil/pdf/WIS_OneLine_format_20170406.pdf)

           'Dm2':  Mean wave direction - as above, but using b2,a2

           'Dspec1': mean direction as function of frequency, from arctan(b1/a1)

           'Dspec2': mean direction as function of frequency, from arctan(b2/a2)

           'sprdD':  Directional spread  (one definition, Kuik 1988, buoys), total sea-swell

           'spreadD_kuik_m1': directional spread from circular moments (eq 24)

           'spreadD_kuik_m2': directional spread from circular moments (eq 27)

            "spreadD_f":  [t x Freq] array of spread at each frequency (eq 4b orielly/24 kuik)

            "skewnessD_f: [t x freq] array of skewness at each frequency (eq 4c orielly/25 kuik)

            "kurtosisD_f: [t x freq] array of kurtosis at each frequency (eq 4d orielly/26 kuik)

           'meta': directions to see this help

    References:
        Kuik 1988, "A method for the Routine Analysis of Pitch-and-Roll Buoy Wave Data" Journal of
            Physical Oceanography. Volume 18, p 1020 - 1034.
            https://journals.ametsoc.org/doi/pdf/10.1175/1520-0485%281988%29018%3C1020%3AAMFTRA%3E2.0.CO%3B2

        O'Reilley, W. C, T.H.C Herbers, R. J. Seymour, R. T. Guza, 1996 "A comparison of Directional Buoy and Fixed
            Platform Measurements of Pacific Swell", Journal of Atmospheric and Oceanic Technology. Vol 13, p231 - 238;
            https://journals.ametsoc.org/doi/pdf/10.1175/1520-0426%281996%29013%3C0231%3AACODBA%3E2.0.CO%3B2

        USACE Wave Information Study (WIS) website: http://wis.usace.army.mil/pdf/WIS_OneLine_format_20170406.pdf

    """
    assert type(frqbins) in [np.ndarray, np.ma.MaskedArray], 'the input frqeuency bins must be a numpy array'
    assert type(dirbins) in [np.ndarray, np.ma.MaskedArray], 'the input DIRECTION bins must be a numpy array'
    assert np.array(spec).ndim == 3, 'Spectra must be a 3 dimensional array'
    try:
        assert (spec != 0).all() is not True, 'Spectra must have energy to calculate statistics, all values are 0'
    except AssertionError:
        return 0
    assert spec.shape[1] == frqbins.shape[0], 'The spectra must be dimensioned [t,freq, direciton]'
    assert spec.shape[2] == dirbins.shape[0], 'The spectra must be dimensioned [t,freq, direciton]'
    assert (spec > 0).all(), "spectra have fill values in place, correct spectra before proceeding"
    ####################################################################################################################

    ## bug for non-directional wave spectra
    if dirbins.size == 4:
        raise  NotImplementedError ("there's a bug in here for non-directional 2d spectra calculations")
    frqbins = np.array(frqbins)
    dirbins = np.array(dirbins)

    # finding delta freqeucny (may change as in CDIP spectra)
    df = np.diff(np.append(frqbins[0], frqbins), n=1)
    # finding delta degrees
    dd = np.abs(np.median(np.diff(dirbins)))  # dirbins[2] - dirbins[1]  # assume constant directional bin size
    Drad = np.deg2rad(dirbins)  # making a radian degree bin
    # frequency spec
    fspec = np.sum(spec, axis=2) * dd  # fd spectra - sum across the frequcny bins to leave 1 x n-frqbins


    # doing moments over 0.05 to 0.33 Hz (3-20s waves) (mainly for m4 sake)
    idx = np.argwhere((frqbins >= lowFreq) & (frqbins <=highFreq)).squeeze()

    m0 = np.sum(fspec[:, idx] * df[idx], axis=1)                            # 0th moment
    m1 = np.sum(fspec[:, idx] * df[idx] * frqbins[idx], axis=1)             # 1st moment
    m2 = np.sum(fspec[:, idx] * df[idx] * frqbins[idx] ** 2, axis=1)        # 2nd moment
    # m3 = np.sum(fSpecOut[:, idx] * df[idx] * frqbins[idx] ** 3, axis=1)   # 3rd moment
    m4 = np.sum(fspec[:, idx] * df[idx] * frqbins[idx] ** 4, axis=1)        # 4th moment
    m11 = np.sum(fspec[:, idx] * df[idx] * frqbins[idx] ** -1, axis=1)      # negitive one moment

    # sigwave height
    Hm0 = 4 * np.sqrt(m0)
    # period stuff
    ipf = fspec.argmax(axis=1)           # index of max frequency
    Tp = 1 / frqbins[ipf]                # peak period
    Tm02 = np.sqrt(m0 / m2)              # mean period
    Tm01 = m0 / m1                       # average period - comparible to TS Tm
    Tm10 = m11 / m0
    # f-spec spread
    sprdF = np.sqrt((m0 * m4 - m2 ** 2) / (m0 * m4))
    ############### directional REDO ######### #    #  ####################################
    angMat = np.tile(Drad, (len(frqbins), 1))   # angle array, directions for each frequency
    # normalized direction spectra (per deg)
    Ds_, DmrArr = np.ones_like(spec) * 1e-6, np.ones_like(spec) *1e-6
    a1_, a2_, b1_, b2_ = np.ma.empty_like(fspec), np.ma.empty_like(fspec), np.ma.empty_like(fspec), np.ma.empty_like(fspec)   # initialize
    for i in range(spec.shape[0]):  # loop through, there's probably a faster way to do this
        Ds_[i] = spec[i]/np.tile(fspec[i], [len(dirbins), 1]).T
        ## calculate a's and b's from 2D spectra
        a1_[i] = (np.cos(angMat) * Ds_[i]).sum(axis=1) * dd      # a1(f)
        b1_[i] = (np.sin(angMat) * Ds_[i]).sum(axis=1) * dd      # b1(f)
        a2_[i] = (np.cos(2 * angMat) * Ds_[i]).sum(axis=1) * dd  # a2(f)
        b2_[i] = (np.sin(2 * angMat) * Ds_[i]).sum(axis=1) * dd  # a2(f)

    # mean directions as a function of frequency  (in Degrees)
    Dspec = np.mod(np.rad2deg(np.arctan2(b1_, a1_)), 360)
    Dspec2 = np.mod(np.rad2deg(np.arctan2(b2_, a2_))/2, 180)

    #circular Moments Kuik '88
    # for r in range(Dspec.shape[0]):                             # looping, but should be faster way to do it with tile
    #     DmrArr[r] = np.tile(np.deg2rad(Dspec[r]), (len(dirbins) , 1)).T
    # model free directional parameters (o'reiley 1996)/circular moments kuik 88
    m1_c = np.sqrt(a1_ **2 + b1_**2)
    m2_c = a2_*np.cos(2*np.deg2rad(Dspec)) + b2_*np.sin(2*np.deg2rad(Dspec))
    n2_c = b2_*np.cos(2*np.deg2rad(Dspec)) - a2_*np.sin(2*np.deg2rad(Dspec))


    # Frequency integrated a/bs
    a1b = (a1_[:, idx] * fspec[:, idx] * df[idx]).sum(axis=1)/m0
    b1b = (b1_[:, idx] * fspec[:, idx] * df[idx]).sum(axis=1)/m0
    a2b = (a2_[:, idx] * fspec[:, idx] * df[idx]).sum(axis=1)/m0
    b2b = (b2_[:, idx] * fspec[:, idx] * df[idx]).sum(axis=1)/m0

    # mean wave angle, energy integrated, calculated from a's and b's
    Dm_ = np.mod(np.rad2deg( np.arctan2(b1b, a1b)), 360)                # off by about 5 from kent's matlab scripts
    Dm2_ = np.mod(0.5 * np.rad2deg(np.arctan2(b2b, a2b)), 360)
    Dp = dirbins[np.argmax(spec.sum(axis=1), axis=1)]
    # calculate mean direction from only a/b info (no moments)
    # weights = fspec.T/fspec.max(axis=1).T
    # dm_rad = np.arctan2(b1_*weights, a1_*weights).sum(axis=1)
    # dm_deg = np.mod(np.rad2deg(dm_rad), 360)
    # np.mod(np.rad2deg(np.arctan2((b1_ * fspec), (a1_ * fspec))), 360)
    # Dm_ab = (Dspec * fspec).sum(axis=1)/dd


    # Directional Spreads
    sprdD =        np.rad2deg(np.sqrt(2 * (1-np.sqrt(a1b**2 + b1b**2))))       # integrated spread across all freqs
    sprdD_kuikm1 = np.rad2deg(np.sqrt(2 * (1-m1)   ))                # spread at peak eq 24 kuik '88
    sprdD_kuikm2 = np.rad2deg(np.sqrt(    (1-m2)/2 ))                # spread at peak eq 27 kuik '88

    # frequency dependant spread, skewness, asymetry characteristics
    spreadD_f = np.rad2deg(np.sqrt(2*(1-m1_c)))
    skewnessD_f = -n2_c/ ((1-m2_c/2)**(3/2))
    # kurtosisD_f = 6 - 8*m1_c + 2*m2_c/(2*(1-m1))*2

    meta = 'See help on this function for explanation of output'
    stats = {'Hm0': Hm0,
             'Tp': Tp,
             'Tm': Tm02,
             'Tave': Tm01,
             'Tm10': Tm10,
             'Dp': Dp,
             'Dm': Dm_,
             'Dm2': Dm2_,
             'Dspec1': Dspec,
             'Dspec2': Dspec2,
             'spreadF': sprdF,
             'spreadD': sprdD,
             'spreadDP_m1': sprdD_kuikm1,
             'spreadDP_m2': sprdD_kuikm2,
             "spreadD_f": spreadD_f,
             "skewnessD_f": skewnessD_f,
             # "kurtosisD_f": kurtosisD_f,
             'meta': meta}

    return stats

def fSpecPeaksValleys(spec1d, wavefreqbin):
    """This function takes a 1 dimensional frequency spectra and finds indicies of spectral peaks
        and valleys (ideally used to seperate different swell componants) ... not pollished

    Args:
      spec1d: 1 d frequency spectra
      plotfname: file name for figure to be made
      wavefreqbin: returns: peakindexes, valley indexes

    Returns:
      peakindexes, valley indexes

    """
    # import peakutils
    # from scipy import signal
    # # first smooth the spectra to find appropriate peaks
    # # smoothSpec1d = signal.savgol_filter(spec1d, window_length=5, polyorder=2)  # smoothing the spectra
    # smoothSpec1d = spec1d
    # mindist = 3  # this is the minimum number of bins between peaks to be identified
    # threshold = 0.3  # normalized peak threshold
    # peakIdxs = np.squeeze(signal.argrelmax(smoothSpec1d, order=mindist))

    # find indicies of peaks
    # peakIdxs = peakutils.indexes(smoothSpec1d, thres=threshold, min_dist=mindist)

    import sys
    sys.path.append('/home/spike/repos/peakdetect')
    import peakdetect  # https://gist.github.com/sixtenbe/1178136
    lookahead = 3  # len(spec1d) / 15
    delta = 0.08  # minimum difference between a peak and a valley
    peakIdxs, valIdxs = peakdetect.peakdetect(spec1d, wavefreqbin, lookahead=lookahead, delta=delta)

    #
    # # are there more than one peak in the spectra
    # if len(peakIdxs) == 1:  # there's only one frequency in the spectra
    #     valIdxs = None
    # else:  # find the valleys for associated peaks
    #     valIdxs = [] # np.zeros(len(peakIdxs)-1, dtype=int)  # valley indicies
    #     deleteThese = []
    #     for ii in range(0,len(peakIdxs)-1):
    #         neworder = 1
    #         comp = np.squeeze(signal.argrelmin(smoothSpec1d[peakIdxs[ii]:peakIdxs[ii+1]], order=neworder))
    #         while np.size(comp) > 1:  # find 1 valley between 2 peaks
    #             neworder += 1 # increase the order until one valley is found
    #             comp = np.squeeze(signal.argrelmin(smoothSpec1d[peakIdxs[ii]:peakIdxs[ii+1]], order=neworder))
    #             if neworder > 10:
    #                 raise OverflowError, 'bad solution to finding peak'
    #         if np.size(comp) == 0:
    #             deleteThese.append(ii + 1)
    #         else:
    #             valIdxs.append(comp + peakIdxs[ii]) # valley indices are relative to peaks
    #     # remove bad found peaks
    #     peakIdxs = np.delete(peakIdxs, deleteThese)
    #

    ################################################################
    # # begin QA QC for peak Check

    if len(peakIdxs) == 0:  # if no peaks were found (small wave conditions )
        peakIdxs = [[wavefreqbin[np.argmax(spec1d)], spec1d[np.argmax(spec1d)]]]
    elif len(peakIdxs) == len(valIdxs):
        valIdxs.remove(valIdxs[-1])  # remove last valley found, should be odd number
    # # first check for half power
    #     deletedPeaks = []  # deleted indices that don't meet half power criterai
    #     for ff in range(len(peakIdxs)-1):
    #         print 'checking the peaks'
    #         val = spec1d[valIdxs[ff]]    # energy at the valley
    #         peak = spec1d[peakIdxs[ff]]  # energy at the peak
    #         if peak/2 < val:  # if valley is larger than half peak energy delete it
    #             deletedPeaks.append(ff)
    #         # if peak
    # now delete all selected peaks
    # peakIdxs = np.delete(peakIdxs, deletedPeaks)
    # valIdxs = np.delete(valIdxs, deletedPeaks)
    # if len(peakIdxs) > 3:
    #     print 'Too Many Peaks Found!!!'

    ################################################################
    # plot solution
    # if plotfname != None:
    #     plt.figure()
    #     plt.subplot(211)
    #     plt.plot(wavefreqbin, spec1d, label='Spectra')
    #     # plt.plot(wavefreqbin, smoothSpec1d, label='Smoothed')
    #     for idx in peakIdxs:
    #         plt.plot(idx[0], idx[1], 'rd', label='peaks')
    #     for idx in valIdxs:
    #         plt.plot(idx[0], idx[1], 'go', label='valleys' )
    #     plt.ylabel('Energy $m^2/Hz$')
    #     plt.legend()
    #     plt.subplot(212)
    #     plt.plot(wavefreqbin, dspec)
    #     for idx in peakIdxs:
    #         plt.plot(idx[0], dspec[np.squeeze(np.argwhere(idx[0] == wavefreqbin))], 'rd', label='peaks')
    #     plt.ylabel('Direction [deg TN]')
    #     plt.savefig(plotfname)
    #     plt.close()
    return peakIdxs, valIdxs

def findTp( spec, wavefreqbin):
    """This function finds the Tp of a spectra

    Args:
      spec: 2(no time) or 3  dimensional spectrum [t, freq, dir]
      wavefreqbin: takes both freq bin or period bin

    Returns:
      array of Tp

    """
    try:
        assert spec.ndim == 3, 'This function assumes a 3 dimensional spectrum [t, freq, dir]'
    except AssertionError:
        spec = np.expand_dims(spec, axis=0)
    assert wavefreqbin.shape[0] == spec.shape[1], 'This function expects frequency in the 2nd dimension'

    fspec = np.sum(spec, axis=2)  # frequency spec
    freqIdx = np.argmax(fspec, axis=1)  # finding the freq/period of max energy
    fOut = wavefreqbin[freqIdx]  # associating the ind with the freq/period

    return fOut

def findDpAtTp( spec, wavedirbin):
    """finds the peak direction at peak frequency

    Args:
      spec: 2 dimensional spectra, dimensioned [time, freq, direction]
      wavedirbin: directions associated with spectra (= third dimension)

    Returns:
      array
      Peak direction at peak frequency

    """
    try:
        assert spec.ndim == 3, 'This function assumes a 3 dimensional spectrum [t, freq, dir]'
    except AssertionError:
        spec = np.expand_dims(spec, axis=0)  # mkaind 3 dimensions
    assert wavedirbin.shape[0] == spec.shape[2], 'This function expects direction as the 3rd dim'
    TpIdx = np.argmax(spec.sum(axis=2), axis=1)  # finding the Peak period Idx
    DpOut = np.zeros_like(TpIdx)
    for tt in range(TpIdx.shape[0]):
        DpOut[tt] = wavedirbin[np.argmax(spec[tt, TpIdx[tt], :])]  # finding the max idx for each time

    return DpOut

def findPeakDirs( spec, dirBin):
    """in single (or multiple) 2d spectra, this will find the peak direction for every frequency

    Args:
      spec: spectra in 3 dim (time, freq, dir)
      freqBin: frequency bin associated with 2nd dimension of spec
      dirBin: directions associated with 3rd dimension of spec

    Returns:
      directions of len ([t], freqbin)
      eg. for every frequency a direction is returned

    """
    peakDirs = np.zeros((spec.shape[0], spec.shape[1]))
    for t in range(spec.shape[0]):  # looping over time
        for idx in range(spec.shape[1]):  # looping over frequencies
            peakDirs[t, idx] = dirBin[np.argmax(spec[t, idx, :])]  # picking max direction for each frequency
    # for every frequency a direction returned
    return peakDirs

def findPeakFreq2Dspec(spec, dirBin):
    """in single (or multiple) 2d spectra, this will find the peak frequency for every direction

    Args:
      spec: spectra in 3 dim (time, freq, dir)
      freqBin: frequency bin associated with 2nd dimension of spec
      dirBin: directions associated with 3rd dimension of spec

    Returns:
      directions of len ([t], dirbin)
      eg. for every direction  a frequency is returned

    """
    peakFreqs = np.zeros((spec.shape[0], spec.shape[2]))
    for t in range(spec.shape[0]):  # looping over time
        for idx in range(spec.shape[1]):  # looping over directions
            peakFreqs[t, idx] = dirBin[np.argmax(spec[t, :, idx])]  # picking max frequency for each direction
    # for every frequency a direction returned
    return peakFreqs

def isThisWindSea(waveDirectionAtPeak, waveSpeedAtPeak, windDir, windSpeed):
    """This function will check the wave direction and the wind direction.  It will do a comparison between the two
        if the wind is within +/- 45 degrees of the wave direction, and the wind is faster than the wave speed,
        it will be returned True, for wind Sea

    Args:
      waveDirectionAtPeak: This is a wave direction in degrees (must be same coordinate sys as wind dir)
      waveSpeedAtPeak: This is speed of wave at peak (speed must be same units as wind Dir)
      windDir: this is wind Direction (time matched to Wave direction)
      windSpeed: this is wind speed, Time matched to wave Direction

    Returns:
      True or False value

    """
    windowAngle = 45
    windAngleMax = anglesLib.angle_correct(windDir + windowAngle)
    windAngleMin = anglesLib.angle_correct(windDir - windowAngle)
    # if there is no wrap
    windSea = False  # setting
    if waveSpeedAtPeak <= windSpeed:  # if speeds match up
        if (windDir > 360 - windowAngle) and ((360 > waveDirectionAtPeak >= windAngleMin) or (
                        0 <= waveDirectionAtPeak <= windAngleMax)):  # wind window wraps above 360
            # upper bound: wave angle has to be between the 360 and the lower bound angle direction limit
            # lower bound: wave angle has to be above the wind upper bound direction limit
            windSea = True
        elif (windDir < windowAngle) and ((0 <= waveDirectionAtPeak <= windAngleMax) or (
                        windAngleMin < waveDirectionAtPeak <= 360)):  # wind window wraps below 0
            # upper bound: the wave angle is smaller than the upper bound wind angle
            # lower bound (with wrap around 360): wave direction is either greater than zero and upper bound wind direction limit
            #   or wave direction is between the lower bound wind direction and 360
            windSea = True
        elif (waveDirectionAtPeak > windAngleMin) and (
                    waveDirectionAtPeak < windAngleMax):  # if angles match up with no wrap
            windSea = True

    return windSea

def findidxSeaSwell(spec1d, dspec, wavefreqbin, windSpeed, windDir, depth, plotfname=None):
    """This function separates sea and swell starting with the 1d frequency spectra and the 1d directional spectra

    Args:
      spec1d: 1 d frequency spectrum
      wavefreqbin: frequency spectrum associated with wave
      dspec: 1d directional spectrum (arctan(b1,a1))
      waveDirectionAtPeak: the direction of the wave from
      plotfname: return: an index corresponding to (Default value = None)
      windSpeed: param windDir:
      depth: returns: an index corresponding to
      windDir:

    Returns:
      an index corresponding to

    """
    # body of function
    assert (dspec >= 0).all(), 'please correct wave angles between 0 and 360'
    assert len(windDir) == spec1d.shape[0], 'Wind records are not the same length as the frequnecy spectra'
    spec1d = np.expand_dims(spec1d, axis=0) if spec1d.ndim == 1 else spec1d  # expanding dims as necessicary
    dspec = np.expand_dims(dspec, axis=0) if dspec.ndim == 1 else dspec  # expanding the dimesnions is correct
    # loop through how ever many spectra there are
    outidxs = []  # initialization out output
    for i in range(spec1d.shape[0]):
        swellfspec, seafspec = np.ones_like(spec1d) * 1e-6, np.ones_like(spec1d) * 1e-6
        peaks, valleys = fSpecPeaksValleys(spec1d[i], wavefreqbin)  # finding peaks and valleys in fspec
        if valleys == None or len(valleys) == 0:  # there are not 2 wave system componants in the spectra
            waveDirectionAtPeak = dspec[i, np.argwhere(peaks[0][0] == wavefreqbin).squeeze()]
            _, waveSpeedAtPeak, _ = dispersion(depth.squeeze(), 1 / peaks[0][0])
            # find out whether it's sea or swell, (wave direction vs wind direction +/- 45) and log it appropriately
            isit = isThisWindSea(waveDirectionAtPeak, waveSpeedAtPeak, windDir=windDir[i], windSpeed=windSpeed[i])
            if isit == True:
                # this is sea
                idx2separate = 0  # this is wind Sea
            else:
                idx2separate = -1  # ththis is swell
            waveDirectionAtPeak = [waveDirectionAtPeak]
        else:
            # seperate through sea and swell
            waveDirectionAtPeak = []  # initialization
            for ii in range(len(peaks)):  # looping though peaks finding wave direction at each
                waveDirectionAtPeak.append(dspec[i, np.argwhere(peaks[ii][0] == wavefreqbin).squeeze()])
            for ii in range(len(peaks)):  # looping through each valley starting at
                # waveDirectionAtPeak= dspec[np.argwhere(peaks[ii][0] == wavefreqbin).squeeze()]  #
                _, waveSpeedAtPeak, _ = dispersion(depth.squeeze(), 1 / peaks[ii][0])
                isit = isThisWindSea(waveDirectionAtPeak[ii], waveSpeedAtPeak, windDir=windDir[i],
                                          windSpeed=windSpeed[i])
                if isit == True:
                    # its windsea, pick the index and don't go any further
                    idx2separate = np.argwhere(valleys[ii - 1][0] == wavefreqbin).squeeze()  # separation frequency
                    break
                # if isit is False, then we have swell, move to the next peak to find sea
                else:
                    idx2separate = -1  # this is swell
        if plotfname != None:

            if waveSpeedAtPeak > windSpeed[i]:
                title = 'waveSpeed > windSpeed - Swell %s' % plotfname[i].split('/')[-1][5:-1]
            elif waveSpeedAtPeak <= windSpeed[i]:
                title = 'waveSpeed <= windSpeed - MaybeSea %s' % plotfname[i].split('/')[-1][5:-1]

            print(plotfname[i].split('/')[-1][5:-1])
            plt.figure()
            plt.suptitle(title)
            plt.subplot(211)
            plt.plot(wavefreqbin, spec1d[i], label='Frequency Spectra')
            # plt.plot(wavefreqbin, smoothSpec1d, label='Smoothed')
            for idx in peaks:
                plt.plot(idx[0], idx[1], 'gx')
            for idx in valleys:
                plt.plot(idx[0], idx[1], 'gx')
            plt.plot(wavefreqbin[idx2separate], spec1d[i, idx2separate], 'rd', label='wave separation frequanc6y')
            plt.ylabel('Energy $m^2/Hz$')
            plt.legend()
            plt.subplot(212)
            plt.plot(wavefreqbin, dspec[i])
            plt.plot([wavefreqbin[0], wavefreqbin[-1]], [windDir[i], windDir[i]], '--', label='Wind Direction')
            plt.plot(wavefreqbin[idx2separate], dspec[i, idx2separate], 'rd', label='Separation Point')
            for ii in range(len(peaks)):
                plt.plot(peaks[ii][0], waveDirectionAtPeak[ii], 'gx')
                plt.text(peaks[ii][0], waveDirectionAtPeak[ii], '  diff = %i' % min(
                    360 - np.abs(waveDirectionAtPeak[ii] - windDir[i]), np.abs(waveDirectionAtPeak[ii] - windDir[i])))
            plt.ylabel('Direction [deg TN]')
            plt.xlabel('Wave Frequency')
            plt.legend()
            plt.savefig(plotfname[i])
            plt.close()

        #
        # swellfspec[:idx2separate] = spec1d[:idx2separate]
        # seafspec[idx2separate:] = spec1d[idx2separate:]
        # Sea.append(seafspec)
        # Swell.append(swellfspec)
        outidxs.append(idx2separate)
    return outidxs

def decompose2Dspec(spec, wavefreqbin):
    """
    This function is still under development, its supposed to take input of a 2D spectra and decompose to fourier
    coefficeints

    Args:
        spec:
        wavefreqbin:

    Returns:

    """

    fspec = spec.sum(axis=-1)  # integrating across all directions

    a1, b1 = np.zeros_like(fspec), np.zeros_like(fspec)
    for freq in wavefreqbin:
        a1 = np.arccos(fspec)

        b1 = np.arcsin(fspec)

def seaAndSwell2D(specTime, spec, wavefreqbin, wavedirbin, windSpeed, windDirTn, plot=False, depth=26):
    """This function will make sea and swell spectra given the below variables.  The wind Directions must be in the same
    coordinate system as the wave spectra (including wave direction bins)
    ... still under development

    Args:
      specTime: this is a time stamp for the data dimensioned by [time]
      spec: this is the spectral wave energy data dimensioned by [time, wave direction, wave frequency]
      wavefreqbin: this are the frequencies associated with the spectral wave data
      wavedirbin: these are the direction bins associated with the spectra, same angle convention and
      windSpeed: the speed of the wind
      windDirTn: the wind direction of the
      depth: depth is assumed to be 26 meter wave rider (Default value = 26)
      plot (bool): Turn QA plots on or off (Default value = False)

    Returns:
      sea, swell spectra the same size as the input spectra

    """
    assert specTime.shape[0] == spec.shape[0], " data doesn't line up, try using winds from model"
    assert specTime.shape[0] == windSpeed.shape[0], "time must match between wind and wave data"
    angleWindow = 45  # this is the wind window +/-
    # 1  input periods into dispersion relationship  # get back speeds for each frequency
    _, wavespeeds, _ = dispersion(depth, 1 / wavefreqbin)

    # 2  find peak directions for each frequency band
    peakDirsTN = findPeakDirs(spec=spec, dirBin=wavedirbin)

    # 3 now seperate
    swellSea, windSea = np.ones_like(spec) * 1e-6, np.ones_like(spec) * 1e-6
    for tt in range(specTime.shape[0]):
        for ff in range(wavefreqbin.shape[0]):  # loop through frequency bin
            if ff in range(wavefreqbin.shape[0])[-3:]:
                windSea[tt, ff, :] = spec[tt, ff, :]
            if (windDirTn[tt] + angleWindow >= 360):  # if the upper bound of wind direction wraps to upper directions
                # upper bound: wave angle has to be between the 360 and the lower bound angle direction limit
                # lower bound: wave angle has to be above the wind upper bound direction limit
                if (0 <= peakDirsTN[tt, ff] <= anglesLib.angle_correct(windDirTn[tt] + angleWindow)) | (
                                360 > peakDirsTN[tt, ff] >= windDirTn[tt] - angleWindow):
                    if windSpeed[tt] > wavespeeds[ff]:
                        # the wind is positively reinforcing wave generation --> Sea
                        windSea[tt, ff, :] = spec[tt, ff, :]
                    else:
                        swellSea[tt, ff, :] = spec[tt, ff, :]
                else:
                    swellSea[tt, ff, :] = spec[tt, ff, :]
            elif (windDirTn[tt] - 45 < 0):  # if the lower bound of wind direction wraps to negative directions
                # upper bound: the wave angle is smaller than the upper bound wind angle
                # lower bound (with wrap around 360): wave direction is either greater than zero and upper bound wind direction limit
                #   or wave direction is between the lower bound wind direction and 360
                if (0 <= peakDirsTN[tt, ff] <= anglesLib.angle_correct(windDirTn[tt] + angleWindow)) | (
                        anglesLib.angle_correct(windDirTn[tt] - angleWindow) <= peakDirsTN[tt, ff] < 360):
                    if windSpeed[tt] > wavespeeds[ff]:
                        # the wind is positively reinforcing wave generation --> Sea
                        windSea[tt, ff, :] = spec[tt, ff, :]
                    else:
                        swellSea[tt, ff, :] = spec[tt, ff, :]
                else:
                    swellSea[tt, ff, :] = spec[tt, ff, :]
            # if wind direction bounds do not wrap0
            elif (peakDirsTN[tt, ff] <= windDirTn[tt] + angleWindow) & (
                        peakDirsTN[tt, ff] >= windDirTn[tt] - angleWindow):
                # the speeds are worth checking because they are within 45 degrees of the wave propagation
                if windSpeed[tt] > wavespeeds[ff]:
                    # the wind is positively reinforcing wave generation --> Sea
                    windSea[tt, ff, :] = spec[tt, ff, :]
                else:
                    swellSea[tt, ff, :] = spec[tt, ff, :]
            else:
                # the wind direction is not reinforcing the wave direction
                swellSea[tt, ff, :] = spec[tt, ff, :]

        if plot == True:
            from matplotlib import pyplot as plt

            cbarMin = np.min(spec[tt])
            cbarMax = np.max(spec[tt])
            fname = 'figures/SeaSwellcompare_%s.png' % specTime[tt].strftime('%Y%m%dT%H%M%SZ')
            plt.figure(figsize=(12, 12))
            plt.suptitle('Swell And Sea Seperator \n %s' % (specTime[tt].strftime('%Y%m%dT%H%M%SZ')))

            plt.subplot(221)
            plt.title('Total spectra')
            plt.ylabel('wave Direction')
            plt.xlabel('wave Frequency')
            plt.pcolor(wavefreqbin, wavedirbin, spec[tt].T)
            plt.plot(wavefreqbin, peakDirsTN[tt], 'w.-', label='peak wave Direction')
            plt.plot(wavefreqbin, np.tile(anglesLib.angle_correct(windDirTn[tt] + angleWindow), len(wavefreqbin)), 'w--')
            plt.plot(wavefreqbin, np.tile(anglesLib.angle_correct(windDirTn[tt] - angleWindow), len(wavefreqbin)), 'w--')
            plt.plot([0, 0.5], [windDirTn[tt], windDirTn[tt]], 'w-', label='Wind direction')
            # plt.legend(loc='upper right')

            ax1 = plt.subplot(222)
            plt.title('wind and wave speeds')
            plt.xlabel('wave Frequency')
            plt.plot(wavefreqbin, wavespeeds, 'b-', label='wavespeed')
            plt.plot(wavefreqbin, np.tile(windSpeed[tt], len(wavefreqbin)), 'k-', label='Windspeed +')
            ax1.set_ylabel('along wind Componant of WaveSpeed', color='b')
            ax1.text(.2, (windSpeed[tt] + 2) / 2, 'Wind Sea')
            ax1.text(.2, (windSpeed[tt] + 2), 'Swell Sea')
            ax1.legend(loc='best')

            plt.subplot(223)
            plt.title('WindSea')
            plt.pcolor(wavefreqbin, wavedirbin, windSea[tt].T)  # , vmin=cbarMin, vmax=cbarMax)
            plt.ylabel('wave Direction')
            plt.xlabel('wave Frequency')
            plt.colorbar()

            plt.subplot(224)
            plt.title('Swell Sea')
            plt.pcolor(wavefreqbin, wavedirbin, swellSea[tt].T, vmin=cbarMin, vmax=cbarMax)
            plt.ylabel('wave Direction')
            plt.xlabel('wave Frequency')
            plt.colorbar()

            plt.tight_layout(pad=.1, rect=[.03, .03, .95, .9])
            plt.savefig(fname)
            plt.close()

    return windSea, swellSea

def seaAndSwell1D(spec, wavefreqbin, truncate=0.1):
    """this function will take a 1 d spectra

    Args:
      spec: 1 d spectra, can be single or dimensioned [time, frequency
      wavefreqbin: associated wave frequency with frequency
      truncate: value used in truncating the spectra between sea/swell (the valley location) (Default value = 0.1)
      windSea: the wind sea portion of the spectra
      swellSea: low frequency portion of the spectra associate with swell

    Returns:
      param windSea:  the wind sea portion of the spectra

    """
    assert spec.shape[-1] == len(wavefreqbin), '1D stats need a 1 d spectra'
    fspec = spec

    # 3 now seperate
    swellSea, windSea = np.ones_like(fspec) * 1e-6, np.ones_like(fspec) * 1e-6

    idx = np.argmax(wavefreqbin >= truncate)

    if fspec.ndim == 1:
        windSea[idx:] = fspec[idx:]
        swellSea[:idx] = fspec[:idx]
    else:
        windSea[:, idx:] = fspec[:, idx:]
        swellSea[:, :idx] = fspec[:, :idx]

    return windSea, swellSea