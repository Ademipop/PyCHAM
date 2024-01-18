##########################################################################################
#                                                                                        											 #
#    Copyright (C) 2018-2024 Simon O'Meara : simon.omeara@manchester.ac.uk                  				 #
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
# File Created at 2024-01-18 17:40:55.038270

import numpy as np
import scipy.sparse as SP
from scipy.integrate import solve_ivp

# define function
def ode_solv(y, integ_step, rrc, 
	Cinfl_now, 
	rowvals, colptrs, num_comp, num_sb,
	act_coeff, core_diss, kelv_fac, kimt, num_asb,
	jac_mod_len, jac_part_hmf_indx, rw_indx, N_perbin, jac_part_H2O_indx,
	H2Oi, self):

	# inputs: -------------------------------------
	# y - initial concentrations (# molecules/cm3)
	# integ_step - the maximum integration time step (s)
	# self.rindx_g - index of reactants per equation
	# self.pindx_g - index of products per equation
	# self.rstoi_g - stoichiometry of reactants
	# self.pstoi_g - stoichiometry of products
	# self.nreac_g - number of reactants per equation
	# self.nprod_g - number of products per equation
	# rrc - reaction rate coefficient
	# self.jac_stoi_g - stoichiometries relevant to Jacobian
	# self.njac_g - number of Jacobian elements affected per equation
	# self.jac_den_indx_g - index of component denominators for Jacobian
	# self.jac_indx_g - index of Jacobian to place elements per equation (rows)
	# Cinfl_now - influx of components with continuous influx 
	#		(# molecules/cm3/s)
	# self.y_arr_g - index for matrix used to arrange concentrations of gas-phase reactants, 
	#	enabling calculation of reaction rate coefficients 
	# self.y_rind_g - index of y relating to reactants for reaction rate 
	# 	coefficient equation
	# self.uni_y_rind_g - unique index of reactants 
	# self.y_pind_g - index of y relating to products
	# self.uni_y_pind_g - unique index of products 
	# self.reac_col_g - column indices for sparse matrix of reaction losses
	# self.prod_col_g - column indices for sparse matrix of production gains
	# self.rstoi_flat_g - 1D array of reactant stoichiometries per equation
	# self.pstoi_flat_g - 1D array of product stoichiometries per equation
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
	# self.Psat - pure component saturation vapour pressures (# molecules/cm3)
	# self.Cw - effective absorbing mass concentration of wall (# molecules/cm3) 
	# act_coeff - activity coefficient of components
	# self.jac_wall_indxn - index of inputs to Jacobian by wall partitioning
	# self.seedi - index of seed material
	# core_diss - dissociation constant of seed material
	# kelv_fac - kelvin factor for particles
	# kimt - mass transfer coefficients for gas-particle partitioning (s) and gas-wall partitioning (/s)
	# num_asb - number of actual size bins (excluding wall)
	# self.jac_part_indxn - index for sparse Jacobian for particle influence 
	# self.jac_extr_indx - index for sparse Jacobian for air extraction influence 
	# self.rindx_aq - index of aqueous-phase reactants 
	# self.eqn_num - number of gas- and aqueous-phase reactions 
	# jac_mod_len - modification length due to high fraction of component(s)
	# 	in particle phase
	# jac_part_hmf_indx - index of Jacobian affected by water
	#	 in the particle phase
	# rw_indx - indices of rows affected by water in particle phase
	# N_perbin - number concentration of particles per size bin (#/cm3)
	# jac_part_H2O_indx - sparse Jacobian indices for the effect of
	#	particle-phase water on all other components
	# H2Oi - index for water
	# self.dil_fac - dilution factor for chamber (fraction of chamber air removed/s)
	# self.RO2_indx - index of organic peroxy radicals
	# self.comp_namelist - chemical scheme names of components
	# self.Psat_Pa - saturation vapour pressure of components (Pa) at starting
	#	temperature of chamber
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
		rrc_y = np.ones((self.rindx_g.shape[0]*self.rindx_g.shape[1]))
		rrc_y[self.y_arr_g] = y[self.y_rind_g, 0]
		rrc_y = rrc_y.reshape(self.rindx_g.shape[0], self.rindx_g.shape[1], order = 'C')
		# reaction rate (molecules/cm3/s) 
		rr = rrc[0:self.rindx_g.shape[0]]*((rrc_y**self.rstoi_g).prod(axis=1))
		# loss of reactants
		data = rr[self.rr_arr_g]*self.rstoi_flat_g # prepare loss values
		# convert to sparse matrix
		loss = SP.csc_matrix((data, self.y_rind_g, self.reac_col_g))
		# register loss of reactants
		dd[self.uni_y_rind_g, 0] -= np.array((loss.sum(axis = 1))[self.uni_y_rind_g])[:, 0]
		# gain of products
		data = rr[self.rr_arr_p_g]*self.pstoi_flat_g # prepare loss values
		# convert to sparse matrix
		loss = SP.csc_matrix((data, self.y_pind_g, self.prod_col_g))
		# register gain of products
		dd[self.uni_y_pind_g, 0] += np.array((loss.sum(axis = 1))[self.uni_y_pind_g])[:, 0]
		
		# account for components with continuous gas-phase influx
		dd[[self.con_infl_indx], 0] += Cinfl_now[:, 0]
		# account for continuous extraction of chamber air
		df_indx = np.ones((dd.shape[0])).astype('int') # index for estimating dilution factors
		if (self.odsw_flag == 1): # if water solver used 
			df_indx[H2Oi::num_comp] = 0 # water diluted in water solver 
		df_indx[num_comp*(num_sb-self.wall_on+1)::] = 0 # cannot dilute what is on wall 
		df_indx = df_indx==1 # transform to Boolean array 
		dd[df_indx, 0] -= y[df_indx, 0]*1.*self.dil_fac_now
		
	
		# gas-particle partitioning-----------------
		# transform component concentrations in particles and walls
		# into size bins in rows, components in columns
		ymat = (y[num_comp::, 0]).reshape(num_sb, num_comp)
		
		# for particles, force all components in bins with no particle to zero
		ymat[0:num_asb, :][N_perbin[:, 0] == 0, :] = 0
		
		# for particles, calculate total particle-phase concentration per size bin (# molecules/cm3 (air))
		csum = ((ymat[0:num_asb, :].sum(axis=1)-ymat[0:num_asb, self.seedi].sum(axis=1))+((ymat[0:num_asb, self.seedi]*core_diss).sum(axis=1)).reshape(-1)).reshape(-1, 1)
		# tile total particle-phase concentration over components (# molecules/cm3 (air))
		csum = np.tile(csum, [1, num_comp])
		# size bins with contents
		isb = (csum[0:num_asb, 0] > 0.)
		
		# container for gas-phase concentrations at particle surface
		Csit = np.zeros((num_sb, num_comp))
		
		# mole fractions of components at particle surface
		Csit[0:num_asb, :][isb, :] = (ymat[0:num_asb, :][isb, :]/csum[0:num_asb, :][isb, :])
		
		if any(isb):
			# gas-phase concentration of components at
			# particle surface (# molecules/cm3 (air))
			Csit[0:num_asb, :][isb, :] = Csit[0:num_asb, :][isb, :]*self.Psat[0:num_asb, :][isb, :]*kelv_fac[isb]*act_coeff[0:num_asb, :][isb, :]
			# partitioning rate (# molecules/cm3/s)
			dd_all = kimt[0:num_asb, :]*(y[0:num_comp, 0].reshape(1, -1)-Csit[0:num_asb, :])
			# gas-phase change
			dd[0:num_comp, 0] -= dd_all.sum(axis=0)
			# particle change
			dd[num_comp:num_comp*(num_asb+1), 0] += (dd_all.flatten())
		
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
		data = np.zeros((32484+jac_mod_len))
		
		for i in range(self.rindx_g.shape[0]): # gas-phase reaction loop
			# reaction rate (# molecules/cm3/s)
			rr = rrc[i]*(y[self.rindx_g[i, 0:self.nreac_g[i]], 0].prod())
			# prepare Jacobian inputs
			jac_coeff = np.zeros((self.njac_g[i, 0]))
			# only fill Jacobian if reaction rate sufficient
			if (rr != 0.):
				jac_coeff = (rr*(self.jac_stoi_g[i, 0:self.njac_g[i, 0]])/
				(y[self.jac_den_indx_g[i, 0:self.njac_g[i, 0]], 0]))
			data[self.jac_indx_g[i, 0:self.njac_g[i, 0]]] += jac_coeff
		
		
		# gas-particle partitioning
		part_eff = np.zeros((12500))
		if (sum(N_perbin[:, 0]) > 0.): # if any particles present 
			part_eff[0:6250:2] = -kimt[0:num_asb, :].sum(axis=0) # effect of gas on gas
		
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
				diag = kimt[isb, :]*self.Psat[0, :]*act_coeff[0, :]*kelv_fac[isb, 0]*(-(csum[isb]-ymat[isb, :])/(csum[isb]**2.)) 
				# implement to part_eff
				part_eff[diag_indxg] -= diag
				part_eff[diag_indxp] += diag
				
				if (rw_indx[isb] > -1): # if water in this size bin 
					# prepare for row(s) (particle-phase non-water component effects on water in particle phase)
					rw = kimt[isb, rw_indx[isb]]*self.Psat[0, rw_indx[isb]]*act_coeff[0, rw_indx[isb]]*kelv_fac[isb, 0]*(-(-ymat[isb, rw_indx[isb]])/(csum[isb]**2.)) 
					# indices
					indxg = sti_rw+np.arange(0, ((num_comp-1)*2), 2).astype('int')
					indxp = sti_rw+np.arange(1, ((num_comp-1)*2), 2).astype('int')
					# implement to part_eff_rw
					part_eff_rw[indxg] -= rw
					part_eff_rw[indxp] += rw
					
					# prepare for column(s) (particle-phase water effect on non-water in particle phase)
					#cl = kimt[isb, :]*self.Psat[0, :]*act_coeff[0, :]*kelv_fac[isb, 0]*(-(-ymat[isb, :])/(csum[isb]**2.))
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
		
		data[self.jac_part_indxn] += part_eff # diagonal
		data[jac_part_hmf_indx] += part_eff_rw # rows
		#data[jac_part_H2O_indx] += part_eff_cl # columns
		
		data[self.jac_extr_indx] -= 1.*self.dil_fac_now
		
		# create Jacobian
		j = SP.csc_matrix((data, rowvals, colptrs))
		
		return(j)
	
	# set ODE solver tolerances
	atol = 0.001
	rtol = 0.0001
	self.ode_cnt = 0
	
	# check for underflow issues
	# reaction rate coefficient calculation
	#rrc_y = np.ones((self.rindx_g.shape[0]*self.rindx_g.shape[1]))
	#rrc_y[self.y_arr_g] = y[self.rindx_g]
	#rrc_y = rrc_y.reshape(self.rindx_g.shape[0], self.rindx_g.shape[1], order = 'C')
	# reaction rate coefficient zeroed wherever product of reactant concentrations is zero (including where underflow causes zero, thereby preventing underflows breaking the solver which appears to be an issue on less powerful machines such as HP Spectre Folio) (/s) 
	#rrc[((rrc_y**self.rstoi_g).prod(axis=1)) == 0.0] = 0.
	
	# call on the ODE solver, note y contains the initial condition(s) (molecules/cm3 (air)) and must be 1D even though y in dydt and jac has shape (number of elements, 1)
	sol = solve_ivp(dydt, [0, integ_step], y, atol = atol, rtol = rtol, method = 'BDF', t_eval = [integ_step], vectorized = True, jac = jac)
	
	if (sol.status == -1): # if integration step failed, then we want to reduce the time step and try again 
		y[0] = -1.e6
	else:
		# force all components in size bins with no particle to zero
		y = np.squeeze(sol.y)
		y = y.reshape(num_sb+1, num_comp)
		if (num_asb > 0):
			y[1:num_asb+1, :][N_perbin[:, 0] == 0, :] = 0
		# return to array
		y = y.flatten()
		
	# return concentration(s) and time(s) following integration
	return(y, sol.t)
