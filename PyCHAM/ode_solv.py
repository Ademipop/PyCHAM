'''solution of ODEs, generated by eqn_pars.py'''
# module to solve ordinary differential equations (ODEs)
# File Created at 2020-10-05 15:16:19.557183

import numpy as np
import scipy.sparse as SP
from assimulo.problem import Explicit_Problem
from assimulo.solvers import CVode
from assimulo.solvers import CVode
from numba import jit, f8

# define function
def ode_solv(y, integ_step, rindx, pindx, rstoi, pstoi, 
	nreac, nprod, rrc, jac_stoi, njac, jac_den_indx, 
	jac_indx, Cinfl_now, y_arr, y_rind, uni_y_rind, 
	y_pind, uni_y_pind, reac_col, prod_col, 
	rstoi_flat, pstoi_flat, rr_arr, rr_arr_p,
	rowvals, colptrs, num_comp, num_sb,
	wall_on, Psat, Cw, act_coeff, kw, jac_wall_indx,
	corei, core_diss, kelv_fac, kimt, num_asb,
	jac_part_indx):

	# inputs: -------------------------------------
	# y - initial concentrations (moleucles/cm3)
	# integ_step - the maximum integration time step (s)
	# rindx - index of reactants per equation
	# pindx - index of products per equation
	# rstoi - stoichiometry of reactants
	# pstoi - stoichiometry of products
	# nreac - number of reactants per equation
	# nprod - number of products per equation
	# rrc - reaction rate coefficient
	# jac_stoi - stoichiometries relevant to Jacobian
	# njac - number of Jacobian elements affected per equation
	# jac_den_indx - index of component denominators for Jacobian
	# jac_indx - index of Jacobian to place elements per equation (rows)
	# Cinfl_now - influx of components with constant influx 
	#		(molecules/cc/s)
	# y_arr - index for matrix used to arrange concentrations, 
	#	enabling calculation of reaction rate coefficients 
	# y_rind - index of y relating to reactants for reaction rate 
	# 	coefficient equation
	# uni_y_rind - unique index of reactants 
	# y_pind - index of y relating to products
	# uni_y_pind - unique index of products 
	# reac_col - column indices for sparse matrix of reaction losses
	# prod_col - column indices for sparse matrix of production gains
	# rstoi_flat - 1D array of reactant stoichiometries per equation
	# pstoi_flat - 1D array of product stoichiometries per equation
	# rr_arr - index for reaction rates to allow reactant loss
	# 	calculation
	# rr_arr_p - index for reaction rates to allow reactant loss
	# 	calculation
	# rowvals - row indices of Jacobian elements
	# colptrs - indices of  rowvals corresponding to each column of the
	# 	Jacobian
	# num_comp - number of components
	# num_sb - number of size bins
	# wall_on - flag saying whether to include wall partitioning
	# Psat - pure component saturation vapour pressures (molecules/cc)
	# Cw - effective absorbing mass concentration of wall (molecules/cc) 
	# act_coeff - activity coefficient of components
	# kw - mass transfer coefficient to wall (/s)
	# jac_wall_indx - index of inputs to Jacobian by wall partitioning
	# corei - index of seed material
	# core_diss - dissociation constant of seed material
	# kelv_fac - kelvin factor for particles
	# kimt - mass transfer coefficient for gas-particle partitioning (s)
	# num_asb - number of actual size bins (excluding wall)
	# jac_part_indx - index for sparse Jacobian for particle influence 
	# ---------------------------------------------

	def dydt(t, y): # define the ODE(s)

		# empty array to hold rate of change per component
		dd = np.zeros((len(y)))
		# empty array to hold relevant concentrations for
		# reaction rate coefficient calculation
		rrc_y = np.ones((rindx.shape[0]*rindx.shape[1]))
		rrc_y[y_arr] = y[y_rind]
		rrc_y = rrc_y.reshape(rindx.shape[0], rindx.shape[1], order = 'C')
		# reaction rate (molecules/cc/s) 
		rr = rrc*((rrc_y**rstoi).prod(axis=1))
		# loss of reactants
		data = rr[rr_arr]*rstoi_flat # prepare loss values
		# convert to sparse matrix
		loss = SP.csc_matrix((data, y_rind, reac_col))
		# register loss of reactants
		dd[uni_y_rind] -= np.array((loss.sum(axis = 1))[uni_y_rind])[:,0]
		# gain of products
		data = rr[rr_arr_p]*pstoi_flat # prepare loss values
		# convert to sparse matrix
		loss = SP.csc_matrix((data, y_pind, prod_col))
		# register gain of products
		dd[uni_y_pind] += np.array((loss.sum(axis = 1))[uni_y_pind])[:,0]
		
		# gas-wall partitioning
		# concentration on wall (molecules/cc (air))
		Csit = y[num_comp*num_sb:num_comp*(num_sb+1)]
		# saturation vapour pressure on wall (molecules/cc (air))
		# note, just using the top rows of Psat and act_coeff
		# as do not need the repetitions over size bins
		if (Cw>0.):
			Csit = Psat[0, :]*(Csit/Cw)*act_coeff[0, :]
			# rate of transfer (molecules/cc/s)
			dd_all = kw*(y[0:num_comp]-Csit)
			dd[0:num_comp] -= dd_all # gas-phase change
			dd[num_comp*num_sb:num_comp*(num_sb+1)] += dd_all # wall change
		
		return (dd)

	def jac(t,y): # define the Jacobian
		# elements of sparse Jacobian matrix
		data = np.zeros((94))
		for i in range(rindx.shape[0]): # equation loop
			# reaction rate (molecules/cc/s)
			rr = rrc[i]*(y[rindx[i, 0:nreac[i]]].prod())
			# prepare Jacobian inputs
			jac_coeff = np.zeros((njac[i, 0]))
			# only fill Jacobian if reaction rate sufficient
			if (rr != 0.):
				jac_coeff = (rr*(jac_stoi[i, 0:njac[i, 0]])/
				(y[jac_den_indx[i, 0:njac[i, 0]]]))
			data[jac_indx[i, 0:njac[i, 0]]] += jac_coeff
		
		if (Cw>0.):
			wall_eff = np.zeros((68))
			wall_eff[0:34:2] = -kw # effect of gas on gas 
			wall_eff[1:34:2] = +kw # effect of gas on wall 
			# effect of wall on gas
			wall_eff[34:68:2] = +kw*(Psat[0,:]*act_coeff[0, :]/Cw) 
			# effect of wall on wall
			wall_eff[34+1:68:2] = -kw*(Psat[0,:]*act_coeff[0, :]/Cw) 
			data[jac_wall_indx] += wall_eff
		
		# create Jacobian
		j = SP.csc_matrix((data, rowvals, colptrs))
		return(j)

	mod = Explicit_Problem(dydt, y) # instantiate solver
	mod.jac = jac # set the Jacobian
	mod_sim = CVode(mod) # define a solver instance
	# there is a general trend of an inverse relationship
	# between tolerances and computation time
	mod_sim.atol = 0.001
	mod_sim.rtol = 0.0001
	# integration approach (backward differentiation formula)
	mod_sim.discr = 'BDF'
	# call solver
	res_t, res = mod_sim.simulate(integ_step)
	# return concentrations following integration
	return(res, res_t)
