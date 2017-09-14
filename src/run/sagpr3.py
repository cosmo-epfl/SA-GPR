#!/usr/bin/python

import sys
import numpy as np
import math
import scipy.linalg
import argparse 
import os
sys.path.insert(1,os.path.join(sys.path[0], '..'))
import utils.kern_utils
#from random import shuffle

###############################################################################################################################

def do_sagpr3(lm1,lm3,fractrain,bets,kernel1_flatten,kernel3_flatten,sel,rdm):

    intrins_dev1 = 0.0
    abs_error1 = 0.0
    intrins_dev3 = 0.0
    abs_error3 = 0.0
    ncycles = 5

    print "Results averaged over "+str(ncycles)+" cycles"

    for ic in range(ncycles):

        ndata = len(bets)
        [ns,nt,ntmax,trrange,terange] = utils.kern_utils.shuffle_data(ndata,sel,rdm,fractrain)

        # Build kernel matrix
        kernel1 = utils.kern_utils.unflatten_kernel(ndata,3,kernel1_flatten)
        kernel3 = utils.kern_utils.unflatten_kernel(ndata,7,kernel3_flatten)

        # Partition properties and kernel for training and testing
        betstrain = [bets[i] for i in trrange]
        betstest = [bets[i] for i in terange]
        vtrain = np.array([i.split() for i in betstrain]).astype(complex)
        vtest = np.array([i.split() for i in betstest]).astype(complex)
        k1tr = [[kernel1[i,j] for j in trrange] for i in trrange]
        k1te = [[kernel1[i,j] for j in trrange] for i in terange]
        k3tr = [[kernel3[i,j] for j in trrange] for i in trrange]
        k3te = [[kernel3[i,j] for j in trrange] for i in terange]

        # Extract the 10 non-equivalent components xxx,xxy,xxz,xyy,xyz,xzz,yyy,yyz,yzz,zzz; include degeneracy.
        [bettrain,bettest] = utils.kern_utils.get_non_equivalent_components(vtrain,vtest)

        # Unitary transormation matrix from Cartesian to spherical (l=1,m=-1,0,+1 | l=3,m=-3,-2,-1,0,+1,+2,+3), Condon-Shortley convention; include degeneracy.
        CS = np.array([[-3.0/np.sqrt(30.0),0.0,3.0/np.sqrt(30.0),1.0/np.sqrt(8.0),0.0,-3.0/np.sqrt(120.0),0.0,3.0/np.sqrt(120.0),0.0,-1.0/np.sqrt(8.0)],[1.0j/np.sqrt(30.0),0.0,1.0j/np.sqrt(30.0),-1.0j/np.sqrt(8.0),0.0,1.0j/np.sqrt(120.0),0.0,1.0j/np.sqrt(120.0),0.0,-1.0j/np.sqrt(8.0)],[0.0,-1.0/np.sqrt(15.0),0.0,0.0,1.0/np.sqrt(12.0),0.0,-1.0/np.sqrt(10.0),0.0,1.0/np.sqrt(12.0),0.0],[-1.0/np.sqrt(30.0),0.0,1.0/np.sqrt(30.0),-1.0/np.sqrt(8.0),0.0,-1.0/np.sqrt(120.0),0.0,1.0/np.sqrt(120.0),0.0,1.0/np.sqrt(8.0)],[0.0,0.0,0.0,0.0,-1.0j/np.sqrt(12.0),0.0,0.0,0.0,1.0j/np.sqrt(12.0),0.0],[-1.0/np.sqrt(30.0),0.0,1.0/np.sqrt(30.0),0.0,0.0,4.0/np.sqrt(120.0),0.0,-4.0/np.sqrt(120.0),0.0,0.0],[3.0j/np.sqrt(30.0),0.0,3.0j/np.sqrt(30.0),1.0j/np.sqrt(8.0),0.0,3.0j/np.sqrt(120.0),0.0,3.0j/np.sqrt(120.0),0.0,1.0j/np.sqrt(8.0)],[0.0,-1.0/np.sqrt(15.0),0.0,0.0,-1.0/np.sqrt(12.0),0.0,-1.0/np.sqrt(10.0),0.0,-1.0/np.sqrt(12.0),0.0],[1.0j/np.sqrt(30.0),0.0,1.0j/np.sqrt(30.0),0.0,0.0,-4.0j/np.sqrt(120),0.0,-4.0j/np.sqrt(120),0.0,0.0],[0.0,-3.0/np.sqrt(15.0),0.0,0.0,0.0,0.0,2.0/np.sqrt(10.0),0.0,0.0,0.0]],dtype=complex)
        degeneracy = [1.0,np.sqrt(3.0),np.sqrt(3.0),np.sqrt(3.0),np.sqrt(6.0),np.sqrt(3.0),1.0,np.sqrt(3.0),np.sqrt(3.0),1.0]
        for i in xrange(10):
            CS[i] = CS[i] * degeneracy[i]

#        # Transformation matrix from complex to real spherical harmonics (l=1,m=-1,0,+1).
#        CR1 = np.array([[1.0j,0.0,1.0j],[0.0,np.sqrt(2.0),0.0],[1.0,0.0,-1.0]],dtype=complex) / np.sqrt(2.0)
#        # Transformation matrix from complex to real spherical harmonics (l=3,m=-3,-2,-1,0,+1,+2,+3).
#        CR3 =np.array([[1.0j,0.0,0.0,0.0,0.0,0.0,1.0j],[0.0,1.0j,0.0,0.0,0.0,-1.0j,0.0],[0.0,0.0,1.0j,0.0,1.0j,0.0,0.0],[0.0,0.0,0.0,np.sqrt(2.0),0.0,0.0,0.0],[0.0,0.0,1.0,0.0,-1.0,0.0,0.0],[0.0,1.0,0.0,0.0,0.0,1.0,0.0],[1.0,0.0,0.0,0.0,0.0,0.0,-1.0]],dtype=complex) / np.sqrt(2.0)

        # Transformation matrices from complex to real spherical harmonics (l=1,m=-1,0,+1 | l=3,m=-3,-2,-1,0,+1,+2,+3)
        [CR1,CR3] = utils.kern_utils.complex_to_real_transformation([3,7])

        # Extract the complex spherical components (l=1,l=3) of the hyperpolarizabilities.
        [ [vtrain1,vtrain3],[vtest1,vtest3] ] = utils.kern_utils.partition_spherical_components(bettrain,bettest,CS,[3,7],ns,nt)

        # For l=1 and l=3, convert the complex spherical components into real spherical components.
        vtrain1 = np.concatenate(np.array([np.real(np.dot(CR1,vtrain1[i])) for i in xrange(nt)],dtype=float)).astype(float)
        vtest1  = np.concatenate(np.array([np.real(np.dot(CR1,vtest1[i]))  for i in xrange(ns)],dtype=float)).astype(float)
        vtrain3 = np.concatenate(np.array([np.real(np.dot(CR3,vtrain3[i])) for i in xrange(nt)],dtype=float)).astype(float)
        vtest3  = np.concatenate(np.array([np.real(np.dot(CR3,vtest3[i]))  for i in xrange(ns)],dtype=float)).astype(float)

        # Build training kernels
        [ktrain1,ktrainpred1] = utils.kern_utils.build_training_kernel(nt,3,k1tr,lm1)
        [ktrain3,ktrainpred3] = utils.kern_utils.build_training_kernel(nt,7,k3tr,lm3)

        # Invert training kernels.
        invktrvec1 = scipy.linalg.solve(ktrain1,vtrain1)
        invktrvec3 = scipy.linalg.solve(ktrain3,vtrain3)

        # Build testing kernels.
        ktest1 = utils.kern_utils.build_testing_kernel(ns,nt,3,k1te)
        ktest3 = utils.kern_utils.build_testing_kernel(ns,nt,7,k3te)

        # Predict on test data set.
        outvec1 = np.dot(ktest1,invktrvec1)
        outvec3 = np.dot(ktest3,invktrvec3)
        # Convert the predicted full tensor back to Cartesian coordinates.
        outvec1s = outvec1.reshape((ns,3))
        outvec3s = outvec3.reshape((ns,7))
        outsphr1 = np.zeros((ns,3),dtype=complex)
        outsphr3 = np.zeros((ns,7),dtype=complex)
        betsphe = np.zeros((ns,10),dtype=complex)
        betcart = np.zeros((ns,10),dtype=float)
        betas = np.zeros((ns,27),dtype=float)
        for i in xrange(ns):
            outsphr1[i] = np.dot(np.conj(CR1).T,outvec1s[i])
            outsphr3[i] = np.dot(np.conj(CR3).T,outvec3s[i])
            betsphe[i] = [outsphr1[i][0],outsphr1[i][1],outsphr1[i][2],outsphr3[i][0],outsphr3[i][1],outsphr3[i][2],outsphr3[i][3],outsphr3[i][4],outsphr3[i][5],outsphr3[i][6]]
            betcart[i] = np.real(np.dot(betsphe[i],np.conj(CS).T))
        predcart = np.concatenate([ [betcart[i][0],betcart[i][1]/np.sqrt(3.0),betcart[i][2]/np.sqrt(3.0),betcart[i][1]/np.sqrt(3.0),betcart[i][3]/np.sqrt(3.0),betcart[i][4]/np.sqrt(6.0),betcart[i][2]/np.sqrt(3.0),betcart[i][4]/np.sqrt(6.0),betcart[i][5]/np.sqrt(3.0),betcart[i][1]/np.sqrt(3.0),betcart[i][3]/np.sqrt(3.0),betcart[i][4]/np.sqrt(6.0),betcart[i][3]/np.sqrt(3.0),betcart[i][6],betcart[i][7]/np.sqrt(3.0),betcart[i][4]/np.sqrt(6.0),betcart[i][7]/np.sqrt(3.0),betcart[i][8]/np.sqrt(3.0),betcart[i][2]/np.sqrt(3.0),betcart[i][4]/np.sqrt(6.0),betcart[i][5]/np.sqrt(3.0),betcart[i][4]/np.sqrt(6.0),betcart[i][7]/np.sqrt(3.0),betcart[i][8]/np.sqrt(3.0),betcart[i][5]/np.sqrt(3.0),betcart[i][8]/np.sqrt(3.0),betcart[i][9]] for i in xrange(ns)]).astype(float)
        intrins_dev1   += np.std(vtest1)**2
        abs_error1 += np.sum((outvec1-vtest1)**2)/(3*ns)
        intrins_dev3   += np.std(vtest3)**2
        abs_error3 += np.sum((outvec3-vtest3)**2)/(7*ns)

    intrins_dev1 = np.sqrt(intrins_dev1/float(ncycles))
    abs_error1 = np.sqrt(abs_error1/float(ncycles))
    intrins_error1 = 100*np.sqrt(abs_error1**2/intrins_dev1**2)

    intrins_dev3 = np.sqrt(intrins_dev3/float(ncycles))
    abs_error3 = np.sqrt(abs_error3/float(ncycles))
    intrins_error3 = 100*np.sqrt(abs_error3**2/intrins_dev3**2)

    print ""
    print "testing data points: ", ns    
    print "training data points: ", nt   
    print "Results for lambda_1 and lambda_3 = ", lm1, lm3
    print "--------------------------------"
    print "RESULTS FOR L=1"
    print "--------------------------------"
    print " TEST STD  = %.6f"%intrins_dev1
    print " ABS  RMSE = %.6f"%abs_error1
    print " TEST RMSE = %.6f %%"%intrins_error1
    print "--------------------------------"
    print "RESULTS FOR L=3"
    print "--------------------------------"
    print " TEST STD  = %.6f"%intrins_dev3
    print " ABS  RMSE = %.6f"%abs_error3
    print " TEST RMSE = %.6f %%"%intrins_error3

###############################################################################################################################

def add_command_line_arguments_learn(parsetext):
    parser = argparse.ArgumentParser(description=parsetext)
    parser.add_argument("-t", "--tensors", help="File containing tensors")
    parser.add_argument("-k1", "--kernel1", help="File containing L=1 kernel")
    parser.add_argument("-k3", "--kernel3", help="File containing L=3 kernel")
    parser.add_argument("-sel", "--select",nargs='+', help="Select maximum training partition")
    parser.add_argument("-ftr", "--ftrain",type=float, help="Fraction of data points used for testing")
    parser.add_argument("-lm", "--lmda", nargs='+', help="Lambda values list for KRR calculation")
    parser.add_argument("-rdm", "--random",type=int, help="Number of random training points")
    args = parser.parse_args()
    return args

###############################################################################################################################

def set_variable_values_learn(args):
    lm0=0.001
    lm1=0.001
    lm2=0.001
    lm3=0.001
    lm = [lm0,lm1,lm2,lm2]
    if args.lmda:
        lmlist = args.lmda
        # This list will either be separated by spaces or by commas (or will not be allowed).
        # We will be a little forgiving and allow a mixture of both.
        if sum([lmlist[i].count(',') for i in xrange(len(lmlist))]) > 0:
            for i in xrange(len(lmlist)):
                lmlist[i] = lmlist[i].split(',')
            lmlist = np.concatenate(lmlist)
        if (len(lmlist)%2 != 0):
            print "Error: list of lambdas must have the format n,lambda[n],m,lambda[m],..."
            sys.exit(0)
        for i in xrange(len(lmlist)/2):
            nval = int(lmlist[2*i])
            lmval = float(lmlist[2*i+1])
            lm[nval] = lmval

    ftrain=1
    if args.ftrain:
        ftr = args.ftrain 
    if args.tensors:
        tfile = args.tensors
    else:
        print "Features file must be specified!"
        sys.exit(0)
    # Read in features
    tens=[line.rstrip('\n') for line in open(tfile)]

    print "Loading kernel matrices..."

    # Read in L=1 kernel
    if args.kernel1:
        kfile1 = args.kernel1
    else:
        print "Kernel 1 file must be specified!"
        sys.exit(0)
    kernel1 = np.loadtxt(kfile1,dtype=float)

    # Read in L=3 kernel
    if args.kernel3:
        kfile3 = args.kernel3
    else:
        print "Kernel 3 file must be specified!"
        sys.exit(0)
    kernel3 = np.loadtxt(kfile3,dtype=float)

    beg = 0
    end = int(len(tens)/2)
    sel = [beg,end]
    if args.select:
        sellist = args.select
        for i in xrange(len(sellist)):
            sel[0] = int(sellist[0])
            sel[1] = int(sellist[1])

    rdm = 0
    if args.random:
        rdm = args.random

    return [lm[1],lm[3],ftr,tens,kernel1,kernel3,sel,rdm]

###############################################################################################################################

if __name__ == '__main__':
    # Read in all arguments and call the main function.
    args = add_command_line_arguments_learn("SA-GPR for rank-3 tensors")
    [lm1,lm3,fractrain,bets,kernel1_flatten,kernel3_flatten,sel,rdm] = set_variable_values_learn(args)
    do_sagpr3(lm1,lm3,fractrain,bets,kernel1_flatten,kernel3_flatten,sel,rdm)
