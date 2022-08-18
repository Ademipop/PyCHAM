##########################################################################################
#                                                                                        											 #
#    Copyright (C) 2018-2022 Simon O'Meara : simon.omeara@manchester.ac.uk                  				 #
#                                                                                       											 #
#    All Rights Reserved.                                                                									 #
#    This file is part of PyCHAM                                                         									 #
#                                                                                        											 #
#    PyCHAM is free software: you can redistribute it and/or modify it under              						 #
#    the terms of the GNU General Public License as published by the Free Software       					 #
#    Foundation, either version 3 of the License, or (at your option) any later          						 #
#    version.                                                                            										 #
#                                                                                        											 #
#    PyCHAM is distributed in the hope that it will be useful, but WITHOUT                						 #
#    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS       			 #
#    FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more              				 #
#    details.                                                                            										 #
#                                                                                        											 #
#    You should have received a copy of the GNU General Public License along with        					 #
#    PyCHAM.  If not, see <http://www.gnu.org/licenses/>.                                 							 #
#                                                                                        											 #
##########################################################################################
'''solution of ODEs, generated by eqn_pars.py'''
# module to solve system of ordinary differential equations (ODEs) using solve_ivp of Scipy 
# File Created at 2022-08-18 16:19:35.337667

import numpy as np
import scipy.sparse as SP
from scipy.integrate import solve_ivp

# define function
def ode_solv(y, integ_step, rindx, pindx, rstoi, pstoi, 
	nreac, nprod, rrc, jac_stoi, njac, jac_den_indx, 
	jac_indx, Cinfl_now, y_arr, y_rind, uni_y_rind, 
	y_pind, uni_y_pind, reac_col, prod_col, 
	rstoi_flat, pstoi_flat, rr_arr, rr_arr_p,
	rowvals, colptrs, num_comp, num_sb,
	Psat, act_coeff, jac_wall_indx,
	core_diss, kelv_fac, kimt, num_asb,
	jac_part_indx, jac_extr_indx,
	rindx_aq, pindx_aq, rstoi_aq, pstoi_aq,
	nreac_aq, nprod_aq, jac_stoi_aq, njac_aq, jac_den_indx_aq, jac_indx_aq,
	y_arr_aq, y_rind_aq, uni_y_rind_aq, y_pind_aq, uni_y_pind_aq,
	reac_col_aq, prod_col_aq, rstoi_flat_aq,
	pstoi_flat_aq, rr_arr_aq, rr_arr_p_aq, eqn_num, jac_mod_len,
	jac_part_hmf_indx, rw_indx, N_perbin, jac_part_H2O_indx,
	H2Oi, Cinfl_nowp_indx,
	Cinfl_nowp, self):

	# inputs: -------------------------------------
	# y - initial concentrations (# molecules/cm3)
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
	# Cinfl_now - influx of components with continuous influx 
	#		(# molecules/cm3/s)
	# y_arr - index for matrix used to arrange concentrations of gas-phase reactants, 
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
	# self.wall_on - flag saying whether to include wall partitioning
	# Psat - pure component saturation vapour pressures (# molecules/cm3)
	# self.Cw - effective absorbing mass concentration of wall (# molecules/cm3) 
	# act_coeff - activity coefficient of components
	# jac_wall_indx - index of inputs to Jacobian by wall partitioning
	# self.seedi - index of seed material
	# core_diss - dissociation constant of seed material
	# kelv_fac - kelvin factor for particles
	# kimt - mass transfer coefficients for gas-particle partitioning (s) and gas-wall partitioning (/s)
	# num_asb - number of actual size bins (excluding wall)
	# jac_part_indx - index for sparse Jacobian for particle influence 
	# jac_extr_indx - index for sparse Jacobian for air extraction influence 
	# rindx_aq - index of aqueous-phase reactants 
	# eqn_num - number of gas- and aqueous-phase reactions 
	# jac_mod_len - modification length due to high fraction of component(s)
	# 	in particle phase
	# jac_part_hmf_indx - index of Jacobian affected by water
	#	 in the particle phase
	# rw_indx - indices of rows affected by water in particle phase
	# N_perbin - number concentration of particles per size bin (#/cc)
	# jac_part_H2O_indx - sparse Jacobian indices for the effect of
	#	particle-phase water on all other components
	# H2Oi - index for water
	# self.dil_fac - dilution factor for chamber (fraction of chamber air removed/s)
	# self.RO2_indx - index of organic peroxy radicals
	# self.comp_namelist - chemical scheme names of components
	# self.Psat_Pa - saturation vapour pressure of components (Pa) at starting
	#	temperature of chamber
	# Cinfl_nowp_indx - index of particle-phase components with continuous influx 
	# Cinfl_nowp - concentration (# molecules/cm3/s) of particle-phase components with
	#	continuous influx
	# self - reference to program 
	# ---------------------------------------------

	def dydt(t, y): # define the ODE(s)
		
		# inputs: ----------------
		# y - concentrations (# molecules/cm3), note when using
		#	scipy integrator solve_ivp, this should have shape
		#	(number of elements, 1)
		# t - time interval to integrate over (s)
		# ---------------------------------------------
		
		# ensure y is correct shape
		if (y.shape[1] > 1):
			y = y[:, 0].reshape(-1, 1)
		# empty array to hold rate of change per component (this is the returned value from dydt)
		dd = np.zeros((y.shape[0], 1))
		
		# gas-phase reactions -------------------------
		# empty array to hold relevant concentrations for
		# reaction rate coefficient calculation
		rrc_y = np.ones((rindx.shape[0]*rindx.shape[1]))
		rrc_y[y_arr] = y[y_rind, 0]
		rrc_y = rrc_y.reshape(rindx.shape[0], rindx.shape[1], order = 'C')
		# reaction rate (molecules/cm3/s) 
		rr = rrc[0:rindx.shape[0]]*((rrc_y**rstoi).prod(axis=1))
		# loss of reactants
		data = rr[rr_arr]*rstoi_flat # prepare loss values
		# convert to sparse matrix
		loss = SP.csc_matrix((data, y_rind, reac_col))
		# register loss of reactants
		dd[uni_y_rind, 0] -= np.array((loss.sum(axis = 1))[uni_y_rind])[:, 0]
		# gain of products
		data = rr[rr_arr_p]*pstoi_flat # prepare loss values
		# convert to sparse matrix
		loss = SP.csc_matrix((data, y_pind, prod_col))
		# register gain of products
		dd[uni_y_pind, 0] += np.array((loss.sum(axis = 1))[uni_y_pind])[:, 0]
		
		# gas-particle and gas-wall partitioning-----------------
		# transform component concentrations in particles and walls
		# into size bins in rows, components in columns
		ymat = (y[num_comp::, 0]).reshape(num_sb, num_comp)
		
		# for particles, force all components in bins with no particle to zero
		ymat[0:num_asb, :][N_perbin[:, 0] == 0, :] = 0
		
		# for particles, calculate total particle-phase concentration per size bin (# molecules/cm3 (air))
		csum = ((ymat[0:num_asb, :].sum(axis=1)-ymat[0:num_asb, self.seedi].sum(axis=1))+((ymat[0:num_asb, self.seedi]*core_diss).sum(axis=1)).reshape(-1)).reshape(-1, 1)
		# tile total particle-phase concentration over components (# molecules/cm3 (air))
		csum = np.tile(csum, [1, num_comp])
		# concatenate wall bin total concentrations to total particle-phase concentration (# molecules/cm3)
		csum = np.concatenate((csum, self.Cw), axis=0)
		
		# size bins with contents
		isb = (csum[0:num_asb, 0] > 0.)
		
		# wall bins with contents
		wsb = (self.Cw[:, 0] > 0.)
		
		# container for gas-phase concentrations at particle surface and at wall surface
		Csit = np.zeros((num_sb, num_comp))
		
		# mole fractions of components at particle surface
		Csit[0:num_asb, :][isb, :] = (ymat[0:num_asb, :][isb, :]/csum[0:num_asb, :][isb, :])
		# mole fraction of components on walls, note that Cw included in csum above
		Csit[num_asb::, :][wsb, :] = (ymat[num_asb::, :][wsb, :]/csum[num_asb::, :][wsb, :])
		
		if any(isb):
			# gas-phase concentration of components at
			# particle surface (# molecules/cm3 (air))
			Csit[0:num_asb, :][isb, :] = Csit[0:num_asb, :][isb, :]*Psat[0:num_asb, :][isb, :]*kelv_fac[isb]*act_coeff[0:num_asb, :][isb, :]
			# partitioning rate (# molecules/cm3/s)
			dd_all = kimt[0:num_asb, :]*(y[0:num_comp, 0].reshape(1, -1)-Csit[0:num_asb, :])
			# gas-phase change
			dd[0:num_comp, 0] -= dd_all.sum(axis=0)
			# particle change
			dd[num_comp:num_comp*(num_asb+1), 0] += (dd_all.flatten())
		
		if any(wsb):
			# gas-phase concentration of components at
			# wall surface (# molecules/cm3 (air))
			Csit[num_asb::, :][wsb, :] = Csit[num_asb::, :][wsb, :]*Psat[num_asb::, :][wsb, :]*act_coeff[num_asb::, :][wsb, :]
			# partitioning rate (# molecules/cm3/s)
			dd_all = kimt[num_asb::, :]*(y[0:num_comp, 0].reshape(1, -1)-Csit[num_asb::, :])
			# gas-phase change (summed over all wall bins)
			dd[0:num_comp, 0] -= dd_all.sum(axis=0)
			# wall change
			dd[num_comp*(num_asb+1)::, 0] += (dd_all.flatten())
		
		
		
		dd = (dd[:, 0]).reshape(num_sb+1, num_comp)
		# force all components in size bins with no particle to zero
		if (num_asb > 0):
			dd[1:num_asb+1, :][N_perbin[:, 0] == 0, :] = 0
		# return to array, note that consistent with the solve_ivp manual, this ensures dd is
		# a vector rather than matrix, since y0 is a vector
		dd = dd.flatten()
		return (dd)

	def jac(t, y): # define the Jacobian
		
		# inputs: ----------------
		# y - concentrations (# molecules/cm3), note when using scipy integrator solve_ivp, this should have shape (number of elements, 1)
		# t - time interval to integrate over (s)
		# ---------------------------------------------
		
		# ensure y is correct shape
		if (y.ndim == 2):
			if (y.shape[1] > 1):
				y = y[:, 0].reshape(-1, 1)
		if (y.ndim <= 1):
			y = y.reshape(-1, 1)
		
		# elements of sparse Jacobian matrix
		data = np.zeros((65+jac_mod_len))
		
		for i in range(rindx.shape[0]): # gas-phase reaction loop
			# reaction rate (# molecules/cm3/s)
			rr = rrc[i]*(y[rindx[i, 0:nreac[i]], 0].prod())
			# prepare Jacobian inputs
			jac_coeff = np.zeros((njac[i, 0]))
			# only fill Jacobian if reaction rate sufficient
			if (rr != 0.):
				jac_coeff = (rr*(jac_stoi[i, 0:njac[i, 0]])/
				(y[jac_den_indx[i, 0:njac[i, 0]], 0]))
			data[jac_indx[i, 0:njac[i, 0]]] += jac_coeff
		
		
		# gas-particle partitioning
		part_eff = np.zeros((28))
		if (sum(N_perbin[:, 0]) > 0.): # if any particles present 
			part_eff[0:12:3] = -kimt[0:num_asb, :].sum(axis=0) # effect of gas on gas
		
		# empty array for any particle-on-gas and particle-on-particle effects on water in the particle-phase for rows of Jacobian
		part_eff_rw = np.zeros((len(jac_part_hmf_indx)))
		# empty array for any particle-on-gas and particle-on-particle effects of water in the particle-phase on non-water components in the particle-phase for columns of Jacobian
		part_eff_cl = np.zeros((len(jac_part_H2O_indx)))
		# starting index for jacobian row inputs for effect on water
		sti_rw = 0 
		
		# transform particle phase concentrations into
		# size bins in rows, components in columns
		ymat = (y[num_comp:num_comp*(num_asb+1), 0]).reshape(num_asb, num_comp)
		ymat[N_perbin[:, 0] == 0, :] = 0 # ensure zero components where zero particles
		# total particle-phase concentration per size bin (molecules/cm3 (air))
		csum = ymat.sum(axis=1)-ymat[:, self.seedi].sum(axis=1)+(ymat[:, self.seedi]*core_diss).sum(axis=1)
		
		# effect of particle on gas
		for isb in range(int(num_asb)): # size bin loop
			if (csum[isb] > 0): # if components present in this size bin
				# effect of gas on particle
				part_eff[1+isb:num_comp*(num_asb+1):num_asb+1] = +kimt[isb, :]
				# start index
				sti = int((num_asb+1)*num_comp+isb*(num_comp*2))
				# diagonal index
				diag_indxg = sti+np.arange(0, num_comp*2, 2).astype('int')
				diag_indxp = sti+np.arange(1, num_comp*2, 2).astype('int')
				# prepare for diagonal (component effect on itself)
				diag = kimt[isb, :]*Psat[0, :]*act_coeff[0, :]*kelv_fac[isb, 0]*(-(csum[isb]-ymat[isb, :])/(csum[isb]**2.)) 
				# implement to part_eff
				part_eff[diag_indxg] -= diag
				part_eff[diag_indxp] += diag
				
				if (rw_indx[isb] > -1): # if water in this size bin 
					# prepare for row(s) (particle-phase non-water component effects on water in particle phase)
					rw = kimt[isb, rw_indx[isb]]*Psat[0, rw_indx[isb]]*act_coeff[0, rw_indx[isb]]*kelv_fac[isb, 0]*(-(-ymat[isb, rw_indx[isb]])/(csum[isb]**2.)) 
					# indices
					indxg = sti_rw+np.arange(0, ((num_comp-1)*2), 2).astype('int')
					indxp = sti_rw+np.arange(1, ((num_comp-1)*2), 2).astype('int')
					# implement to part_eff_rw
					part_eff_rw[indxg] -= rw
					part_eff_rw[indxp] += rw
					
					# prepare for column(s) (particle-phase water effect on non-water in particle phase)
					#cl = kimt[isb, :]*Psat[0, :]*act_coeff[0, :]*kelv_fac[isb, 0]*(-(-ymat[isb, :])/(csum[isb]**2.))
					#cl = np.zeros((num_comp))
					# remove water
					#cl = np.concatenate((cl[0:H2Oi], cl[H2Oi+1::]))
					#indxg = sti_rw+np.arange(0, (num_comp-1)).astype('int')
					#indxp = sti_rw+np.arange((num_comp-1), (num_comp-1)*2).astype('int')
					# implement to part_eff_cl
					#part_eff_cl[indxg] -= cl
					#part_eff_cl[indxp] += cl
					
					# starting index update
					sti_rw += (num_comp-1)*2
		
		data[jac_part_indx] += part_eff # diagonal
		data[jac_part_hmf_indx] += part_eff_rw # rows
		#data[jac_part_H2O_indx] += part_eff_cl # columns
		
		wsb = 0 # count on wall bins
		# holder for wall effect
		wall_eff = np.zeros((40))
		# effect of gas on gas 
		wall_eff[0:16:4] = -np.sum(kimt[num_asb::, :], axis=0) 
		for wsb in range(int(self.wall_on)): # wall bin loop
			if (self.Cw[wsb, 0] > 0.):
				# effect of gas on wall 
				wall_eff[wsb+1:16:4] = +kimt[num_asb+wsb, :] 
				# effect of wall on gas
				wall_eff[wsb*2*num_comp+num_comp*(self.wall_on+1):num_comp*(self.wall_on+1)+(wsb+1)*2*num_comp:2] = +kimt[num_asb::, :][wsb, :]*(Psat[num_asb::, :][wsb, :]*act_coeff[num_asb::, :][wsb, :]/self.Cw[wsb, :]) 
				# effect of wall on wall
				wall_eff[wsb*2*num_comp+num_comp*(self.wall_on+1)+1:num_comp*(self.wall_on+1)+(wsb+1)*2*num_comp:2] = -kimt[num_asb::, :][wsb, :]*(Psat[num_asb::, :][wsb, :]*act_coeff[num_asb::, :][wsb, :]/self.Cw[wsb, :]) 
		data[jac_wall_indx] += wall_eff
		
		# create Jacobian
		j = SP.csc_matrix((data, rowvals, colptrs))
		
		return(j)
	
	# set ODE solver tolerances
	atol = 0.001
	rtol = 0.0001
	
	# check for underflow issues
	# reaction rate coefficient calculation
	#rrc_y = np.ones((rindx.shape[0]*rindx.shape[1]))
	#rrc_y[y_arr] = y[y_rind]
	#rrc_y = rrc_y.reshape(rindx.shape[0], rindx.shape[1], order = 'C')
	# reaction rate coefficient zeroed wherever product of reactant concentrations is zero (including where underflow causes zero, thereby preventing underflows breaking the solver which appears to be an issue on less powerful machines such as HP Spectre Folio) (/s) 
	#rrc[((rrc_y**rstoi).prod(axis=1)) == 0.0] = 0.
	
	# call on the ODE solver, note y contains the initial condition(s) (molecules/cm3 (air)) and must be 1D even though y in dydt and jac has shape (number of elements, 1)
	sol = solve_ivp(dydt, [0, integ_step], y, atol = atol, rtol = rtol, method = 'BDF', t_eval = [integ_step], vectorized = True, jac = jac)
	
	# force all components in size bins with no particle to zero
	y = np.squeeze(sol.y)
	y = y.reshape(num_sb+1, num_comp)
	if (num_asb > 0):
		y[1:num_asb+1, :][N_perbin[:, 0] == 0, :] = 0
	# return to array
	y = y.flatten()
	
	# return concentration(s) and time(s) following integration
	return(y, sol.t)
