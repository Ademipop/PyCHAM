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
'''solution of deliquescence and efflorescence RH, generated by eqn_pars.py in fully functioning mode, or by ui_check.py in testing mode'''
# module to estimate deliquescence and efflorescence relative humidity as a function of temperature
# File Created at 2023-04-19 08:51:02.674995

# function for deliquescence
def drh(TEMP):
	
	# inputs: -----------------
	# TEMP - temperature in chamber (K)
	# ---------------------------
	
	# deliquescence relative humidity (fraction 0-1)
	DRH = 0.*TEMP
	return(DRH)

# function for efflorescence
def erh(TEMP):
	
	# inputs: -----------------
	# TEMP - temperature in chamber (K)
	# ---------------------------
	
	# efflorescence relative humidity (fraction 0-1)
	ERH = 0.*TEMP
	return(ERH)
