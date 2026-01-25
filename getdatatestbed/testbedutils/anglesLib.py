import math, warnings
import numpy as np


def cart2pol(x, y):
    """this translates from cartesian coords to polar coordinates (radians)

    Args:
      x: x componant
      y: y componant

    Returns:
        r radial componant
        theta angular compoanat (returned in radian)

    """
    r = np.sqrt(x ** 2 + y ** 2)
    theta = np.arctan2(y, x)
    return r, theta

def pol2cart(r, theta):
    """this translates from polar coords (radians) to polar coordinates
    assumed radian input for theta

    Args:
      r: speed, magnatude
      theta: direction (in radians)

    Returns:
       x - componant
       y - componant

    """
    if (np.max(theta) > 2 * np.pi).any():
        print('Warning polar2cart assumes radian direction in, angles found above 2pi')
    x = r * np.cos(theta)
    y = r * np.sin(theta)
    return x, y

def geo2STWangle(geo_angle_in, zeroAngle=70., METin=1, fixanglesout=0):
    """This rotates an angle (angle_in) from geographic Meterological convention 0= True North
    and puts it to an STWAVE angle 0 is onshore
    variable pierang is the angle from shore to 90 degrees (shore coordinates) in geographic convention
    ie the pier at Duck NC is at an angle of 70 degrees TN (stateplane) and this is assumed to be shore perpendicular

    Args:
      geo_angle_in: an array or list of angles to be rotated from MET convention of angle from
      zeroAngle: the angle of the pier, from this the azimuth is calculated (MET CONVENTION) (Default value = 70.)
      METin: 1 if the input angle is in MET convention (angle from) (Default value = 1)
      fixanglesout: if set to 1, will correct out angles to +/-180 (Default value = 0)

    Returns:
      angle_out corrected angle back out, into cartesian space

    """
    # assert len(np.shape(geo_angle_in)) <= 1, 'function geo2STWangle not tested in more than 1 dimension'
    azimuth = 270 - zeroAngle  # the control of the zero for rotation of the grid in TN coords
    geo_angle_in = np.array(geo_angle_in, dtype=float)  # making sure floating calcs are used
    if METin == 1:  # flip the from/to convention
        ocean_angle_in = angle_correct(geo_angle_in + 180)  # to 'ocean' from 'MET' convention
    else:
        ocean_angle_in = geo_angle_in
    rotate = angle_correct(90 - azimuth)  # moving geo
    STWangle = angle_correct(rotate - ocean_angle_in)  # rotation of angles to grid convention
    #  putting into +/- 180 degrees
    if fixanglesout == 1:
        flip = np.argwhere(STWangle > 180)  # indicies that need to be flipped
        STWangle[flip] -= 360
    return STWangle

def STWangle2geo(STWangle, pierang=70, METout=1):
    """This is the complementary function to geo2STWangle,  It takes STWAVE angles (local coordinate system with a towards
     definition and + CCW)
    and translates them into geospatial grid angles (with a MET -from- convention and a CW+ convention)

    Args:
      gridangle: an array or list of angles to be rotated
      pierang: the (MET CONVENTION) (Default value = 70)
      METout: if left 1, this creates output into a MET conveinton with the definition in the from (Default value = 1)
      STWangle: returns: angle_out array of angles returned back to geographic convention (true north, clockwise positive)

    Returns:
      angle_out array of angles returned back to geographic convention (true north, clockwise positive)

    """
    # TODO this needs to be renamed
    assert len(np.shape(STWangle)) <= 3, 'STWangle2geo has not been tested in greater than 3dimensions'
    azimuth = 270 - pierang  # rotation of the Grid in local coordinate
    rotate = angle_correct(90 - azimuth)  # putting azimuth into ocean (towards) convention
    angle_out = rotate - STWangle
    if METout == 1:
        angle_out += 180
    angle_out = angle_correct(angle_out)  # correcting to < +360
    return angle_out

def vectorRotation(vector, theta=90, axis='z'):
    """This function does a vector rotation of the vector input in vector, rotated by theta
    NO NO NO NO -> +theta results in clockwise rotation!!!!!

    Args:
      vector: 2d or 3d vector you want rotated... [x, y, z]
      axis: axis you want it rotated about 'x' = [1, 0, 0], 'y' = [0, 1, 0], 'z' = [0, 0, 1] (Default value = 'z')
      theta: angle in decimal degrees (Default value = 90)

    Returns:
      vector rotated clockwise theta degrees about axis, uses Euler-Rodrigues formula

    """

    vector = np.asarray(vector)
    assert -360 <= theta <= 360, 'your angle must be a decimal degree value -360  and 360 degrees'
    assert len(vector) >= 2, "You must hand this function a 2D or 3D vector!"
    assert len(vector) <= 3, "You must hand this function a 2D or 3D vector!"

    if len(vector) == 2:
        vector = np.append(vector, 0)  # this just converts it to a 3D vector
        ret = '2d'
    else:
        ret = '3d'

    if type(axis) == str:
        assert axis in ['x', 'y', 'z'], 'Acceptable axis inputs are x, y, z, or a 3D vector'

        if axis == 'x':
            axis = [1, 0, 0]
        elif axis == 'y':
            axis = [0, 1, 0]
        elif axis == 'z':
            axis = [0, 0, 1]
        else:
            pass
        axis = np.asarray(axis)
    else:
        axis = np.asarray(axis)
        assert len(axis) == 3, 'Acceptable axis inputs are x, y, z, or a 3D vector'

    theta = 2*math.pi*(theta/360.0)
    axis = axis / math.sqrt(np.dot(axis, axis))
    a = math.cos(theta / 2.0)
    b, c, d = -axis * math.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    r_mat = np.array([[aa + bb - cc - dd, 2 * (bc + ad), 2 * (bd - ac)],
                     [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])

    r_vector = np.dot(r_mat, vector)

    if ret == '3d':
        return r_vector
    else:
        return r_vector[0:2]

def angle_correct(angle_in, rad=False):
    """this function takes angles in that are both positve and negative
    and corrects them to posivitve only

    Args:
      angle_in: param rad: radian =0 input angles are in degrees
      rad (bool): input anglesa are in radian (Default value = False)


    Returns:
      array of corrected angles in

    """
    angle_in = np.array(angle_in)
    try:
        assert (angle_in == 0).all() is not True, 'All of the Angles are 0, cannot correct'
    except AssertionError:
        return angle_in
    if rad == 0:
        if (angle_in == 0).all():
            warnings.warn('WARNING - Correcting angles of Zero')
        elif (np.abs(angle_in) < 2 * np.pi).all():
            warnings.warn(' WARNING angles are all < 2Pi , ensure that angles are in degrees not radians')

        shape = np.shape(angle_in)
        if len(shape) == 0:
            posmask = angle_in >= 360
            negmask = angle_in < 0
            while negmask.any() or posmask.any():
                if negmask.any() == True:
                    angle_in += 360
                elif posmask.any() == True:
                    angle_in -= 360
                posmask = angle_in >= 360
                negmask = angle_in < 0
        if len(shape) == 1:
            posmask = angle_in >= 360
            negmask = angle_in < 0
            while negmask.any() or posmask.any():
                if negmask.any():  # filter negs out
                    idxneg = np.where(negmask)
                    angle_in[idxneg] += 360
                if posmask.any():  # filter overly positives out
                    idxpos = np.where(posmask)
                    angle_in[idxpos] -= 360
                posmask = angle_in >= 360
                negmask = angle_in < 0
        elif len(shape) == 2:
            for ii in range(0, np.size(angle_in, axis=0)):
                angle_in_2 = np.zeros((np.size(angle_in[ii, :])))  # initializing
                angle_in_2 = angle_in[ii, :]  # taking small chunk 1D array
                posmask = angle_in_2 >= 360  # seeing what's over 360
                negmask = angle_in_2 < 0  # seeing what's under 0
                while negmask.any() or posmask.any():
                    if negmask.any():  # filter negs out
                        idxneg = np.where(negmask)  # finding ids of where
                        if np.size(angle_in_2) == 1 and negmask == True:  # if there's only 1 instance
                            angle_in_2 += 360
                        else:
                            angle_in_2[idxneg] += 360
                    if posmask.any():  # filter overly positives out
                        idxpos = np.where(posmask)
                        if np.size(angle_in_2) == 1 and posmask == True:
                            angle_in_2 -= 360
                        else:
                            angle_in_2[idxpos] -= 360
                    posmask = angle_in_2 >= 360
                    negmask = angle_in_2 < 0
                angle_in[ii, :] = angle_in_2

        elif len(shape) == 3:
            for yy in range(0, np.size(angle_in, axis=1)):
                angle_in_3 = np.zeros(np.size(angle_in, axis=1))
                angle_in_3 = angle_in[:, yy, :]
                for ii in range(0, np.size(angle_in, axis=0)):
                    angle_in_2 = np.zeros((np.size(angle_in_3[ii, :])))  # initializing
                    angle_in_2 = angle_in_3[ii, :]  # taking small chunk 1D array
                    posmask = angle_in_2 >= 360  # seeing what's over 360
                    negmask = angle_in_2 < 0  # seeing what's under 0
                    while negmask.any() or posmask.any():
                        if negmask.any():  # filter negs out
                            idxneg = np.where(negmask)  # finding ids of where
                            if np.size(angle_in_2) == 1 and negmask == True:  # if there's only 1 instance
                                angle_in_2 += 360
                            else:
                                angle_in_2[idxneg] += 360
                        if posmask.any():  # filter overly positives out
                            idxpos = np.where(posmask)
                            if np.size(angle_in_2) == 1 and posmask == True:
                                angle_in_2 -= 360
                            else:
                                angle_in_2[idxpos] -= 360
                        posmask = angle_in_2 >= 360
                        negmask = angle_in_2 < 0
                    angle_in_3[ii, :] = angle_in_2
                angle_in[:, yy, :] = angle_in_3
    else:
        print('<<ERROR>> this function only takes angles in as degrees right now')

    assert (angle_in < 360).all() and (angle_in >= 0).all(), 'The angle correction function didn''t work properly'
    return angle_in