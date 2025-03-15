import numpy as np
import os
import pandas as pd
import time

import pyomo.environ as pe
import pyomo.opt as po

start_time = time.time()

PATH = os.path.dirname(__file__)
print(PATH)
DATA = {'D_data': pd.read_csv(os.path.join(PATH, 'D_data.csv'))}

five_years = 'yes'

hours_of_optimization = 8760
hours_in_a_year = 8760
if five_years == 'yes':
    hours_of_optimization *= 7

#pulling region-specific demand shape based on user-defined year
def collecting_D(D_year, region):
    D_data = DATA['D_data']
    if D_year == '2050':
        D_data = pd.read_csv(os.path.join(PATH, '2050_demand_data.csv'), index_col=0)
        D_underlined = D_data[region]
    elif D_year == '2030':
        D_data = pd.read_csv(os.path.join(PATH, '2030_load.csv'), index_col=0)
        D_underlined = D_data[region]
    elif D_year == '2033':
        D_data = pd.read_csv(os.path.join(PATH, 'LoadUpdate_2033.csv'), index_col=0)
        D_underlined = D_data[region]
    elif D_year == 'average_day':
        D_data = pd.read_csv(os.path.join(PATH, 'average_day_extended.csv'), index_col=0)
        D_underlined = D_data[region]
    else:
        region_year = region + '_' + D_year
        D_underlined = D_data[region_year]

    D_underlined = D_underlined.reset_index(drop=True)

    if five_years == 'yes':
        D_underlined = pd.concat([D_underlined] * 7, ignore_index=True)

    return (D_underlined)

#gathering region-specific wind and solar hourly CF data based on user-defined aggregation type
def collecting_G_and_CF_for_VRE(VRE_type, area_width, sites, year, region):
    if region != 'North Central':
        G_data_full = pd.read_csv(os.path.join(PATH, 'gen_profiles_with_site_number_' + region + '.csv'), dtype='unicode')
    elif region == 'North Central': G_data_full = pd.read_csv(os.path.join(PATH, 'gen_profiles_with_site_number_North_Central.csv'), dtype='unicode')

    if area_width == 0:
        sites = 1

    if VRE_type == 'solar':
        G_data = G_data_full[f'solararea_width{area_width}sites{sites}year{year}{region}']
    elif VRE_type == 'wind':
        G_data = G_data_full[f'windarea_width{area_width}sites{sites}year{year}{region}']

    CF = float(G_data[9])

    G_data_hour_trend = G_data.iloc[11:]
    G_data_hour_trend = G_data_hour_trend.reset_index(drop=True)
    G_data_hour_trend = pd.to_numeric(G_data_hour_trend)

    G = G_data_hour_trend * CF

    if five_years == 'yes':
        G_data_2007 = G_data_full[VRE_type + 'area_width' + area_width + 'sites' + sites + 'year' + '2007' + region]
        CF_2007 = float(G_data_2007[9])
        G_data_2008 = G_data_full[VRE_type + 'area_width' + area_width + 'sites' + sites + 'year' + '2008' + region]
        CF_2008 = float(G_data_2008[9])
        G_data_2009 = G_data_full[VRE_type + 'area_width' + area_width + 'sites' + sites + 'year' + '2009' + region]
        CF_2009 = float(G_data_2009[9])
        G_data_2010 = G_data_full[VRE_type + 'area_width' + area_width + 'sites' + sites + 'year' + '2010' + region]
        CF_2010 = float(G_data_2010[9])
        G_data_2011 = G_data_full[VRE_type + 'area_width' + area_width + 'sites' + sites + 'year' + '2011' + region]
        CF_2011 = float(G_data_2011[9])
        G_data_2012 = G_data_full[VRE_type + 'area_width' + area_width + 'sites' + sites + 'year' + '2012' + region]
        CF_2012 = float(G_data_2012[9])
        G_data_2013 = G_data_full[VRE_type + 'area_width' + area_width + 'sites' + sites + 'year' + '2013' + region]
        CF_2013 = float(G_data_2013[9])

        G_data_hour_trend = pd.concat(
            [G_data_2007.iloc[11:], G_data_2008.iloc[11:], G_data_2009.iloc[11:], G_data_2010.iloc[11:],
             G_data_2011.iloc[11:], G_data_2012.iloc[11:], G_data_2013.iloc[11:]], ignore_index=True)
        CF = (CF_2007 + CF_2008 + CF_2009 + CF_2010 + CF_2011 + CF_2012 + CF_2013) / 7
        G = pd.concat([G_data_2007.iloc[11:].astype(float) * CF_2007, G_data_2008.iloc[11:].astype(float) * CF_2008,
                       G_data_2009.iloc[11:].astype(float) * CF_2009, G_data_2010.iloc[11:].astype(float) * CF_2010,
                       G_data_2011.iloc[11:].astype(float) * CF_2011, G_data_2012.iloc[11:].astype(float) * CF_2012,
                       G_data_2013.iloc[11:].astype(float) * CF_2013], ignore_index=True)
    return (G, CF)

#pulling region-specific RoR hourly CF data 
def collecting_G_and_CF_for_ror(region, year):
    if region == 'California':
        acronym = 'California'
    elif region == 'Texas':
        acronym = 'Texas'
    elif region == 'Southwest':
        acronym = 'Southwest'
    elif region == 'Southeast':
        acronym = 'Southeast'
    elif region == 'Northwest':
        acronym = 'Northwest'
    elif region == 'Northeast':
        acronym = 'Northeast'
    elif region == 'North Central':
        acronym = 'North_Central'
    elif region == 'Central':
        acronym = 'Central'
    elif region == 'Atlantic':
        acronym = 'Atlantic'

    G = pd.read_csv(acronym + '_hourly_RoR_hydro_cf_curve_' + year + '.csv', index_col=0)
    CF = G.mean()[0]

    if five_years == 'yes':
        G_2007 = pd.read_csv(acronym + '_hourly_RoR_hydro_cf_curve_' + '2007' + '.csv', index_col=0)
        G_2008 = pd.read_csv(acronym + '_hourly_RoR_hydro_cf_curve_' + '2008' + '.csv', index_col=0)
        G_2009 = pd.read_csv(acronym + '_hourly_RoR_hydro_cf_curve_' + '2009' + '.csv', index_col=0)
        G_2010 = pd.read_csv(acronym + '_hourly_RoR_hydro_cf_curve_' + '2010' + '.csv', index_col=0)
        G_2011 = pd.read_csv(acronym + '_hourly_RoR_hydro_cf_curve_' + '2011' + '.csv', index_col=0)
        G_2012 = pd.read_csv(acronym + '_hourly_RoR_hydro_cf_curve_' + '2012' + '.csv', index_col=0)
        G_2013 = pd.read_csv(acronym + '_hourly_RoR_hydro_cf_curve_' + '2013' + '.csv', index_col=0)

        G = pd.concat([G_2007, G_2008, G_2009, G_2010, G_2011, G_2012, G_2013], ignore_index=True)
        CF = G.mean()[0]

    return (G.squeeze(), CF)

#calculating annualized capital cost based on OCC and financial inputs
def OCC_to_capital(OCC, L, IR, RROE, DF, ITC, PTC, f, FD, CFF, CF):
    # constants
    TR = 0.257
    i = 0.025

    # calcualtions
    WACC_nominal = DF * IR * (1 - TR) + (1 - DF) * RROE
    WACC = (1 + WACC_nominal) / (1 + i) - 1
    CRF = WACC / (1 - (1 / (1 + WACC) ** L))
    FD = pd.Series(FD)
    f = pd.Series(f)
    PVD = sum(FD * f)
    PFF = (1 - TR * PVD * (1 - ITC / 2) - ITC) / (1 - TR)
    FCR = CRF * PFF
    CRF_10yr = WACC / (1-(1/(1 + WACC)**10))
    PTC_discount = PTC / (1 - TR) * CRF / CRF_10yr
    capital = OCC * FCR * CFF - PTC_discount * CF * 8760 / 1000
    
    return (capital)

#pulling costs and financial data from the input dataframe
def pulling_costs_data(costs_df, tech_name):
    OCC_tech = costs_df.loc[tech_name, "OCC"]
    FOM_tech = costs_df.loc[tech_name, "FOM"]
    VOM_tech = costs_df.loc[tech_name, "VOM"] / 1000
    fuelcost_tech = costs_df.loc[tech_name, "Fuel"] / 1000
    heatrate_tech = costs_df.loc[tech_name, "Heat Rate"]
    L_tech = costs_df.loc[tech_name, "L"]
    
    IR_tech = costs_df.loc[tech_name, "IR"]
    RROE_tech = costs_df.loc[tech_name, "RROE"]
    DF_tech = costs_df.loc[tech_name, "DF"]
    ITC_tech = costs_df.loc[tech_name, "ITC"]
    PTC_tech = costs_df.loc[tech_name, "PTC"]
    CFF_tech = costs_df.loc[tech_name, "CFF"]
    return (OCC_tech, FOM_tech, VOM_tech, fuelcost_tech, heatrate_tech, L_tech, IR_tech, RROE_tech, DF_tech, ITC_tech, PTC_tech, CFF_tech)

#intermidiary function that calls pulling_data_costs and OCC_to_capital for each technology to get inputs in correct format for model
def gathering_financial_values(CF_solar, CF_wind, CF_offw, CF_conventional, CF_RoR):
    LCOE_check = 'yes'
    #CF_solar = 0.35
    #CF_wind = 0.488424
    #CF_offw = 0.5
    #CF_conventional = 0.59
    #CF_RoR = 0.66
    CF_ngct = 0.3116
    CF_ngcc = 0.5061
    CF_ngccs = 0.5061
    CF_nuclear = 0.927
    CF_PHS = 0.1 #nonzero to avoid throwing errors
    CF_LIB = 0.1 #nonzero to avoid throwing errors
    CF_LIBshort = 0.1 #nonzero to avoid throwing errors
    CF_LIBlong = 0.1 #nonzero to avoid throwing errors
    CF_geo = 0.9
    CF_CBCCS = 0.8
    if CF_offw == 0:
        CF_offw = 0.001
        
    tech_costs = pd.read_csv("2033_Costs.csv", index_col=0)

    # solar
    OCC_solar, FOM_solar, VOM_solar, fuelcost_solar, heatrate_solar, L_solar, IR_solar, RROE_solar, DF_solar, ITC_solar, PTC_solar, CFF_solar = pulling_costs_data(tech_costs, "Solar")
    f_solar = [0.9346, 0.8735, 0.8164, 0.7631, 0.7132, 0.6666]
    FD_solar = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    capital_solar = OCC_to_capital(OCC_solar, L_solar, IR_solar, RROE_solar, DF_solar, ITC_solar, PTC_solar, f_solar, FD_solar, CFF_solar, CF_solar)
    if LCOE_check == 'yes':
        print('solar check = ' + str((capital_solar + FOM_solar) * 1000 / hours_in_a_year / CF_solar) + ' $/MWh')
        
    # wind
    OCC_wind, FOM_wind, VOM_wind, fuelcost_wind, heatrate_wind, L_wind, IR_wind, RROE_wind, DF_wind, ITC_wind, PTC_wind, CFF_wind = pulling_costs_data(tech_costs, "Wind")
    f_wind = [0.9275, 0.8602, 0.7978, 0.7400, 0.6863, 0.6365]
    FD_wind = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    capital_wind = OCC_to_capital(OCC_wind, L_wind, IR_wind, RROE_wind, DF_wind, ITC_wind, PTC_wind, f_wind, FD_wind, CFF_wind, CF_wind)
    if LCOE_check == 'yes':
        print('wind check = ' + str((capital_wind + FOM_wind) * 1000 / hours_in_a_year / CF_wind) + ' $/MWh')

    # offw
    OCC_offw, FOM_offw, VOM_offw, fuelcost_offw, heatrate_offw, L_offw, IR_offw, RROE_offw, DF_offw, ITC_offw, PTC_offw, CFF_offw = pulling_costs_data(tech_costs, "Offshore Wind")
    f_offw = [0.9278, 0.8608, 0.7987, 0.7410, 0.6875, 0.6379]
    FD_offw = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    capital_offw = OCC_to_capital(OCC_offw, L_offw, IR_offw, RROE_offw, DF_offw, ITC_offw, PTC_offw, f_offw, FD_offw, CFF_offw, CF_offw)
    if LCOE_check == 'yes':
        print('offw check = ' + str((capital_offw + FOM_offw) * 1000 / hours_in_a_year / CF_offw) + ' $/MWh')

    # conventional
    OCC_conventional, FOM_conventional, VOM_conventional, fuelcost_conventional, heatrate_conventional, L_conventional, IR_conventional, RROE_conventional, DF_conventional, ITC_conventional, PTC_conventional, CFF_conventional = pulling_costs_data(tech_costs, "Conventional Hydro")
    f_conventional = [0.9308, 0.8663, 0.8063, 0.7505, 0.6985, 0.6501]
    FD_conventional = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    capital_conventional = OCC_to_capital(OCC_conventional, L_conventional, IR_conventional, RROE_conventional, DF_conventional, ITC_conventional, PTC_conventional, f_conventional, FD_conventional, CFF_conventional, CF_conventional)
    if LCOE_check == 'yes':
        print('conventional check = ' + str((capital_conventional + FOM_conventional) * 1000 / hours_in_a_year / CF_conventional) + ' $/MWh')

    # RoR
    OCC_RoR, FOM_RoR, VOM_RoR, fuelcost_RoR, heatrate_RoR, L_RoR, IR_RoR, RROE_RoR, DF_RoR, ITC_RoR, PTC_RoR, CFF_RoR = pulling_costs_data(tech_costs, "RoR Hydro")
    f_RoR = [0.9308, 0.8663, 0.8063, 0.7505, 0.6985, 0.6501]
    FD_RoR = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    capital_RoR = OCC_to_capital(OCC_RoR, L_RoR, IR_RoR, RROE_RoR, DF_RoR, ITC_RoR, PTC_RoR, f_RoR, FD_RoR, CFF_RoR, CF_RoR)
    if LCOE_check == 'yes':
        print('RoR check = ' + str((capital_RoR + FOM_RoR) * 1000 / hours_in_a_year / CF_RoR) + ' $/MWh')

    # NGCT
    OCC_ngct, FOM_ngct, VOM_ngct, fuelcost_ngct, heatrate_ngct, L_ngct, IR_ngct, RROE_ngct, DF_ngct, ITC_ngct, PTC_ngct, CFF_ngct = pulling_costs_data(tech_costs, "NGCT")
    f_ngct = [0.9499, 0.9023, 0.8571, 0.8142, 0.7734, 0.7346, 0.6978, 0.6629, 0.6297, 0.5981, 0.5682, 0.5397, 0.5127,
              0.487, 0.4626, 0.4394]
    FD_ngct = [0.05, 0.095, 0.0855, 0.077, 0.0693, 0.0623, 0.059, 0.059, 0.0591, 0.059, 0.0591, 0.059, 0.0591,
               0.059, 0.0591, 0.0295]
    capital_ngct = OCC_to_capital(OCC_ngct, L_ngct, IR_ngct, RROE_ngct, DF_ngct, ITC_ngct, PTC_ngct, f_ngct, FD_ngct, CFF_ngct, CF_ngct)
    if LCOE_check == 'yes':
        print('ngct check = ' + str((capital_ngct + FOM_ngct) * 1000 / hours_in_a_year / CF_ngct + VOM_ngct*1000 + fuelcost_ngct * heatrate_ngct) + ' $/MWh')

    # NGCC (F-frame)
    OCC_ngcc, FOM_ngcc, VOM_ngcc, fuelcost_ngcc, heatrate_ngcc, L_ngcc, IR_ngcc, RROE_ngcc, DF_ngcc, ITC_ngcc, PTC_ngcc, CFF_ngcc = pulling_costs_data(tech_costs, "NGCC")
    f_ngcc = [0.9499, 0.9023, 0.8571, 0.8142, 0.7734, 0.7346, 0.6978, 0.6629, 0.6297, 0.5981, 0.5682, 0.5397, 0.5127,
              0.487, 0.4626, 0.4394]
    FD_ngcc = [0.05, 0.095, 0.0855, 0.077, 0.0693, 0.0623, 0.059, 0.059, 0.0591, 0.059, 0.0591, 0.059, 0.0591,
               0.059, 0.0591, 0.0295]
    capital_ngcc = OCC_to_capital(OCC_ngcc, L_ngcc, IR_ngcc, RROE_ngcc, DF_ngcc, ITC_ngcc, PTC_ngcc, f_ngcc, FD_ngcc, CFF_ngcc, CF_ngcc)
    if LCOE_check == 'yes':
        print('ngcc check = ' + str((capital_ngcc + FOM_ngcc) * 1000 / hours_in_a_year / CF_ngcc + VOM_ngcc*1000 + fuelcost_ngcc * heatrate_ngcc) + ' $/MWh')

    # NGCCS (F-frame, 95% CC)
    OCC_ngccs, FOM_ngccs, VOM_ngccs, fuelcost_ngccs, heatrate_ngccs, L_ngccs, IR_ngccs, RROE_ngccs, DF_ngccs, ITC_ngccs, PTC_ngccs, CFF_ngccs = pulling_costs_data(tech_costs, "NGCCS")
    f_ngccs = [0.9499, 0.9023, 0.8571, 0.8142, 0.7734, 0.7346, 0.6978, 0.6629, 0.6297, 0.5981, 0.5682, 0.5397, 0.5127,
               0.487, 0.4626, 0.4394]
    FD_ngccs = [0.05, 0.095, 0.0855, 0.077, 0.0693, 0.0623, 0.059, 0.059, 0.0591, 0.059, 0.0591, 0.059, 0.0591,
                0.059, 0.0591, 0.0295]
    capital_ngccs = OCC_to_capital(OCC_ngccs, L_ngccs, IR_ngccs, RROE_ngccs, DF_ngccs, ITC_ngccs, PTC_ngccs, f_ngccs, FD_ngccs, CFF_ngccs, CF_ngccs)
    if LCOE_check == 'yes':
        print('ngccs check = ' + str((capital_ngccs + FOM_ngccs) * 1000 / hours_in_a_year / CF_ngccs + VOM_ngccs*1000 + fuelcost_ngccs * heatrate_ngccs) + ' $/MWh')

    # PHS (class 8)
    OCC_PHS, FOM_PHS, VOM_PHS, fuelcost_PHS, heatrate_PHS, L_PHS, IR_PHS, RROE_PHS, DF_PHS, ITC_PHS, PTC_PHS, CFF_PHS = pulling_costs_data(tech_costs, "PHS")
    f_PHS = [0.9308, 0.8663, 0.8063, 0.7505, 0.6985, 0.6501]
    FD_PHS = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    capital_PHS = OCC_to_capital(OCC_PHS, L_PHS, IR_PHS, RROE_PHS, DF_PHS, ITC_PHS, PTC_PHS, f_PHS, FD_PHS, CFF_PHS, CF_PHS)
    if LCOE_check == 'yes':
        print('PHS check = ' + str(capital_PHS) + ' $/MW')
        
    # LIB (4Hr)
    OCC_LIB, FOM_LIB, VOM_LIB, fuelcost_LIB, heatrate_LIB, L_LIB, IR_LIB, RROE_LIB, DF_LIB, ITC_LIB, PTC_LIB, CFF_LIB = pulling_costs_data(tech_costs, "LIB")
    f_LIB = [0.9346, 0.8735, 0.8164, 0.7631, 0.7132, 0.6666]
    FD_LIB = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    capital_LIB = OCC_to_capital(OCC_LIB, L_LIB, IR_LIB, RROE_LIB, DF_LIB, ITC_LIB, PTC_LIB, f_LIB, FD_LIB, CFF_LIB, CF_LIB)
    if LCOE_check == 'yes':
        print('LIB check = ' + str(capital_LIB) + ' $/MW')
        
    # LIB (2Hr)
    OCC_LIBshort, FOM_LIBshort, VOM_LIBshort, fuelcost_LIBshort, heatrate_LIBshort, L_LIBshort, IR_LIBshort, RROE_LIBshort, DF_LIBshort, ITC_LIBshort, PTC_LIBshort, CFF_LIBshort = pulling_costs_data(tech_costs, "LIBShort")
    capital_LIBshort = OCC_to_capital(OCC_LIBshort, L_LIBshort, IR_LIBshort, RROE_LIBshort, DF_LIBshort, ITC_LIBshort, PTC_LIBshort, f_LIB, FD_LIB, CFF_LIBshort, CF_LIBshort)
    if LCOE_check == 'yes':
        print('LIBshort check = ' + str(capital_LIBshort) + ' $/MW')
        
    # LIB (8Hr)
    OCC_LIBlong, FOM_LIBlong, VOM_LIBlong, fuelcost_LIBlong, heatrate_LIBlong, L_LIBlong, IR_LIBlong, RROE_LIBlong, DF_LIBlong, ITC_LIBlong, PTC_LIBlong, CFF_LIBlong = pulling_costs_data(tech_costs, "LIBLong")
    capital_LIBlong = OCC_to_capital(OCC_LIBlong, L_LIBlong, IR_LIBlong, RROE_LIBlong, DF_LIBlong, ITC_LIBlong, PTC_LIBlong, f_LIB, FD_LIB, CFF_LIBlong, CF_LIBlong)
    if LCOE_check == 'yes':
        print('LIBlong check = ' + str(capital_LIBlong) + ' $/MW')

    # nuclear (AP1000)
    OCC_nuclear, FOM_nuclear, VOM_nuclear, fuelcost_nuclear, heatrate_nuclear, L_nuclear, IR_nuclear, RROE_nuclear, DF_nuclear, ITC_nuclear, PTC_nuclear, CFF_nuclear = pulling_costs_data(tech_costs, "Nuclear")
    f_nuclear = [0.9235, 0.8528, 0.7875, 0.7272, 0.6716, 0.6202]
    FD_nuclear = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    capital_nuclear = OCC_to_capital(OCC_nuclear, L_nuclear, IR_nuclear, RROE_nuclear, DF_nuclear, ITC_nuclear, PTC_nuclear, f_nuclear, FD_nuclear, CFF_nuclear, CF_nuclear)
    if LCOE_check == 'yes':
        print('nuclear check = ' + str((capital_nuclear + FOM_nuclear) * 1000 / hours_in_a_year / CF_nuclear + VOM_nuclear*1000 + fuelcost_nuclear * heatrate_nuclear) + ' $/MWh')
        
    # geo
    OCC_geo, FOM_geo, VOM_geo, fuelcost_geo, heatrate_geo, L_geo, IR_geo, RROE_geo, DF_geo, ITC_geo, PTC_geo, CFF_geo = pulling_costs_data(tech_costs, "Geothermal")
    f_geo = [0.9278, 0.8608, 0.7987, 0.7410, 0.6875, 0.6379]
    FD_geo = [0.2, 0.32, 0.192, 0.1152, 0.1152, 0.0576]
    capital_geo = OCC_to_capital(OCC_geo, L_geo, IR_geo, RROE_geo, DF_geo, ITC_geo, PTC_geo, f_geo, FD_geo, CFF_geo, CF_geo)
    if LCOE_check == 'yes':
        print('geo check = ' + str((capital_geo + FOM_geo) * 1000 / hours_in_a_year / CF_geo + VOM_geo*1000 + fuelcost_geo * heatrate_geo) + ' $/MWh')

    # Coal-Biomass 90% CCS
    OCC_CBCCS, FOM_CBCCS, VOM_CBCCS, fuelcost_CBCCS, heatrate_CBCCS, L_CBCCS, IR_CBCCS, RROE_CBCCS, DF_CBCCS, ITC_CBCCS, PTC_CBCCS, CFF_CBCCS = pulling_costs_data(tech_costs, "Coal-Biomass CCS")
    L_CBCCS = 75
    f_CBCCS = [0.9236, 0.8530, 0.7878, 0.7276, 0.6720, 0.6207, 0.5732, 0.5294, 0.4890, 0.4516, 0.4171, 0.3852, 0.3558, 0.3286, 0.3035, 0.2803, 0.2589, 0.2391, 0.2208, 0.2039, 0.1884]
    FD_CBCCS = [0.0375, 0.0722, 0.0668, 0.0618, 0.0571, 0.0529, 0.0489, 0.0452, 0.0446, 0.0446, 0.0446, 0.0446, 0.0446, 0.0446, 0.0446, 0.0446, 0.0446, 0.0446, 0.0446, 0.0446, 0.0223]
    capital_CBCCS = OCC_to_capital(OCC_CBCCS, L_CBCCS, IR_CBCCS, RROE_CBCCS, DF_CBCCS, ITC_CBCCS, PTC_CBCCS, f_CBCCS, FD_CBCCS, CFF_CBCCS, CF_CBCCS)
    if LCOE_check == 'yes':
        print('coal-biomass check = ' + str((capital_CBCCS + FOM_CBCCS) * 1000 / hours_in_a_year / CF_CBCCS + VOM_CBCCS*1000 + fuelcost_CBCCS * heatrate_CBCCS) + ' $/MWh')

        
    return (capital_solar, FOM_solar, VOM_solar, fuelcost_solar, heatrate_solar, \
            capital_wind, FOM_wind, VOM_wind, fuelcost_wind, heatrate_wind, \
            capital_offw, FOM_offw, VOM_offw, fuelcost_offw, heatrate_offw, \
            capital_conventional, FOM_conventional, VOM_conventional, fuelcost_conventional, heatrate_conventional, \
            capital_RoR, FOM_RoR, VOM_RoR, fuelcost_RoR, heatrate_RoR, \
            capital_ngct, FOM_ngct, VOM_ngct, fuelcost_ngct, heatrate_ngct, \
            capital_ngcc, FOM_ngcc, VOM_ngcc, fuelcost_ngcc, heatrate_ngcc, \
            capital_ngccs, FOM_ngccs, VOM_ngccs, fuelcost_ngccs, heatrate_ngccs, \
            capital_LIB, FOM_LIB, VOM_LIB, fuelcost_LIB, heatrate_LIB, \
            capital_LIBshort, FOM_LIBshort, VOM_LIBshort, fuelcost_LIBshort, heatrate_LIBshort, \
            capital_LIBlong, FOM_LIBlong, VOM_LIBlong, fuelcost_LIBlong, heatrate_LIBlong, \
            capital_PHS, FOM_PHS, VOM_PHS, fuelcost_PHS, heatrate_PHS, \
            capital_nuclear, FOM_nuclear, VOM_nuclear, fuelcost_nuclear, heatrate_nuclear, \
            capital_geo, FOM_geo, VOM_geo, fuelcost_geo, heatrate_geo, \
            capital_CBCCS, FOM_CBCCS, VOM_CBCCS, fuelcost_CBCCS, heatrate_CBCCS)

def collecting_conventional_CFs(year, region):
    CF_info = pd.read_csv(os.path.join(PATH, 'monthly_hydro_CFs_' + year + '.csv'), dtype='unicode',
                          index_col=0)
    CF_monthly_hydro = CF_info.loc[region].astype(float)

    if five_years == 'yes':
        CF_info_2007 = pd.read_csv(os.path.join(PATH, 'monthly_hydro_CFs_' + '2007' + '.csv'), dtype='unicode',
                                   index_col=0)
        CF_info_2008 = pd.read_csv(os.path.join(PATH, 'monthly_hydro_CFs_' + '2008' + '.csv'), dtype='unicode',
                                   index_col=0)
        CF_info_2009 = pd.read_csv(os.path.join(PATH, 'monthly_hydro_CFs_' + '2009' + '.csv'), dtype='unicode',
                                   index_col=0)
        CF_info_2010 = pd.read_csv(os.path.join(PATH, 'monthly_hydro_CFs_' + '2010' + '.csv'), dtype='unicode',
                                   index_col=0)
        CF_info_2011 = pd.read_csv(os.path.join(PATH, 'monthly_hydro_CFs_' + '2011' + '.csv'), dtype='unicode',
                                   index_col=0)
        CF_info_2012 = pd.read_csv(os.path.join(PATH, 'monthly_hydro_CFs_' + '2012' + '.csv'), dtype='unicode',
                                   index_col=0)
        CF_info_2013 = pd.read_csv(os.path.join(PATH, 'monthly_hydro_CFs_' + '2013' + '.csv'), dtype='unicode',
                                   index_col=0)

        CF_monthly_hydro_2007 = CF_info_2007.loc[region].astype(float)
        CF_monthly_hydro_2008 = CF_info_2008.loc[region].astype(float)
        CF_monthly_hydro_2009 = CF_info_2009.loc[region].astype(float)
        CF_monthly_hydro_2010 = CF_info_2010.loc[region].astype(float)
        CF_monthly_hydro_2011 = CF_info_2011.loc[region].astype(float)
        CF_monthly_hydro_2012 = CF_info_2012.loc[region].astype(float)
        CF_monthly_hydro_2013 = CF_info_2013.loc[region].astype(float)

        CF_monthly_hydro = pd.concat([CF_monthly_hydro_2007.astype(float), CF_monthly_hydro_2008.astype(float),
                                      CF_monthly_hydro_2009.astype(float), CF_monthly_hydro_2010.astype(float),
                                      CF_monthly_hydro_2011.astype(float), CF_monthly_hydro_2012.astype(float),
                                      CF_monthly_hydro_2013.astype(float)])

    return (CF_monthly_hydro)

def collecting_offw_CFs(year, region):
    CF_data = pd.read_csv(os.path.join(PATH, region + '_offshore_wind.csv'), dtype='unicode', index_col=0)
    if five_years == 'yes':
        CF_averages = CF_data.iloc[:, -1]
        CF_curve = CF_averages[1:]
        CF = CF_averages[0]
        CF_curve = CF_curve.reset_index(drop=True)
    elif year == '2007':
        CF_curve = CF_data.iloc[1:8761, -1].astype(float)
        CF = CF_curve.mean()
        CF_curve = CF_curve.reset_index(drop=True)
    elif year == '2008':
        CF_curve = CF_data.iloc[8761:17521, -1].astype(float)
        CF = CF_curve.mean()
        CF_curve = CF_curve.reset_index(drop=True)
    elif year == '2009':
        CF_curve = CF_data.iloc[17521:26281, -1].astype(float)
        CF = CF_curve.mean()
        CF_curve = CF_curve.reset_index(drop=True)
    elif year == '2010':
        CF_curve = CF_data.iloc[26281:35041, -1].astype(float)
        CF = CF_curve.mean()
        CF_curve = CF_curve.reset_index(drop=True)
    elif year == '2011':
        CF_curve = CF_data.iloc[35041:43801, -1].astype(float)
        CF = CF_curve.mean()
        CF_curve = CF_curve.reset_index(drop=True)
    elif year == '2012':
        CF_curve = CF_data.iloc[43801:52561, -1].astype(float)
        CF = CF_curve.mean()
        CF_curve = CF_curve.reset_index(drop=True)
    elif year == '2013':
        CF_curve = CF_data.iloc[52561:61321, -1].astype(float)
        CF = CF_curve.mean()
        CF_curve = CF_curve.reset_index(drop=True)

    return (CF_curve.astype(float), float(CF))

def gathering_emissions_values(e_cap, only_operational_emissions, CF_solar, CF_wind, CF_offw, CF_conventional, CF_RoR):
    LCA_check = 'yes'

    #CF_solar = 0.2122
    #CF_wind = 0.3723
    #CF_offw = 0.3987
    #CF_conventional = 0.42
    #CF_RoR = 0.615
    CF_ngct = 0.3116
    CF_ngcc = 0.5061
    CF_ngccs = 0.5061
    CF_nuclear = 0.927
    CF_geo = 0.9
    CF_CBCCS = 0.8
    
    emissions_multiplier = 0.6921 #1.5C Warming
    #emissions_multiplier = 0.8031 #2C warming
    
    if CF_offw == 0:
        CF_offw = 0.001

    emissions_df = pd.read_csv("Emissions.csv", index_col=0)
    
    # emissions from capacity (gCO2/kW/yr)
    emissions_GC_solar = emissions_df.loc["Solar", "Grid-dependent Capacity Emissions (gCO2/kW/yr/kWh-used)"] * float(e_cap) + \
                         emissions_df.loc["Solar", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier 
    emissions_GC_wind = emissions_df.loc["Wind", "Grid-dependent Capacity Emissions (gCO2/kW/yr/kWh-used)"] * float(e_cap) + \
                        emissions_df.loc["Wind", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_offw = emissions_df.loc["Offshore Wind", "Grid-dependent Capacity Emissions (gCO2/kW/yr/kWh-used)"] * float(e_cap) + \
                        emissions_df.loc["Offshore Wind", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_LIB = emissions_df.loc["LIB", "Grid-dependent Capacity Emissions (gCO2/kW/yr/kWh-used)"] * float(e_cap) + \
                       emissions_df.loc["LIB", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier    
    emissions_GC_LIBshort = emissions_df.loc["LIBShort", "Grid-dependent Capacity Emissions (gCO2/kW/yr/kWh-used)"] * float(e_cap) + \
                            emissions_df.loc["LIBShort", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier  
    emissions_GC_LIBlong = emissions_df.loc["LIBLong", "Grid-dependent Capacity Emissions (gCO2/kW/yr/kWh-used)"] * float(e_cap) + \
                           emissions_df.loc["LIBLong", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier  

    emissions_GC_conventional = emissions_df.loc["Conventional Hydro", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_RoR = emissions_df.loc["RoR Hydro", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_nuclear = emissions_df.loc["Nuclear", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_ngct = emissions_df.loc["NGCT", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_ngcc = emissions_df.loc["NGCC", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_ngccs = emissions_df.loc["NGCCS", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_PHS = emissions_df.loc["PHS", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_geo = emissions_df.loc["Geothermal", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier
    emissions_GC_CBCCS = emissions_df.loc["Coal-Biomass CCS", "Grid-independent Capacity Emissions (gCO2/kW/yr)"] * emissions_multiplier

    if only_operational_emissions == 'yes':
        emissions_GC_solar = 0
        emissions_GC_wind = 0
        emissions_GC_offw = 0
        emissions_GC_conventional = 0
        emissions_GC_RoR = 0
        emissions_GC_nuclear = 0
        emissions_GC_ngct = 0
        emissions_GC_ngcc = 0
        emissions_GC_ngccs = 0
        emissions_GC_LIB = 0
        emissions_GC_PHS = 0
        emissions_GC_geo = 0
        emissions_GC_CBCCS = 0

    # emisions from operation (gCO2/kWh)
    emissions_output_solar = emissions_df.loc["Solar", "Operational Emissions (gCO2/kWh)"]
    emissions_output_wind = emissions_df.loc["Wind", "Operational Emissions (gCO2/kWh)"]
    emissions_output_offw = emissions_df.loc["Offshore Wind", "Operational Emissions (gCO2/kWh)"]
    emissions_output_conventional = emissions_df.loc["Conventional Hydro", "Operational Emissions (gCO2/kWh)"]
    emissions_output_RoR = emissions_df.loc["RoR Hydro", "Operational Emissions (gCO2/kWh)"]
    emissions_output_nuclear = emissions_df.loc["Nuclear", "Operational Emissions (gCO2/kWh)"] * emissions_multiplier 
    emissions_output_ngct = emissions_df.loc["NGCT", "Operational Emissions (gCO2/kWh)"]
    emissions_output_ngcc = emissions_df.loc["NGCC", "Operational Emissions (gCO2/kWh)"]
    emissions_output_ngccs = emissions_df.loc["NGCCS", "Operational Emissions (gCO2/kWh)"]
    emissions_output_LIB = emissions_df.loc["LIB", "Operational Emissions (gCO2/kWh)"]
    emissions_output_LIBshort = emissions_df.loc["LIBShort", "Operational Emissions (gCO2/kWh)"]
    emissions_output_LIBlong = emissions_df.loc["LIBLong", "Operational Emissions (gCO2/kWh)"]
    emissions_output_PHS = emissions_df.loc["PHS", "Operational Emissions (gCO2/kWh)"]
    emissions_output_geo = emissions_df.loc["Geothermal", "Operational Emissions (gCO2/kWh)"]
    emissions_output_CBCCS = emissions_df.loc["Coal-Biomass CCS", "Operational Emissions (gCO2/kWh)"]

    if LCA_check == 'yes':
        print('solar check = ' + str(emissions_GC_solar / hours_in_a_year / CF_solar) + ' gCO2/kWh')
        print('wind check = ' + str(emissions_GC_wind / hours_in_a_year / CF_wind) + ' gCO2/kWh')
        print('offw check = ' + str(emissions_GC_offw / hours_in_a_year / CF_offw) + ' gCO2/kWh')
        print('conventional check = ' + str(emissions_GC_conventional / hours_in_a_year / CF_conventional) + ' gCO2/kWh')
        print('RoR check = ' + str(emissions_GC_RoR / hours_in_a_year / CF_RoR) + ' gCO2/kWh')

        print('ngct check = ' + str(emissions_GC_ngct / hours_in_a_year / CF_ngct + emissions_output_ngct) + ' gCO2/kWh')
        print('ngcc check = ' + str(emissions_GC_ngcc / hours_in_a_year / CF_ngcc + emissions_output_ngcc) + ' gCO2/kWh')
        print('ngccs check = ' + str(emissions_GC_ngccs / hours_in_a_year / CF_ngccs + emissions_output_ngccs) + ' gCO2/kWh')
        print('nuclear check = ' + str(emissions_GC_nuclear / hours_in_a_year / CF_nuclear + emissions_output_nuclear) + ' gCO2/kWh')
        print('geo check = ' + str(emissions_GC_geo / hours_in_a_year / CF_geo + emissions_output_geo) + ' gCO2/kWh')
        print('CBCCS check = ' + str(emissions_GC_CBCCS / hours_in_a_year / CF_CBCCS + emissions_output_CBCCS) + ' gCO2/kWh')

        print('LIB check = ' + str(emissions_GC_LIB) + ' gCO2/kW/yr')
        print('LIBshort check = ' + str(emissions_GC_LIBshort) + ' gCO2/kW/yr')
        print('LIBlong check = ' + str(emissions_GC_LIBlong) + ' gCO2/kW/yr')
        print('PHS check = ' + str(emissions_GC_PHS) + ' gCO2/kW/yr')

    return (emissions_GC_solar, emissions_GC_wind, emissions_GC_offw, emissions_GC_conventional, emissions_GC_RoR, emissions_GC_nuclear, \
            emissions_GC_ngct, emissions_GC_ngcc, emissions_GC_ngccs, emissions_GC_LIB, emissions_GC_LIBshort, emissions_GC_LIBlong, emissions_GC_PHS, emissions_GC_geo, emissions_GC_CBCCS, \
            emissions_output_solar, emissions_output_wind, emissions_output_offw, emissions_output_conventional, emissions_output_RoR, emissions_output_nuclear, \
            emissions_output_ngct, emissions_output_ngcc, emissions_output_ngccs, \
            emissions_output_LIB, emissions_output_LIBshort, emissions_output_LIBlong, emissions_output_PHS, emissions_output_geo, emissions_output_CBCCS)

def run(region, optimize_shares, year, D_year, area_width, sites, cap, e_cap, e_tax, only_operational_emissions, baseload, no_cap, case_location):
    e_tax /= 1000000  # $/g
    if region == "Northeast" and area_width == '360':
        area_width = '240'

    if region == "Northeast" and sites == '169':
        sites = '81'

    #Gathering input data
    D_underlined = collecting_D(D_year, region)
    D_total = sum(D_underlined)
    (G_solar_perkW, CF_solar) = collecting_G_and_CF_for_VRE('solar', area_width, sites, year, region)
    (G_wind_perkW, CF_wind) = collecting_G_and_CF_for_VRE('wind', area_width, sites, year, region)
    (G_RoR_perkW, CF_RoR) = collecting_G_and_CF_for_ror(region, year)
    days_in_month = pd.DataFrame(np.array([[31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]]), columns=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])
    CF_monthly_conventional = collecting_conventional_CFs(year, region)
    CF_hydro = CF_monthly_conventional.mean()
    (G_offw_perkW, CF_offw) = collecting_offw_CFs(year, region)
    G_offw_perkW_df = G_offw_perkW.to_frame()
    G_offw_perkW_df.to_csv(year + '_G_offw_perkW_df.csv')

    #setting cost and emissions values
    (capital_solar, FOM_solar, VOM_solar, fuelcost_solar, heatrate_solar, \
     capital_wind, FOM_wind, VOM_wind, fuelcost_wind, heatrate_wind, \
     capital_offw, FOM_offw, VOM_offw, fuelcost_offw, heatrate_offw, \
     capital_conventional, FOM_conventional, VOM_conventional, fuelcost_conventional, heatrate_conventional, \
     capital_RoR, FOM_RoR, VOM_RoR, fuelcost_RoR, heatrate_RoR, \
     capital_ngct, FOM_ngct, VOM_ngct, fuelcost_ngct, heatrate_ngct, \
     capital_ngcc, FOM_ngcc, VOM_ngcc, fuelcost_ngcc, heatrate_ngcc,
     capital_ngccs, FOM_ngccs, VOM_ngccs, fuelcost_ngccs, heatrate_ngccs, \
     capital_LIB, FOM_LIB, VOM_LIB, fuelcost_LIB, heatrate_LIB, \
     capital_LIBshort, FOM_LIBshort, VOM_LIBshort, fuelcost_LIBshort, heatrate_LIBshort, \
     capital_LIBlong, FOM_LIBlong, VOM_LIBlong, fuelcost_LIBlong, heatrate_LIBlong, \
     capital_PHS, FOM_PHS, VOM_PHS, fuelcost_PHS, heatrate_PHS, \
     capital_nuclear, FOM_nuclear, VOM_nuclear, fuelcost_nuclear, heatrate_nuclear, \
     capital_geo, FOM_geo, VOM_geo, fuelcost_geo, heatrate_geo, \
     capital_CBCCS, FOM_CBCCS, VOM_CBCCS, fuelcost_CBCCS, heatrate_CBCCS) = gathering_financial_values(CF_solar, CF_wind, CF_offw, CF_hydro, CF_RoR)

    (emissions_GC_solar, emissions_GC_wind, emissions_GC_offw, emissions_GC_conventional, emissions_GC_RoR, emissions_GC_nuclear, \
     emissions_GC_ngct, emissions_GC_ngcc, emissions_GC_ngccs, emissions_GC_LIB, emissions_GC_LIBshort, emissions_GC_LIBlong, emissions_GC_PHS, emissions_GC_geo, emissions_GC_CBCCS, \
     emissions_output_solar, emissions_output_wind, emissions_output_offw, emissions_output_conventional, emissions_output_RoR, emissions_output_nuclear,\
     emissions_output_ngct, emissions_output_ngcc, emissions_output_ngccs, emissions_output_LIB, emissions_output_LIBshort, emissions_output_LIBlong, \
     emissions_output_PHS, emissions_output_geo, emissions_output_CBCCS) = gathering_emissions_values(e_cap, only_operational_emissions, CF_solar, CF_wind, CF_offw, CF_hydro, CF_RoR)

    #setting other parameters
    delivery_cost = 47 / 1000  # $/kWh
    TD_losses = 4.7 / 100  # percent loss
    carbon_captured_ngccs = emissions_output_ngcc - emissions_output_ngccs
    carbon_captured_CBCCS = 1046
    CF_nuclear = 0.927

    # source = https://dualchallenge.npc.org/files/CCUS-Chap_2-030521.pdf
    if region == 'Atlantic' or region == 'Northeast' or region == 'Central' or region == 'Southeast' or region == 'California':
        cost_carbon_storage = (7 + 240 * 0.05) / 10 ** 6  # $/ton --> $/gram
    elif region == 'Texas':
        cost_carbon_storage = (7.5 + 240 * 0.05) / 10 ** 6
    elif region == 'Northwest' or region == 'North Central':
        cost_carbon_storage = (11 + 240 * 0.05) / 10 ** 6
    elif region == 'Southwest':
        cost_carbon_storage = (8 + 240 * 0.05) / 10 ** 6

    eta_c_LIB = 0.85
    eta_d_LIB = 0.85

    eta_c_PHS = 0.8
    eta_d_PHS = 0.8

    hourly_LIB_efficiency = 0.99987

    model = pe.ConcreteModel()
    hour = range(hours_of_optimization)
    model.hour = pe.Set(initialize=hour)

    model.D = dict(D_underlined)

    # setting all sizes of technologies
    model.GC_solar = pe.Var(domain=pe.NonNegativeReals)
    model.GC_wind = pe.Var(domain=pe.NonNegativeReals)
    model.GC_offw = pe.Var(domain=pe.NonNegativeReals)
    model.GC_conventional = pe.Var(domain=pe.NonNegativeReals)
    model.GC_RoR = pe.Var(domain=pe.NonNegativeReals)
    model.GC_nuclear = pe.Var(domain=pe.NonNegativeReals)
    model.GC_ngct = pe.Var(domain=pe.NonNegativeReals)
    model.GC_ngcc = pe.Var(domain=pe.NonNegativeReals)
    model.GC_ngccs = pe.Var(domain=pe.NonNegativeReals)
    model.GC_geo = pe.Var(domain=pe.NonNegativeReals)
    model.GC_CBCCS = pe.Var(domain=pe.NonNegativeReals)
    model.GC_LIB = pe.Var(domain=pe.NonNegativeReals)  # power
    model.GC_LIBshort = pe.Var(domain=pe.NonNegativeReals)  # power
    model.GC_LIBlong = pe.Var(domain=pe.NonNegativeReals)  # power
    model.GC_PHS = pe.Var(domain=pe.NonNegativeReals)  # power

    # setting hourly power output of dispatchables
    model.output_conventional = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_ngct = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_ngcc = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_ngccs = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_geo = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_CBCCS = pe.Var(model.hour, domain=pe.NonNegativeReals)

    # tracking power flowrate
    model.ren_2_C = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.ren_2_D = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.ren_2_LIB = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.ren_2_LIBshort = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.ren_2_LIBlong = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.ren_2_PHS = pe.Var(model.hour, domain=pe.NonNegativeReals)

    model.therm_2_D = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.therm_2_LIB = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.therm_2_LIBshort = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.therm_2_LIBlong = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.therm_2_PHS = pe.Var(model.hour, domain=pe.NonNegativeReals)

    model.LIB_2_D = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.LIBshort_2_D = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.LIBlong_2_D = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.PHS_2_D = pe.Var(model.hour, domain=pe.NonNegativeReals)

    model.LIB_level = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.LIBshort_level = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.LIBlong_level = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.PHS_level = pe.Var(model.hour, domain=pe.NonNegativeReals)

    # setting capacity-related costs
    capacity_costs = capital_solar * model.GC_solar + capital_wind * model.GC_wind + capital_offw * model.GC_offw + \
                 capital_conventional * model.GC_conventional + capital_RoR * model.GC_RoR + capital_nuclear * model.GC_nuclear + \
                 capital_ngct * model.GC_ngct + capital_ngcc * model.GC_ngcc + capital_ngccs * model.GC_ngccs + \
                 capital_LIB * model.GC_LIB + capital_LIBshort * model.GC_LIBshort + capital_LIBlong * model.GC_LIBlong + capital_PHS * model.GC_PHS + \
                 capital_geo * model.GC_geo + capital_CBCCS * model.GC_CBCCS

    FOM_costs = FOM_solar * model.GC_solar + FOM_wind * model.GC_wind + FOM_offw * model.GC_offw + \
            FOM_conventional * model.GC_conventional + FOM_RoR * model.GC_RoR + FOM_nuclear * model.GC_nuclear + \
            FOM_ngct * model.GC_ngct + FOM_ngcc * model.GC_ngcc + FOM_ngccs * model.GC_ngccs + \
            FOM_LIB * model.GC_LIB + FOM_LIBshort * model.GC_LIBshort + FOM_LIBlong * model.GC_LIBlong + FOM_PHS * model.GC_PHS + \
            FOM_geo * model.GC_geo + FOM_CBCCS * model.GC_CBCCS

    capacity_emissions = emissions_GC_solar * model.GC_solar + emissions_GC_wind * model.GC_wind + emissions_GC_offw * model.GC_offw + \
                     emissions_GC_conventional * model.GC_conventional + emissions_GC_RoR * model.GC_RoR + emissions_GC_nuclear * model.GC_nuclear + \
                     emissions_GC_ngct * model.GC_ngct + emissions_GC_ngcc * model.GC_ngcc + emissions_GC_ngccs * model.GC_ngccs + \
                     emissions_GC_LIB * model.GC_LIB + emissions_GC_LIBshort * model.GC_LIBshort + emissions_GC_LIBlong * model.GC_LIBlong + \
                     emissions_GC_PHS * model.GC_PHS + emissions_GC_geo * model.GC_geo + emissions_GC_CBCCS * model.GC_CBCCS

    if five_years == 'yes':
        capacity_costs *= 7
        FOM_costs *= 7
        capacity_emissions *= 7

    # setting operation-related costs
    VOM_costs = VOM_ngct * sum(model.output_ngct[i] for i in model.hour) + VOM_ngcc * sum(model.output_ngcc[i] for i in model.hour) + \
            VOM_ngccs * sum(model.output_ngccs[i] for i in model.hour) + VOM_geo * sum(model.output_geo[i] for i in model.hour) + \
            VOM_CBCCS * sum(model.output_CBCCS[i] for i in model.hour) + \
            VOM_nuclear * model.GC_nuclear * hours_of_optimization * CF_nuclear + \
            VOM_PHS * (sum(model.ren_2_PHS[i] for i in model.hour) + sum(model.therm_2_PHS[i] for i in model.hour))

    fuel_costs = fuelcost_ngct * heatrate_ngct * sum(model.output_ngct[i] for i in model.hour) + \
                 fuelcost_ngcc * heatrate_ngcc * sum(model.output_ngcc[i] for i in model.hour) + \
                 fuelcost_ngccs * heatrate_ngccs * sum(model.output_ngccs[i] for i in model.hour) + \
                 fuelcost_nuclear * heatrate_nuclear * model.GC_nuclear * hours_of_optimization * CF_nuclear + \
                 fuelcost_CBCCS * heatrate_CBCCS * sum(model.output_CBCCS[i] for i in model.hour)

    operational_emissions = emissions_output_ngct * sum(model.output_ngct[i] for i in model.hour) + emissions_output_ngcc * sum(model.output_ngcc[i] for i in model.hour) + \
                            emissions_output_ngccs * sum(model.output_ngccs[i] for i in model.hour) + emissions_output_geo * sum(model.output_geo[i] for i in model.hour) + \
                            emissions_output_nuclear * model.GC_nuclear * hours_of_optimization * CF_nuclear + emissions_output_CBCCS * sum(model.output_CBCCS[i] for i in model.hour)

    emissions_captured_costs = (carbon_captured_ngccs * sum(model.output_ngccs[i] for i in model.hour) + carbon_captured_CBCCS * sum(model.output_CBCCS[i] for i in model.hour)) * cost_carbon_storage
    emissions_costs = (capacity_emissions + operational_emissions) * e_tax
    objective_function = capacity_costs + FOM_costs + VOM_costs + fuel_costs + emissions_costs + emissions_captured_costs
    model.cost = pe.Objective(sense=pe.minimize, expr=objective_function)

    # setting all variables required for constraints
    model.G_underlined = pe.Param(model.hour, domain=pe.NonNegativeReals)

    model.power_must_be_served = pe.ConstraintList()
    model.increase_in_battery_lte_CPC = pe.ConstraintList()
    model.increase_in_batteryshort_lte_CPC = pe.ConstraintList()
    model.increase_in_batterylong_lte_CPC = pe.ConstraintList()
    model.increase_in_phs_lte_CPC = pe.ConstraintList()
    model.decrease_in_battery_lte_DPC = pe.ConstraintList()
    model.decrease_in_batteryshort_lte_DPC = pe.ConstraintList()
    model.decrease_in_batterylong_lte_DPC = pe.ConstraintList()
    model.decrease_in_phs_lte_DPC = pe.ConstraintList()

    model.finding_ren_G = pe.ConstraintList()
    model.finding_therm_G = pe.ConstraintList()

    model.LIB_storage_limit = pe.ConstraintList()
    model.LIBshort_storage_limit = pe.ConstraintList()
    model.LIBlong_storage_limit = pe.ConstraintList()
    model.PHS_storage_limit = pe.ConstraintList()

    model.ngct_output_constraint = pe.ConstraintList()
    model.ngcc_output_constraint = pe.ConstraintList()
    model.ngccs_output_constraint = pe.ConstraintList()
    model.conventional_output_constraint = pe.ConstraintList()
    model.geo_output_constraint = pe.ConstraintList()
    model.CBCCS_output_constraint = pe.ConstraintList()

    # setting hourly constraints
    for hour_number in model.hour:
        model.power_must_be_served.add(model.ren_2_D[hour_number] + model.therm_2_D[hour_number] + \
            (model.LIB_2_D[hour_number] + model.LIBshort_2_D[hour_number] + model.LIBlong_2_D[hour_number]) * eta_d_LIB + model.PHS_2_D[hour_number] * eta_d_PHS == model.D[hour_number])

        model.increase_in_battery_lte_CPC.add(model.ren_2_LIB[hour_number] + model.therm_2_LIB[hour_number] <= model.GC_LIB)
        model.increase_in_batteryshort_lte_CPC.add(model.ren_2_LIBshort[hour_number] + model.therm_2_LIBshort[hour_number] <= model.GC_LIBshort)
        model.increase_in_batterylong_lte_CPC.add(model.ren_2_LIBlong[hour_number] + model.therm_2_LIBlong[hour_number] <= model.GC_LIBlong)
        model.increase_in_phs_lte_CPC.add(model.ren_2_PHS[hour_number] + model.therm_2_PHS[hour_number] <= model.GC_PHS)
        model.decrease_in_battery_lte_DPC.add(model.LIB_2_D[hour_number] <= model.GC_LIB)
        model.decrease_in_batteryshort_lte_DPC.add(model.LIBshort_2_D[hour_number] <= model.GC_LIBshort)
        model.decrease_in_batterylong_lte_DPC.add(model.LIBlong_2_D[hour_number] <= model.GC_LIBlong)
        model.decrease_in_phs_lte_DPC.add(model.PHS_2_D[hour_number] <= model.GC_PHS)

        model.finding_ren_G.add(model.ren_2_C[hour_number] + model.ren_2_D[hour_number] + \
             model.ren_2_LIB[hour_number] + model.ren_2_LIBshort[hour_number] + model.ren_2_LIBlong[hour_number] + model.ren_2_PHS[hour_number] == (1 - TD_losses) * \
            (model.GC_solar * G_solar_perkW[hour_number] + model.GC_wind * G_wind_perkW[hour_number] + \
             model.GC_offw * G_offw_perkW[hour_number] + model.GC_RoR * G_RoR_perkW[hour_number] + model.output_conventional[hour_number] + model.GC_nuclear * CF_nuclear))
        model.finding_therm_G.add(model.therm_2_D[hour_number] + \
             model.therm_2_LIB[hour_number] + model.therm_2_LIBshort[hour_number] + model.therm_2_LIBlong[hour_number] + model.therm_2_PHS[hour_number] == (1 - TD_losses) * \
            (model.output_ngct[hour_number] + model.output_ngcc[hour_number] + model.output_ngccs[hour_number] + model.output_geo[hour_number] + model.output_CBCCS[hour_number]))

        model.LIB_storage_limit.add(model.LIB_level[hour_number] <= model.GC_LIB * 4)
        model.LIBshort_storage_limit.add(model.LIBshort_level[hour_number] <= model.GC_LIBshort * 2)
        model.LIBlong_storage_limit.add(model.LIBlong_level[hour_number] <= model.GC_LIBlong * 8)
        model.PHS_storage_limit.add(model.PHS_level[hour_number] <= model.GC_PHS * 10)

        model.ngct_output_constraint.add(model.GC_ngct >= model.output_ngct[hour_number])
        model.ngcc_output_constraint.add(model.GC_ngcc >= model.output_ngcc[hour_number])
        model.ngccs_output_constraint.add(model.GC_ngccs >= model.output_ngccs[hour_number])
        model.conventional_output_constraint.add(model.GC_conventional >= model.output_conventional[hour_number])
        model.geo_output_constraint.add(model.GC_geo >= model.output_geo[hour_number])
        model.CBCCS_output_constraint.add(model.GC_CBCCS >= model.output_CBCCS[hour_number])

    # setting battery-related limits
    model.LIB_level_constraint = pe.ConstraintList()
    model.LIBshort_level_constraint = pe.ConstraintList()
    model.LIBlong_level_constraint = pe.ConstraintList()
    model.PHS_level_constraint = pe.ConstraintList()
    for hour_number in model.hour:
        if hour_number == 0:
            continue
        model.LIB_level_constraint.add(model.LIB_level[hour_number] == model.LIB_level[hour_number - 1] * hourly_LIB_efficiency + (model.ren_2_LIB[hour_number] + model.therm_2_LIB[hour_number]) * eta_c_LIB - model.LIB_2_D[hour_number])
        model.LIBshort_level_constraint.add(model.LIBshort_level[hour_number] == model.LIBshort_level[hour_number - 1] * hourly_LIB_efficiency + (model.ren_2_LIBshort[hour_number] + model.therm_2_LIBshort[hour_number]) * eta_c_LIB - model.LIBshort_2_D[hour_number])
        model.LIBlong_level_constraint.add(model.LIBlong_level[hour_number] == model.LIBlong_level[hour_number - 1] * hourly_LIB_efficiency + (model.ren_2_LIBlong[hour_number] + model.therm_2_LIBlong[hour_number]) * eta_c_LIB - model.LIBlong_2_D[hour_number])
        model.PHS_level_constraint.add(model.PHS_level[hour_number] == model.PHS_level[hour_number - 1] + (model.ren_2_PHS[hour_number] + model.therm_2_PHS[hour_number]) * eta_c_PHS - model.PHS_2_D[hour_number])

    model.setting_battery_0_equal_to_battery_last = pe.Constraint(expr=model.LIB_level[0] == model.LIB_level[hours_of_optimization - 1])
    model.setting_batteryshort_0_equal_to_batteryshort_last = pe.Constraint(expr=model.LIBshort_level[0] == model.LIBshort_level[hours_of_optimization - 1])
    model.setting_batterylong_0_equal_to_batterylong_last = pe.Constraint(expr=model.LIBlong_level[0] == model.LIBlong_level[hours_of_optimization - 1])
    model.setting_phs_0_equal_to_phs_last = pe.Constraint(expr=model.PHS_level[0] == model.PHS_level[hours_of_optimization - 1])

    # setting max CF for thermals due to maintenance and FO
    model.ngccs_CF = pe.Constraint(expr = sum(model.output_ngccs[i] for i in model.hour) <= 0.95 * model.GC_ngccs * hours_of_optimization)
    model.ngcc_CF = pe.Constraint(expr = sum(model.output_ngcc[i] for i in model.hour) <= 0.95 * model.GC_ngcc * hours_of_optimization)
    model.ngct_CF = pe.Constraint(expr = sum(model.output_ngct[i] for i in model.hour) <= 0.95 * model.GC_ngct * hours_of_optimization)
    model.geo_CF = pe.Constraint(expr = sum(model.output_geo[i] for i in model.hour) <= 0.95 * model.GC_geo * hours_of_optimization)
    model.CBCCS_CF = pe.Constraint(expr = sum(model.output_CBCCS[i] for i in model.hour) <= 0.95 * model.GC_CBCCS * hours_of_optimization)
                                                            
    # setting conventional hydro limits
    month = 0
    days_start = 0
    model.conventional_monthly_constraint = pe.ConstraintList()
    for month_number in range(len(CF_monthly_conventional)):
        days_end = days_start + days_in_month.iloc[0, month]

        model.conventional_monthly_constraint.add(expr=sum(model.output_conventional[i] for i in range(int(days_start * 24), int(days_end * 24))) \
                 == model.GC_conventional * 24 * days_in_month.iloc[0, month] * CF_monthly_conventional[month_number])

        days_start = days_end

        if month < 11:
            month += 1
        else:
            month = 0

    if cap == 'yes':
        model.CO2_cap = pe.Constraint(expr=operational_emissions + capacity_emissions <= float(e_cap) * D_total)

    # pulling region-specific build limits
    regional_limits = pd.read_csv("RegionalLimits_2033.csv", index_col=0)
    
    demand_reduction_factor = regional_limits.loc["Demand Reduction Factor", region]
    PHS_expansion_potential = regional_limits.loc["PHS Limit", region]
    RoR_expansion_potential = regional_limits.loc["RoR Limit", region]
    conventional_expansion_potential = regional_limits.loc["Conventional Limit", region]
    offw_expansion_potential = regional_limits.loc["Offshore Wind Limit", region]
    wind_expansion_potential = regional_limits.loc["Wind Limit", region]
    geo_expansion_potential = regional_limits.loc["Geothermal Limit", region]
    solar_expansion_potential = regional_limits.loc["Solar Limit", region]
                                                            
    model.PHS_max = pe.Constraint(expr=model.GC_PHS <= PHS_expansion_potential / demand_reduction_factor)
    model.RoR_max = pe.Constraint(expr=model.GC_RoR <= RoR_expansion_potential / demand_reduction_factor)
    model.conventional_max = pe.Constraint(expr=model.GC_conventional <= conventional_expansion_potential / demand_reduction_factor)
    model.offw_max = pe.Constraint(expr=model.GC_offw <= offw_expansion_potential / demand_reduction_factor)
    model.wind_max = pe.Constraint(expr=model.GC_wind <= wind_expansion_potential / demand_reduction_factor)
    model.solar_max = pe.Constraint(expr=model.GC_solar <= solar_expansion_potential / demand_reduction_factor)
    model.geo_max = pe.Constraint(expr=model.GC_geo <= geo_expansion_potential / demand_reduction_factor)
    
    solver = po.SolverFactory('gurobi', solver_io='python')
    result = solver.solve(model, tee=True)

    # data post-processing
    #demand satisfied from
    ren_2_D = pd.DataFrame.from_dict(model.ren_2_D.extract_values(), orient='index', columns=[str(model.hour)])
    therm_2_D = pd.DataFrame.from_dict(model.therm_2_D.extract_values(), orient='index', columns=[str(model.hour)])
    LIB_2_D = pd.DataFrame.from_dict(model.LIB_2_D.extract_values(), orient='index', columns=[str(model.hour)]) * eta_d_LIB
    LIBshort_2_D = pd.DataFrame.from_dict(model.LIBshort_2_D.extract_values(), orient='index', columns=[str(model.hour)]) * eta_d_LIB
    LIBlong_2_D = pd.DataFrame.from_dict(model.LIBlong_2_D.extract_values(), orient='index', columns=[str(model.hour)]) * eta_d_LIB
    PHS_2_D = pd.DataFrame.from_dict(model.PHS_2_D.extract_values(), orient='index', columns=[str(model.hour)]) * eta_d_PHS
    D = pd.DataFrame.from_dict(model.D, orient='index', columns=[str(model.hour)])

    demand_from = pd.DataFrame(index=range(hours_of_optimization))
    demand_from['demand_from_renewables'] = ren_2_D
    demand_from['demand_from_thermal'] = therm_2_D
    demand_from['demand_from_LIB'] = LIB_2_D
    demand_from['demand_from_LIBshort'] = LIBshort_2_D                                                            
    demand_from['demand_from_LIBlong'] = LIBlong_2_D                                                          
    demand_from['demand_from_PHS'] = PHS_2_D
    demand_from['demand'] = D
    demand_from.to_csv(os.path.join(case_location, r'demand_from.csv'))

    #outputting CF profiles
    CF_curves = pd.DataFrame(index=range(hours_of_optimization))
    conventional_CF_curves = pd.DataFrame()
    CF_curves['solar'] = G_solar_perkW
    CF_curves['wind'] = G_wind_perkW
    CF_curves['offw'] = G_offw_perkW
    CF_curves['RoR'] = G_RoR_perkW
    conventional_CF_curves['conventional'] = CF_monthly_conventional
    CF_curves.to_csv(os.path.join(case_location, r'CF_curves.csv'))
    conventional_CF_curves.to_csv(os.path.join(case_location, r'conventional_CF_curves.csv'))

    #energy_storage_levels
    LIB_level = pd.DataFrame.from_dict(model.LIB_level.extract_values(), orient='index', columns=[str(model.hour)])
    LIBshort_level = pd.DataFrame.from_dict(model.LIBshort_level.extract_values(), orient='index', columns=[str(model.hour)])
    LIBlong_level = pd.DataFrame.from_dict(model.LIBlong_level.extract_values(), orient='index', columns=[str(model.hour)])
    PHS_level = pd.DataFrame.from_dict(model.PHS_level.extract_values(), orient='index', columns=[str(model.hour)])

    storage_levels = pd.DataFrame(index=range(hours_of_optimization))
    storage_levels['LIB'] = LIB_level
    storage_levels['LIBshort'] = LIBshort_level
    storage_levels['LIBlong'] = LIBlong_level
    storage_levels['PHS'] = PHS_level
    storage_levels.to_csv(os.path.join(case_location, r'storage_levels.csv'))

    #generation to
    ren_2_C = pd.DataFrame.from_dict(model.ren_2_C.extract_values(), orient='index', columns=[str(model.hour)])
    ren_2_D = pd.DataFrame.from_dict(model.ren_2_D.extract_values(), orient='index', columns=[str(model.hour)])
    ren_2_LIB = pd.DataFrame.from_dict(model.ren_2_LIB.extract_values(), orient='index', columns=[str(model.hour)])
    ren_2_LIBshort = pd.DataFrame.from_dict(model.ren_2_LIBshort.extract_values(), orient='index', columns=[str(model.hour)])
    ren_2_LIBlong = pd.DataFrame.from_dict(model.ren_2_LIBlong.extract_values(), orient='index', columns=[str(model.hour)])
    ren_2_PHS = pd.DataFrame.from_dict(model.ren_2_PHS.extract_values(), orient='index', columns=[str(model.hour)])

    therm_2_D = pd.DataFrame.from_dict(model.therm_2_D.extract_values(), orient='index', columns=[str(model.hour)])
    therm_2_LIB = pd.DataFrame.from_dict(model.therm_2_LIB.extract_values(), orient='index', columns=[str(model.hour)])
    therm_2_LIBshort = pd.DataFrame.from_dict(model.therm_2_LIBshort.extract_values(), orient='index', columns=[str(model.hour)])
    therm_2_LIBlong = pd.DataFrame.from_dict(model.therm_2_LIBlong.extract_values(), orient='index', columns=[str(model.hour)])
    therm_2_PHS = pd.DataFrame.from_dict(model.therm_2_PHS.extract_values(), orient='index', columns=[str(model.hour)])

    generation_to = pd.DataFrame(index=range(hours_of_optimization))
    generation_to['ren_2_C'] = ren_2_C
    generation_to['ren_2_D'] = ren_2_D
    generation_to['ren_2_LIB'] = ren_2_LIB
    generation_to['ren_2_LIBshort'] = ren_2_LIBshort
    generation_to['ren_2_LIBlong'] = ren_2_LIBlong
    generation_to['ren_2_PHS'] = ren_2_PHS
    generation_to['therm_2_D'] = therm_2_D
    generation_to['therm_2_LIB'] = therm_2_LIB
    generation_to['therm_2_LIBshort'] = therm_2_LIBshort
    generation_to['therm_2_LIBlong'] = therm_2_LIBlong
    generation_to['therm_2_PHS'] = therm_2_PHS
    generation_to.to_csv(os.path.join(case_location, r'generation_to.csv'))

    # dispatchable output
    output_conventional = pd.DataFrame.from_dict(model.output_conventional.extract_values(), orient='index', columns=[str(model.hour)])
    output_ngct = pd.DataFrame.from_dict(model.output_ngct.extract_values(), orient='index', columns=[str(model.hour)])
    output_ngcc = pd.DataFrame.from_dict(model.output_ngcc.extract_values(), orient='index', columns=[str(model.hour)])
    output_ngccs = pd.DataFrame.from_dict(model.output_ngccs.extract_values(), orient='index', columns=[str(model.hour)])
    output_geo = pd.DataFrame.from_dict(model.output_geo.extract_values(), orient='index', columns=[str(model.hour)])
    output_CBCCS = pd.DataFrame.from_dict(model.output_CBCCS.extract_values(), orient='index', columns=[str(model.hour)])
    output_nuclear = pd.DataFrame(pe.value(model.GC_nuclear * CF_nuclear), index = range(hours_of_optimization), columns = ['nuclear'])

    dispatchable_output = pd.DataFrame(index=range(hours_of_optimization))
    dispatchable_output['conventional'] = output_conventional
    dispatchable_output['ngct'] = output_ngct
    dispatchable_output['ngcc'] = output_ngcc
    dispatchable_output['ngccs'] = output_ngccs
    dispatchable_output['geo'] = output_geo
    dispatchable_output['nuclear'] = output_nuclear
    dispatchable_output['CBCCS'] = output_CBCCS
    dispatchable_output.to_csv(os.path.join(case_location, r'dispatchable_output.csv'))

    # tech sizing
    GC_solar = pe.value(model.GC_solar)
    GC_wind = pe.value(model.GC_wind)
    GC_offw = pe.value(model.GC_offw)
    GC_conventional = pe.value(model.GC_conventional)
    GC_RoR = pe.value(model.GC_RoR)
    GC_nuclear = pe.value(model.GC_nuclear)
    GC_ngct = pe.value(model.GC_ngct)
    GC_ngcc = pe.value(model.GC_ngcc)
    GC_ngccs = pe.value(model.GC_ngccs)
    GC_LIB = pe.value(model.GC_LIB)
    GC_LIBshort = pe.value(model.GC_LIBshort)
    GC_LIBlong = pe.value(model.GC_LIBlong)
    GC_PHS = pe.value(model.GC_PHS)
    GC_geo = pe.value(model.GC_geo)
    GC_CBCCS = pe.value(model.GC_CBCCS)

    tech_sizes = pd.DataFrame()
    tech_sizes.loc[0, 'solar'] = GC_solar
    tech_sizes.loc[0, 'wind'] = GC_wind
    tech_sizes.loc[0, 'offw'] = GC_offw
    tech_sizes.loc[0, 'conventional'] = GC_conventional
    tech_sizes.loc[0, 'RoR'] = GC_RoR
    tech_sizes.loc[0, 'nuclear'] = GC_nuclear
    tech_sizes.loc[0, 'ngct'] = GC_ngct
    tech_sizes.loc[0, 'ngcc'] = GC_ngcc
    tech_sizes.loc[0, 'ngccs'] = GC_ngccs
    tech_sizes.loc[0, 'geo'] = GC_geo
    tech_sizes.loc[0, 'CBCCS'] = GC_CBCCS
    tech_sizes.loc[0, 'LIB'] = GC_LIB
    tech_sizes.loc[0, 'LIBshort'] = GC_LIBshort
    tech_sizes.loc[0, 'LIBlong'] = GC_LIBlong
    tech_sizes.loc[0, 'PHS'] = GC_PHS

    tech_sizes.to_csv(os.path.join(case_location, r'tech_sizes.csv'))

    # emissions breakdown by type
    capacity_emissions = pe.value(capacity_emissions) / 8760
    operational_emissions = pe.value(operational_emissions) / 8760

    if five_years == 'yes':
        capacity_emissions /= 7
        operational_emissions /= 7

    emissions_breakdown_by_type = pd.DataFrame()
    emissions_breakdown_by_type.loc[0, 'capacity'] = capacity_emissions
    emissions_breakdown_by_type.loc[0, 'operations'] = operational_emissions
    emissions_breakdown_by_type.to_csv(os.path.join(case_location, r'emissions_breakdown_by_type.csv'))

    # emissions breakdown by tech
    solar_capacity_emissions = GC_solar * emissions_GC_solar
    wind_capacity_emissions = GC_wind * emissions_GC_wind
    offw_capacity_emissions = GC_offw * emissions_GC_offw
    conventional_capacity_emissions = GC_conventional * emissions_GC_conventional
    RoR_capacity_emissions = GC_RoR * emissions_GC_RoR
    nuclear_capacity_emissions = GC_nuclear * emissions_GC_nuclear
    ngct_capacity_emissions = GC_ngct * emissions_GC_ngct
    ngcc_capacity_emissions = GC_ngcc * emissions_GC_ngcc
    ngccs_capacity_emissions = GC_ngccs * emissions_GC_ngccs
    LIB_capacity_emissions = GC_LIB * emissions_GC_LIB
    LIBshort_capacity_emissions = GC_LIBshort * emissions_GC_LIBshort
    LIBlong_capacity_emissions = GC_LIBlong * emissions_GC_LIBlong
    PHS_capacity_emissions = GC_PHS * emissions_GC_PHS
    geo_capacity_emissions = GC_geo * emissions_GC_geo
    CBCCS_capacity_emissions = GC_CBCCS * emissions_GC_CBCCS

    nuclear_operation_emissions = float(output_nuclear.sum() * emissions_output_nuclear)
    ngct_operation_emissions = float(output_ngct.sum() * emissions_output_ngct)
    ngcc_operation_emissions = float(output_ngcc.sum() * emissions_output_ngcc)
    ngccs_operation_emissions = float(output_ngccs.sum() * emissions_output_ngccs)
    geo_operation_emissions = float(output_geo.sum() * emissions_output_geo)
    CBCCS_operation_emissions = float(output_CBCCS.sum() * emissions_output_CBCCS)

    if five_years == 'yes':
        nuclear_operation_emissions /= 7
        ngct_operation_emissions /= 7
        ngcc_operation_emissions /= 7
        ngccs_operation_emissions /= 7
        geo_operation_emissions /= 7
        CBCCS_operation_emissions /= 7

    emissions_by_tech = pd.Series(dtype='float64')
    emissions_by_tech['solar'] = solar_capacity_emissions / 8760
    emissions_by_tech['wind'] = wind_capacity_emissions / 8760
    emissions_by_tech['offw'] = offw_capacity_emissions / 8760
    emissions_by_tech['conventional'] = conventional_capacity_emissions / 8760
    emissions_by_tech['RoR'] = RoR_capacity_emissions / 8760
    emissions_by_tech['nuclear'] = nuclear_capacity_emissions / 8760 + nuclear_operation_emissions / 8760
    emissions_by_tech['ngct'] = ngct_capacity_emissions / 8760 + ngct_operation_emissions / 8760
    emissions_by_tech['ngcc'] = ngcc_capacity_emissions / 8760 + ngcc_operation_emissions / 8760
    emissions_by_tech['ngccs'] = ngccs_capacity_emissions / 8760 + ngccs_operation_emissions / 8760
    emissions_by_tech['geo'] = geo_capacity_emissions / 8760 + geo_operation_emissions / 8760
    emissions_by_tech['CBCCS'] = CBCCS_capacity_emissions / 8760 + CBCCS_operation_emissions / 8760
    emissions_by_tech['LIB'] = LIB_capacity_emissions / 8760
    emissions_by_tech['LIBshort'] = LIBshort_capacity_emissions / 8760
    emissions_by_tech['LIBlong'] = LIBlong_capacity_emissions / 8760                                                         
    emissions_by_tech['PHS'] = PHS_capacity_emissions / 8760
    emissions_by_tech.transpose().to_frame().to_csv(os.path.join(case_location, r'emissions_breakdown_by_tech.csv'))

    # cost breakdown by type
    capacity_costs = pe.value(capacity_costs) / 8760 * 1000
    FOM_costs = pe.value(FOM_costs) / 8760 * 1000
    VOM_costs = pe.value(VOM_costs) / 8760 * 1000
    fuel_costs = pe.value(fuel_costs) / 8760 * 1000
    emissions_tax = pe.value(emissions_costs) / 8760 * 1000
    emissions_captured_costs = pe.value(emissions_captured_costs) / 8760 * 1000
    delivery_costs = float(delivery_cost) * 1000

    if five_years == 'yes':
        capacity_costs /= 7
        FOM_costs /= 7
        VOM_costs /= 7
        fuel_costs /= 7
        emissions_tax /= 7
        emissions_captured_costs /= 7

    cost_breakdown_by_type = pd.DataFrame()
    cost_breakdown_by_type.loc[0, 'capacity'] = capacity_costs
    cost_breakdown_by_type.loc[0, 'FOM'] = FOM_costs
    cost_breakdown_by_type.loc[0, 'VOM'] = VOM_costs
    cost_breakdown_by_type.loc[0, 'fuel'] = fuel_costs
    cost_breakdown_by_type.loc[0, 'emissions_tax'] = emissions_tax
    cost_breakdown_by_type.loc[0, 'carbon_capture'] = emissions_captured_costs
    cost_breakdown_by_type.loc[0, 'delivery'] = delivery_costs
    cost_breakdown_by_type.to_csv(os.path.join(case_location, r'cost_breakdown_by_type.csv'))

    # cost breakdown by tech
    solar_capacity_costs = GC_solar * (capital_solar + FOM_solar)
    wind_capacity_costs = GC_wind * (capital_wind + FOM_wind)
    offw_capacity_costs = GC_offw * (capital_offw + FOM_offw)
    conventional_capacity_costs = GC_conventional * (capital_conventional + FOM_conventional)
    RoR_capacity_costs = GC_RoR * (capital_RoR + FOM_RoR)
    nuclear_capacity_costs = GC_nuclear * (capital_nuclear + FOM_nuclear)
    ngct_capacity_costs = GC_ngct * (capital_ngct + FOM_ngct)
    ngcc_capacity_costs = GC_ngcc * (capital_ngcc + FOM_ngcc)
    ngccs_capacity_costs = GC_ngccs * (capital_ngccs + FOM_ngccs)
    geo_capacity_costs = GC_geo * (capital_geo + FOM_geo)
    CBCCS_capacity_costs = GC_CBCCS * (capital_CBCCS + FOM_CBCCS)
    LIB_capacity_costs = GC_LIB * (capital_LIB + FOM_LIB)
    LIBshort_capacity_costs = GC_LIBshort * (capital_LIBshort + FOM_LIBshort)
    LIBlong_capacity_costs = GC_LIBlong * (capital_LIBlong + FOM_LIBlong)
    PHS_capacity_costs = GC_PHS * (capital_PHS + FOM_PHS)

    nuclear_operation_costs = float(output_nuclear.sum() * (VOM_nuclear + fuelcost_nuclear * heatrate_nuclear))
    ngct_operation_costs = float(output_ngct.sum() * (VOM_ngct + fuelcost_ngct * heatrate_ngct))
    ngcc_operation_costs = float(output_ngcc.sum() * (VOM_ngcc + fuelcost_ngcc * heatrate_ngcc))
    ngccs_operation_costs = float(output_ngccs.sum() * (VOM_ngccs + fuelcost_ngccs * heatrate_ngccs))
    CBCCS_operation_costs = float(output_CBCCS.sum() * (VOM_CBCCS + fuelcost_CBCCS * heatrate_CBCCS))
    PHS_operation_costs = float((generation_to['ren_2_PHS'].sum() + generation_to['therm_2_PHS'].sum()) * VOM_PHS)

    ngccs_carbon_capture_costs = float(output_ngccs.sum() * cost_carbon_storage)
    CBCCS_carbon_capture_costs = float(output_CBCCS.sum() * cost_carbon_storage)

    if five_years == 'yes':
        nuclear_operation_costs /= 7
        ngct_operation_costs /= 7
        ngcc_operation_costs /= 7
        ngccs_operation_costs /= 7
        CBCCS_operation_costs /= 7
        ngccs_carbon_capture_costs /= 7
        CBCCS_carbon_capture_costs /= 7
        PHS_operation_costs /= 7

    total_cost_before_delivery = solar_capacity_costs + wind_capacity_costs + offw_capacity_costs + conventional_capacity_costs + RoR_capacity_costs + \
                             nuclear_capacity_costs + ngct_capacity_costs + ngcc_capacity_costs + ngccs_capacity_costs + CBCCS_capacity_costs + \
                             LIB_capacity_costs + LIBshort_capacity_costs + LIBlong_capacity_costs + PHS_capacity_costs + \
                             ngct_operation_costs + ngcc_operation_costs + ngccs_operation_costs + CBCCS_operation_costs + ngccs_carbon_capture_costs + CBCCS_carbon_capture_costs + \
                             PHS_operation_costs

    cost_by_tech = pd.Series(dtype='float64')
    cost_by_tech['solar'] = ((solar_capacity_costs) / 8760 + delivery_cost * (solar_capacity_costs) / total_cost_before_delivery) * 1000 + emissions_by_tech['solar'] * e_tax / 8760 * 1000
    cost_by_tech['wind'] = ((wind_capacity_costs) / 8760 + delivery_cost * (wind_capacity_costs) / total_cost_before_delivery) * 1000 + emissions_by_tech['wind'] * e_tax / 8760 * 1000
    cost_by_tech['offw'] = ((offw_capacity_costs) / 8760 + delivery_cost * (offw_capacity_costs) / total_cost_before_delivery) * 1000 + emissions_by_tech['offw'] * e_tax / 8760 * 1000
    cost_by_tech['conventional'] = ((conventional_capacity_costs) / 8760 + delivery_cost * (conventional_capacity_costs) / total_cost_before_delivery) * 1000 + emissions_by_tech['conventional'] * e_tax / 8760 * 1000
    cost_by_tech['RoR'] = ((RoR_capacity_costs) / 8760 + delivery_cost * (RoR_capacity_costs) / total_cost_before_delivery) * 1000 + emissions_by_tech['RoR'] * e_tax / 8760 * 1000
    cost_by_tech['nuclear'] = ((nuclear_capacity_costs + nuclear_operation_costs) / 8760 + delivery_cost * (nuclear_capacity_costs + nuclear_operation_costs) / total_cost_before_delivery) * 1000 + \
                               emissions_by_tech['nuclear'] * e_tax / 8760 * 1000
    cost_by_tech['ngct'] = ((ngct_capacity_costs + ngct_operation_costs) / 8760 + delivery_cost * (ngct_capacity_costs + ngct_operation_costs) / total_cost_before_delivery) * 1000 + \
                            emissions_by_tech['ngct'] * e_tax / 8760 * 1000
    cost_by_tech['ngcc'] = ((ngcc_capacity_costs + ngcc_operation_costs) / 8760 + delivery_cost * (ngcc_capacity_costs + ngcc_operation_costs) / total_cost_before_delivery) * 1000 + \
                            emissions_by_tech['ngcc'] * e_tax / 8760 * 1000
    cost_by_tech['ngccs'] = ((ngccs_capacity_costs + ngccs_operation_costs + ngccs_carbon_capture_costs) / 8760 + delivery_cost * (ngccs_capacity_costs + ngccs_operation_costs) / total_cost_before_delivery) * 1000 + \
                             emissions_by_tech['ngccs'] * e_tax / 8760 * 1000
    cost_by_tech['CBCCS'] = ((CBCCS_capacity_costs + CBCCS_operation_costs + CBCCS_carbon_capture_costs) / 8760 + delivery_cost * (CBCCS_capacity_costs + CBCCS_operation_costs) / total_cost_before_delivery) * 1000 + \
                             emissions_by_tech['CBCCS'] * e_tax / 8760 * 1000
    cost_by_tech['geo'] = (geo_capacity_costs / 8760 + delivery_cost * geo_capacity_costs / total_cost_before_delivery) * 1000 + \
                             emissions_by_tech['geo'] * e_tax / 8760 * 1000
    cost_by_tech['PHS'] = ((PHS_capacity_costs + PHS_operation_costs) / 8760 + delivery_cost * (PHS_capacity_costs + PHS_operation_costs) / total_cost_before_delivery) * 1000 + \
                           emissions_by_tech['PHS'] * e_tax / 8760 * 1000
    cost_by_tech['LIB'] = ((LIB_capacity_costs) / 8760 + delivery_cost * (LIB_capacity_costs) / total_cost_before_delivery) * 1000 + emissions_by_tech['LIB'] * e_tax / 8760 * 1000
    cost_by_tech['LIBshort'] = ((LIBshort_capacity_costs) / 8760 + delivery_cost * (LIBshort_capacity_costs) / total_cost_before_delivery) * 1000 + emissions_by_tech['LIBshort'] * e_tax / 8760 * 1000
    cost_by_tech['LIBlong'] = ((LIBlong_capacity_costs) / 8760 + delivery_cost * (LIBlong_capacity_costs) / total_cost_before_delivery) * 1000 + emissions_by_tech['LIBlong'] * e_tax / 8760 * 1000
    cost_by_tech.transpose().to_frame().to_csv(os.path.join(case_location, r'cost_breakdown_by_tech.csv'))

    
    #tracking CFs
    generation_df = pd.DataFrame(0, index = ['annual'], columns = ['solar', 'wind', 'offw', 'RoR', 'conventional', 'nuclear', 'fusion', 'geo', 'ngccs', 'ngcc', 'ngct'])
    generation_df.loc['annual', 'solar'] = GC_solar * CF_curves.loc[:, 'solar'].mean()
    generation_df.loc['annual', 'wind'] = GC_wind * CF_curves.loc[:, 'wind'].mean()
    generation_df.loc['annual', 'offw'] = GC_offw * CF_curves.loc[:, 'offw'].mean()
    generation_df.loc['annual', 'RoR'] = GC_RoR * CF_curves.loc[:, 'RoR'].mean()
    generation_df.loc['annual', 'conventional'] = GC_conventional * conventional_CF_curves.loc[:, 'conventional'].mean()
    generation_df.loc['annual', 'nuclear'] = dispatchable_output['nuclear'].mean()
    generation_df.loc['annual', 'geo'] = dispatchable_output['geo'].mean()
    generation_df.loc['annual', 'CBCCS'] = dispatchable_output['CBCCS'].mean()
    generation_df.loc['annual', 'ngccs'] = dispatchable_output['ngccs'].mean()
    generation_df.loc['annual', 'ngcc'] = dispatchable_output['ngcc'].mean()
    generation_df.loc['annual', 'ngct'] = dispatchable_output['ngct'].mean()
    if five_years == 'yes':
        generation_df /= 7 
    generation_df.to_csv(os.path.join(case_location, r'annual_generation.csv'))
    
    electricity_to_demand = 0
    electriciity_lost_in_storage = 0
    electricity_lost_in_TD = 0
    electricity_curtailed = 0
    VREs_after_curtail_df = pd.DataFrame(0, index = ['annual'], columns = ['solar', 'wind', 'offw', 'RoR', 'conventional'])
    VRE_total_for_current_hour = 0
    for hour_num in model.hour:
        VRE_total_for_current_hour = GC_solar * CF_curves.loc[hour_num, 'solar'] + GC_wind * CF_curves.loc[hour_num, 'wind'] + GC_offw * CF_curves.loc[hour_num, 'offw'] + \
            GC_RoR * CF_curves.loc[hour_num, 'RoR'] + dispatchable_output.loc[hour_num, 'conventional']
        VREs_after_curtail_df.loc['annual', 'solar'] += GC_solar * CF_curves.loc[hour_num, 'solar'] - (GC_solar * CF_curves.loc[hour_num, 'solar'] / VRE_total_for_current_hour * generation_to.loc[hour_num, 'ren_2_C'])
        VREs_after_curtail_df.loc['annual', 'wind'] += GC_wind * CF_curves.loc[hour_num, 'wind'] - (GC_wind * CF_curves.loc[hour_num, 'wind'] / VRE_total_for_current_hour * generation_to.loc[hour_num, 'ren_2_C'])
        VREs_after_curtail_df.loc['annual', 'offw'] += GC_offw * CF_curves.loc[hour_num, 'offw'] - (GC_offw * CF_curves.loc[hour_num, 'offw'] / VRE_total_for_current_hour * generation_to.loc[hour_num, 'ren_2_C'])
        VREs_after_curtail_df.loc['annual', 'RoR'] += GC_RoR * CF_curves.loc[hour_num, 'RoR'] - (GC_RoR * CF_curves.loc[hour_num, 'RoR'] / VRE_total_for_current_hour * generation_to.loc[hour_num, 'ren_2_C'])
        VREs_after_curtail_df.loc['annual', 'conventional'] += dispatchable_output.loc[hour_num, 'conventional'] - (dispatchable_output.loc[hour_num, 'conventional'] / VRE_total_for_current_hour * generation_to.loc[hour_num, 'ren_2_C'])                                                  
    VREs_after_curtail_df.to_csv(os.path.join(case_location, r'VRE_after_curtail.csv'))
    return

# run with:
#   python -m analysis.system.pps.power_plus_storage
def single_case(region, emissions_cap_float):
    print('region = ' + region)
    emissions_cap = str(emissions_cap_float)

    # settings
    baseload = 'no'
    no_limits = 'no'
    no_cap = 'no'
    only_operational_emissions = 'no'
    minimum_CFs = 'no'

    region = region
    optimize_shares = 'yes'
    year = '2013'  # year
    D_year = '2030'
    area_width = '360'  # '240',#
    sites = '169'  # '81',#
    cap = 'yes'
    e_cap = emissions_cap
    e_tax = 0

    if baseload == 'yes':
        case_name = region + '_seven_years_' + emissions_cap + 'gCO2_with_baseload'
    elif no_cap == 'yes':
        case_name = region + '_seven_years_no_cap'
    elif only_operational_emissions == 'yes':
        case_name = case_name = region + '_OnlyOperational_' + emissions_cap + 'gCO2'
    else:
        #case_name = region + '_BASE_' + emissions_cap + 'gCO2'
        case_name = region + '_HighDecarb_' + emissions_cap + 'gCO2'

    case_location = os.path.join(PATH, region, case_name)

    if os.path.isdir(case_location):
        print('folder exists')
    else:
        print('make folder')
        os.makedirs(case_location)

    run(region, optimize_shares, year, D_year, area_width, sites, cap, e_cap, e_tax, only_operational_emissions, baseload, no_cap, case_location)
    return



