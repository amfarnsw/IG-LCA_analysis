import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import math
import time
import json
import shutil

import pyomo.environ as pe
import pyomo.opt as po

start_time = time.time()

PATH = os.path.dirname(__file__)
DATA = {'D_data': pd.read_csv(os.path.join(PATH, 'D_data.csv'))}

five_years = 'yes'

hours_of_optimization = 8760
hours_in_a_year = 8760
if five_years == 'yes':
    hours_of_optimization *= 7


def collecting_D(region):
    D_data = DATA['D_data']
    D_data = pd.read_csv(os.path.join(PATH, '2050_demand_data.csv'), index_col=0)
    D_underlined = D_data[region]

    D_underlined = D_underlined.reset_index(drop=True)

    if five_years == 'yes':
        D_underlined = pd.concat([D_underlined] * 7, ignore_index=True)

    return (D_underlined)

def collecting_G_and_CF_for_VRE(VRE_type, area_width, sites, year, region):
    if region != 'North Central':
        G_data_full = pd.read_csv(os.path.join(PATH, 'gen_profiles_with_site_number_' + region + '.csv'), dtype='unicode')
    elif region == 'North Central': G_data_full = pd.read_csv(os.path.join(PATH, 'gen_profiles_with_site_number_North_Central.csv'), dtype='unicode')

    if area_width == 0:  # temp hack cuz 1 row bugs categorical input ops
        sites = 1

    if VRE_type == 'solar':
        G_data = G_data_full[f'solararea_width{area_width}sites{sites}year{year}{region}']
    elif VRE_type == 'wind':
        G_data = G_data_full[f'windarea_width{area_width}sites{sites}year{year}{region}']

    CF = float(G_data[9])

    G_data_hour_trend = G_data.iloc[11:]
    G_data_hour_trend = G_data_hour_trend.reset_index(drop=True)
    G_data_hour_trend = pd.to_numeric(G_data_hour_trend)

    G = G_data_hour_trend * CF  # kWh/kW

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

def gathering_financial_values(fusion_OCC, region):
    LCOE_check = 'no' # 'yes'
    CF_solar = 0.2122
    CF_wind = 0.3723
    CF_offw = 0.3987
    CF_conventional = 0.42
    CF_RoR = 0.615
    CF_ngct = 0.3116
    CF_ngcc = 0.5061
    CF_ngccs = 0.5061
    CF_fusion = 0.85
    CF_nuclear = 0.937
    
    discount_factor = 0.06
    transmission_data = pd.read_csv(os.path.join(PATH, 'TD_costs', region + '_transmission.csv'), dtype='unicode', index_col = 0)
    
    # solar
    CAPEX_solar = 632
    FOM_solar = 13
    VOM_solar = 0
    fuelcost_solar = 0
    heatrate_solar = 0
    L_solar = 30
    transmission_solar = float(transmission_data.loc[2050, 'solar'])

    CRC_solar = discount_factor / (1 - (1 + discount_factor)**(-L_solar))
    capital_solar = CRC_solar * CAPEX_solar
    transmission_capital_solar = CRC_solar * transmission_solar
    if LCOE_check == 'yes':
        print('solar check = ' + str((capital_solar + FOM_solar + transmission_capital_solar) * 1000 / hours_in_a_year / CF_solar) + ' $/MWh')

    # wind
    CAPEX_wind = 924
    FOM_wind = 23
    VOM_wind = 0
    fuelcost_wind = 0
    heatrate_wind = 0
    L_wind = 30
    transmission_wind = float(transmission_data.loc[2050, 'wind'])

    CRC_wind = discount_factor / (1 - (1 + discount_factor)**(-L_wind))
    capital_wind = CRC_wind * CAPEX_wind
    transmission_capital_wind = CRC_wind * transmission_wind
    if LCOE_check == 'yes':
        print('wind check = ' + str((capital_wind + FOM_wind + transmission_capital_wind) * 1000 / hours_in_a_year / CF_wind) + ' $/MWh')

    # offw
    CAPEX_offw = 2528
    FOM_offw = 74
    VOM_offw = 0
    fuelcost_offw = 0
    heatrate_offw = 0
    L_offw = 30
    transmission_offw = float(transmission_data.loc[2050, 'offw'])

    CRC_offw = discount_factor / (1 - (1 + discount_factor)**(-L_offw))
    capital_offw = CRC_offw * CAPEX_offw
    transmission_capital_offw = CRC_offw * transmission_offw
    if LCOE_check == 'yes':
        print('offw check = ' + str((capital_offw + FOM_offw + transmission_capital_offw) * 1000 / hours_in_a_year / CF_offw) + ' $/MWh')

    # conventional
    CAPEX_conventional = 7107
    FOM_conventional = 40
    VOM_conventional = 0
    fuelcost_conventional = 0
    heatrate_conventional = 0
    L_conventional = 100
    transmission_conventional = float(transmission_data.loc[2050, 'hydro'])

    CRC_conventional = discount_factor / (1 - (1 + discount_factor)**(-L_conventional))
    capital_conventional = CRC_conventional * CAPEX_conventional
    transmission_capital_conventional = CRC_conventional * transmission_conventional
    if LCOE_check == 'yes':
        print('conventional check = ' + str((capital_conventional + FOM_conventional + transmission_capital_conventional) * 1000 / hours_in_a_year / CF_conventional) + ' $/MWh')

    # RoR
    CAPEX_RoR = 7929
    FOM_RoR = 139
    VOM_RoR = 0
    fuelcost_RoR = 0
    heatrate_RoR = 0
    L_RoR = 100
    transmission_RoR = float(transmission_data.loc[2050, 'RoR'])

    CRC_RoR = discount_factor / (1 - (1 + discount_factor)**(-L_RoR))
    capital_RoR = CRC_RoR * CAPEX_RoR
    transmission_capital_RoR = CRC_RoR * transmission_RoR
    if LCOE_check == 'yes':
        print('RoR check = ' + str((capital_RoR + FOM_RoR + transmission_capital_RoR) * 1000 / hours_in_a_year / CF_RoR) + ' $/MWh')

    # NGCT
    CAPEX_ngct = 872
    FOM_ngct = 20
    VOM_ngct = 6.44
    fuelcost_ngct = 3.99
    heatrate_ngct = 9.72
    L_ngct = 55
    transmission_ngct = float(transmission_data.loc[2050, 'ngct'])

    CRC_ngct = discount_factor / (1 - (1 + discount_factor)**(-L_ngct))
    capital_ngct = CRC_ngct * CAPEX_ngct
    transmission_capital_ngct = CRC_ngct * transmission_ngct
    if LCOE_check == 'yes':
        print('ngct check = ' + str((capital_ngct + FOM_ngct + transmission_capital_ngct) * 1000 / hours_in_a_year / CF_ngct + VOM_ngct + fuelcost_ngct * heatrate_ngct) + ' $/MWh')

    # NGCC
    CAPEX_ngcc = 985
    FOM_ngcc = 24
    VOM_ngcc = 1.61
    fuelcost_ngcc = 3.99
    heatrate_ngcc = 6.08
    L_ngcc = 30
    transmission_ngcc = float(transmission_data.loc[2050, 'ngcc'])

    CRC_ngcc = discount_factor / (1 - (1 + discount_factor)**(-L_ngcc))
    capital_ngcc = CRC_ngcc * CAPEX_ngcc
    transmission_capital_ngcc = CRC_ngcc * transmission_ngcc
    if LCOE_check == 'yes':
        print('ngcc check = ' + str((capital_ngcc + FOM_ngcc + transmission_capital_ngcc) * 1000 / hours_in_a_year / CF_ngcc + VOM_ngcc + fuelcost_ngcc * heatrate_ngcc) + ' $/MWh')

    # NGCCS
    CAPEX_ngccs = 1611
    FOM_ngccs = 39
    VOM_ngccs = 3.23
    fuelcost_ngccs = 3.99
    heatrate_ngccs = 6.74
    L_ngccs = 55
    transmission_ngccs = float(transmission_data.loc[2050, 'ngccs'])

    CRC_ngccs = discount_factor / (1 - (1 + discount_factor)**(-L_ngccs))
    capital_ngccs = CRC_ngccs * CAPEX_ngccs
    transmission_capital_ngccs = CRC_ngccs * transmission_ngccs
    if LCOE_check == 'yes':
        print('ngccs check = ' + str((capital_ngccs + FOM_ngccs + transmission_capital_ngccs) * 1000 / hours_in_a_year / CF_ngccs + VOM_ngccs + fuelcost_ngccs * heatrate_ngccs) + ' $/MWh')

    # PHS
    CAPEX_PHS = 3377
    FOM_PHS = 18.7
    VOM_PHS = 0.54
    fuelcost_PHS = 0
    heatrate_PHS = 0
    L_PHS = 100
    transmission_PHS = float(transmission_data.loc[2050, 'PHS'])

    CRC_PHS = discount_factor / (1 - (1 + discount_factor)**(-L_PHS))
    capital_PHS = CRC_PHS * CAPEX_PHS
    transmission_capital_PHS = CRC_PHS * transmission_PHS
    if LCOE_check == 'yes':
        print('PHS check = ' + str(capital_PHS + FOM_PHS + transmission_capital_PHS) + ' $/kW/yr')

    # LIB
    CAPEX_LIB = 855
    FOM_LIB = 21
    VOM_LIB = 0.0
    fuelcost_LIB = 0
    heatrate_LIB = 0
    L_LIB = 15
    transmission_LIB = float(transmission_data.loc[2050, 'LIB'])

    CRC_LIB = discount_factor / (1 - (1 + discount_factor)**(-L_LIB))
    capital_LIB = CRC_LIB * CAPEX_LIB
    transmission_capital_LIB = CRC_LIB * transmission_LIB
    if LCOE_check == 'yes':
        print('LIB check = ' + str(capital_LIB + FOM_LIB + transmission_capital_LIB) + ' $/kW/yr')

    # fusion
    CAPEX_fusion = fusion_OCC
    VOM_fusion = 18.4 #base 
    #VOM_fusion = 14.8 #low 
    #VOM_fusion = 33.3 #high  
    fuelcost_fusion = 0
    heatrate_fusion = 0
    L_fusion = 40
    transmission_fusion = float(transmission_data.loc[2050, 'fusion'])

    CRC_fusion = discount_factor / (1 - (1 + discount_factor)**(-L_fusion))
    capital_fusion = CRC_fusion * CAPEX_fusion
    FOM_fusion = 188
    transmission_capital_fusion = CRC_fusion * transmission_fusion
    if LCOE_check == 'yes':
        print('fusion check = ' + str((capital_fusion + FOM_fusion + transmission_capital_fusion) * 1000 / hours_in_a_year / CF_fusion + VOM_fusion) + ' $/MWh')
        
    # geo
    CAPEX_geo = 5156
    FOM_geo = 104
    VOM_geo = 0
    fuelcost_geo = 0
    heatrate_geo = 0
    L_geo = 30
    transmission_geo = float(transmission_data.loc[2050, 'geo'])

    CRC_geo = discount_factor / (1 - (1 + discount_factor)**(-L_geo))
    capital_geo = CRC_geo * CAPEX_geo
    transmission_capital_geo = CRC_geo * transmission_geo
    if LCOE_check == 'yes':
        print('geo check = ' + str((capital_geo + FOM_geo + transmission_capital_geo) * 1000 / hours_in_a_year / CF_geo + VOM_geo) + ' $/MWh')
        
    # nuclear
    CAPEX_nuclear = 6668
    FOM_nuclear = 152
    VOM_nuclear = 2
    fuelcost_nuclear = 0.67
    heatrate_nuclear = 10.45
    L_nuclear = 60
    transmission_nuclear = float(transmission_data.loc[2050, 'nuclear'])

    CRC_nuclear = discount_factor / (1 - (1 + discount_factor)**(-L_nuclear))
    capital_nuclear = CRC_nuclear * CAPEX_nuclear
    transmission_capital_nuclear = CRC_solar * transmission_nuclear
    if LCOE_check == 'yes':
        print('nuclear check = ' + str((capital_nuclear + FOM_nuclear + transmission_capital_nuclear) * 1000 / hours_in_a_year / CF_nuclear + VOM_nuclear + fuelcost_nuclear * heatrate_nuclear) + ' $/MWh')

    # LIBshort
    CAPEX_LIBshort = 556
    FOM_LIBshort = 14
    VOM_LIBshort = 0
    fuelcost_LIBshort = 0
    heatrate_LIBshort = 0
    L_LIBshort = 15
    transmission_LIBshort = float(transmission_data.loc[2050, 'LIBshort'])

    CRC_LIBshort = discount_factor / (1 - (1 + discount_factor)**(-L_LIBshort))
    capital_LIBshort = CRC_LIBshort * CAPEX_LIBshort
    transmission_capital_LIBshort = CRC_LIBshort * transmission_LIBshort
    if LCOE_check == 'yes':
        print('LIBshort check = ' + str(capital_LIBshort + FOM_LIBshort + transmission_capital_LIBshort) + ' $/kW/yr')
        
    # LIBlong
    CAPEX_LIBlong = 1453
    FOM_LIBlong = 35
    VOM_LIBlong = 0
    fuelcost_LIBlong = 0
    heatrate_LIBlong = 0
    L_LIBlong = 15
    transmission_LIBlong = float(transmission_data.loc[2050, 'LIBlong'])

    CRC_LIBlong = discount_factor / (1 - (1 + discount_factor)**(-L_LIBlong))
    capital_LIBlong = CRC_LIBlong * CAPEX_LIBlong
    transmission_capital_LIBlong = CRC_LIBlong * transmission_LIBlong
    if LCOE_check == 'yes':
        print('LIBlong check = ' + str(capital_LIBlong + FOM_LIBlong + transmission_capital_LIBlong) + ' $/kW/yr')
        

    return (capital_solar, FOM_solar, VOM_solar, fuelcost_solar, heatrate_solar, transmission_capital_solar, \
            capital_wind, FOM_wind, VOM_wind, fuelcost_wind, heatrate_wind, transmission_capital_wind, \
            capital_offw, FOM_offw, VOM_offw, fuelcost_offw, heatrate_offw, transmission_capital_offw, \
            capital_conventional, FOM_conventional, VOM_conventional, fuelcost_conventional, heatrate_conventional, transmission_capital_conventional, \
            capital_RoR, FOM_RoR, VOM_RoR, fuelcost_RoR, heatrate_RoR, transmission_capital_RoR, \
            capital_ngct, FOM_ngct, VOM_ngct, fuelcost_ngct, heatrate_ngct, transmission_capital_ngct, \
            capital_ngcc, FOM_ngcc, VOM_ngcc, fuelcost_ngcc, heatrate_ngcc, transmission_capital_ngcc, \
            capital_ngccs, FOM_ngccs, VOM_ngccs, fuelcost_ngccs, heatrate_ngccs, transmission_capital_ngccs, \
            capital_LIB, FOM_LIB, VOM_LIB, fuelcost_LIB, heatrate_LIB, transmission_capital_LIB, \
            capital_PHS, FOM_PHS, VOM_PHS, fuelcost_PHS, heatrate_PHS, transmission_capital_PHS, \
            capital_fusion, FOM_fusion, VOM_fusion, fuelcost_fusion, heatrate_fusion, transmission_capital_fusion, \
            capital_geo, FOM_geo, VOM_geo, fuelcost_geo, heatrate_geo, transmission_capital_geo, \
            capital_nuclear, FOM_nuclear, VOM_nuclear, fuelcost_nuclear, heatrate_nuclear, transmission_capital_nuclear, \
            capital_LIBshort, FOM_LIBshort, VOM_LIBshort, fuelcost_LIBshort, heatrate_LIBshort, transmission_capital_LIBshort, \
            capital_LIBlong, FOM_LIBlong, VOM_LIBlong, fuelcost_LIBlong, heatrate_LIBlong, transmission_capital_LIBlong)

def collecting_conventional_CFs(region, year):
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

def collecting_offw_CFs(region, year):
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

def gathering_emissions_values():
    LCA_check = 'no'  # 'yes'

    CF_solar = 0.2122
    CF_wind = 0.3723
    CF_offw = 0.3987
    CF_conventional = 0.42
    CF_RoR = 0.615
    CF_ngct = 0.3116
    CF_ngcc = 0.5061
    CF_ngccs = 0.5061
    CF_fusion = 0.85
    CF_geo = 0.9
    CF_nuclear = 0.927

    
    # emissions from capacity (gCO2/kW/yr)
    emissions_GC_solar = 42410
    emissions_GC_wind = 23389
    emissions_GC_offw = 39420
    emissions_GC_conventional = 110323
    emissions_GC_RoR = 26406
    emissions_GC_fusion = 32116
    emissions_GC_ngct = 32755
    emissions_GC_ngcc = 39900
    emissions_GC_ngccs = 48768
    emissions_GC_LIB = 19440
    emissions_GC_PHS = 3146
    emissions_GC_LIBlong = 38880
    emissions_GC_LIBshort = 9720
    emissions_GC_geo = 63246
    emissions_GC_nuclear = 4104


    # emisions from operation (gCO2/kWh)
    emissions_output_solar = 0
    emissions_output_wind = 0
    emissions_output_offw = 0
    emissions_output_conventional = 0
    emissions_output_RoR = 0
    emissions_output_fusion = 0.258 #base
    #emissions_output_fusion = 0.1 #low
    #emissions_output_fusion = 1.774 #high
    emissions_output_ngct = 820
    emissions_output_ngcc = 505
    emissions_output_ngccs = 174
    emissions_output_LIB = 0
    emissions_output_PHS = 0
    emissions_output_LIBlong = 0
    emissions_output_LIBshort = 0
    emissions_output_geo = 3.8
    emissions_output_nuclear = 7.9

    if LCA_check == 'yes':
        print('ngct check = ' + str(emissions_output_ngct) + ' gCO2/kWh')
        print('ngcc check = ' + str(emissions_output_ngcc) + ' gCO2/kWh')
        print('ngccs check = ' + str(emissions_output_ngccs) + ' gCO2/kWh')
        print('fusion check = ' + str(emissions_output_fusion) + ' gCO2/kWh')
        print('geo check = ' + str(emissions_output_geo) + ' gCO2/kWh')
        print('nuclear check = ' + str(emissions_output_nuclear) + ' gCO2/kWh')

    return (emissions_GC_solar, emissions_GC_wind, emissions_GC_offw, emissions_GC_conventional, emissions_GC_RoR, emissions_GC_fusion, \
            emissions_GC_ngct, emissions_GC_ngcc, emissions_GC_ngccs, emissions_GC_LIB, emissions_GC_PHS, \
            emissions_GC_LIBshort, emissions_GC_LIBlong, emissions_GC_geo, emissions_GC_nuclear, \
            emissions_output_solar, emissions_output_wind, emissions_output_offw, emissions_output_conventional, emissions_output_RoR, emissions_output_fusion, \
            emissions_output_ngct, emissions_output_ngcc, emissions_output_ngccs, emissions_output_LIB, emissions_output_PHS, \
            emissions_output_LIBshort, emissions_output_LIBlong, emissions_output_geo, emissions_output_nuclear)

def run(region, optimize_shares, year, area_width, sites, cap, e_cap, e_tax, case_location, baseload, forced_fusion, no_limits, no_fusion, exact_fusion, fusion_OCC, consider_current_infrustructure, nuclear_buildout):
    e_tax /= 1000000  # $/g
    if region == "Northeast" and area_width == '360':
        area_width = '240'

    if region == "Northeast" and sites == '169':
        sites = '81'

    """Gathering input data"""
    D_underlined = collecting_D(region)
    D_total = sum(D_underlined)
    (G_solar_perkW, CF_solar) = collecting_G_and_CF_for_VRE('solar', area_width, sites, year, region)
    (G_wind_perkW, CF_wind) = collecting_G_and_CF_for_VRE('wind', area_width, sites, year, region)
    (G_RoR_perkW, CF_RoR) = collecting_G_and_CF_for_ror(region, year)
    days_in_month = pd.DataFrame(np.array([[31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]]), columns=['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])
    CF_monthly_conventional = collecting_conventional_CFs(region, year)
    CF_hydro = CF_monthly_conventional.mean()
    (G_offw_perkW, CF_offw) = collecting_offw_CFs(region, year)
    G_offw_perkW_df = G_offw_perkW.to_frame()
    G_offw_perkW_df.to_csv(year + '_G_offw_perkW_df.csv')

    """setting cost and emissions values"""
    (capital_solar, FOM_solar, VOM_solar, fuelcost_solar, heatrate_solar, transmission_solar, \
     capital_wind, FOM_wind, VOM_wind, fuelcost_wind, heatrate_wind, transmission_wind, \
     capital_offw, FOM_offw, VOM_offw, fuelcost_offw, heatrate_offw, transmission_offw, \
     capital_conventional, FOM_conventional, VOM_conventional, fuelcost_conventional, heatrate_conventional, transmission_conventional, \
     capital_RoR, FOM_RoR, VOM_RoR, fuelcost_RoR, heatrate_RoR, transmission_RoR, \
     capital_ngct, FOM_ngct, VOM_ngct, fuelcost_ngct, heatrate_ngct, transmission_ngct, \
     capital_ngcc, FOM_ngcc, VOM_ngcc, fuelcost_ngcc, heatrate_ngcc, transmission_ngcc, \
     capital_ngccs, FOM_ngccs, VOM_ngccs, fuelcost_ngccs, heatrate_ngccs, transmission_ngccs, \
     capital_LIB, FOM_LIB, VOM_LIB, fuelcost_LIB, heatrate_LIB, transmission_LIB, \
     capital_PHS, FOM_PHS, VOM_PHS, fuelcost_PHS, heatrate_PHS, transmission_PHS, \
     capital_fusion, FOM_fusion, VOM_fusion, fuelcost_fusion, heatrate_fusion, transmission_fusion, \
     capital_geo, FOM_geo, VOM_geo, fuelcost_geo, heatrate_geo, transmission_geo, \
     capital_nuclear, FOM_nuclear, VOM_nuclear, fuelcost_nuclear, heatrate_nuclear, transmission_nuclear, \
     capital_LIBshort, FOM_LIBshort, VOM_LIBshort, fuelcost_LIBshort, heatrate_LIBshort, transmission_LIBshort, \
     capital_LIBlong, FOM_LIBlong, VOM_LIBlong, fuelcost_LIBlong, heatrate_LIBlong, transmission_LIBlong) = gathering_financial_values(fusion_OCC, region)

    (emissions_GC_solar, emissions_GC_wind, emissions_GC_offw, emissions_GC_conventional, emissions_GC_RoR, emissions_GC_fusion, \
     emissions_GC_ngct, emissions_GC_ngcc, emissions_GC_ngccs, emissions_GC_LIB, emissions_GC_PHS, \
     emissions_GC_LIBshort, emissions_GC_LIBlong, emissions_GC_geo, emissions_GC_nuclear, \
     emissions_output_solar, emissions_output_wind, emissions_output_offw, emissions_output_conventional, emissions_output_RoR, emissions_output_fusion, \
     emissions_output_ngct, emissions_output_ngcc, emissions_output_ngccs, emissions_output_LIB, emissions_output_PHS, \
     emissions_output_LIBshort, emissions_output_LIBlong, emissions_output_geo, emissions_output_nuclear) = gathering_emissions_values()

    """setting other parameters"""
    delivery_costs_df = pd.read_csv(os.path.join(PATH, 'TD_costs', 'distribution_data.csv'), dtype='unicode', index_col=0)
    delivery_cost = float(delivery_costs_df.loc[2050, region]) * 10 # cents/kWh > $/MWh
    TD_losses = 4.7 / 100  # percent loss
    carbon_captured_ngccs = emissions_output_ngcc - emissions_output_ngccs

    # source = https://dualchallenge.npc.org/files/CCUS-Chap_2-030521.pdf
    if region == 'Atlantic' or region == 'Northeast' or region == 'Central' or region == 'Southeast' or region == 'California':
        cost_carbon_storage = (7 + 240 * 0.05) / 10 ** 6  # $/ton --> $/gram
    elif region == 'Texas':
        cost_carbon_storage = (7.5 + 240 * 0.05) / 10 ** 6
    elif region == 'Northwest' or region == 'North Central':
        cost_carbon_storage = (11 + 240 * 0.05) / 10 ** 6
    elif region == 'Southwest':
        cost_carbon_storage = (8 + 240 * 0.05) / 10 ** 6

    eta_c_LIB = 0.92
    eta_d_LIB = 0.92

    eta_c_PHS = 0.90
    eta_d_PHS = 0.90

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
    model.GC_fusion = pe.Var(domain=pe.NonNegativeReals)
    model.GC_ngct = pe.Var(domain=pe.NonNegativeReals)
    model.GC_ngcc = pe.Var(domain=pe.NonNegativeReals)
    model.GC_ngccs = pe.Var(domain=pe.NonNegativeReals)
    model.GC_LIB = pe.Var(domain=pe.NonNegativeReals)  # power
    model.GC_PHS = pe.Var(domain=pe.NonNegativeReals)  # power
    model.GC_LIBlong = pe.Var(domain=pe.NonNegativeReals)  # power
    model.GC_LIBshort = pe.Var(domain=pe.NonNegativeReals)  # power
    model.GC_geo = pe.Var(domain=pe.NonNegativeReals)
    model.GC_nuclear = pe.Var(domain=pe.NonNegativeReals)
    
    #early_retire technologies
    model.GC_ngct_early_retires = pe.Var(domain=pe.NonNegativeReals)
    model.GC_ngcc_early_retires = pe.Var(domain=pe.NonNegativeReals)

    # setting hourly power output of dispatchables
    model.output_conventional = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_ngct = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_ngcc = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_ngccs = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_fusion = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_geo = pe.Var(model.hour, domain=pe.NonNegativeReals)
    model.output_nuclear = pe.Var(model.hour, domain=pe.NonNegativeReals)

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
                 capital_conventional * model.GC_conventional + capital_RoR * model.GC_RoR + capital_fusion * model.GC_fusion + \
                 capital_ngct * model.GC_ngct + capital_ngcc * model.GC_ngcc + capital_ngccs * model.GC_ngccs + \
                 capital_LIB * model.GC_LIB + capital_PHS * model.GC_PHS + \
                 capital_LIBlong * model.GC_LIBlong + capital_LIBshort * model.GC_LIBshort + \
                 capital_geo * model.GC_geo + capital_nuclear * model.GC_nuclear
    
    transmission_costs = transmission_solar * model.GC_solar + transmission_wind * model.GC_wind + transmission_offw * model.GC_offw + \
                 transmission_conventional * model.GC_conventional + transmission_RoR * model.GC_RoR + transmission_fusion * model.GC_fusion + \
                 transmission_ngct * model.GC_ngct + transmission_ngcc * model.GC_ngcc + transmission_ngccs * model.GC_ngccs + \
                 transmission_LIB * model.GC_LIB + transmission_PHS * model.GC_PHS + \
                 transmission_LIBlong * model.GC_LIBlong + transmission_LIBshort * model.GC_LIBshort + \
                 transmission_geo * model.GC_geo + transmission_nuclear * model.GC_nuclear

    FOM_costs = FOM_solar * model.GC_solar + FOM_wind * model.GC_wind + FOM_offw * model.GC_offw + \
            FOM_conventional * model.GC_conventional + FOM_RoR * model.GC_RoR + FOM_fusion * model.GC_fusion + \
            FOM_ngct * (model.GC_ngct - model.GC_ngct_early_retires) + FOM_ngcc * (model.GC_ngcc - model.GC_ngcc_early_retires) + FOM_ngccs * model.GC_ngccs + \
            FOM_LIB * model.GC_LIB + FOM_PHS * model.GC_PHS + \
            FOM_LIBlong * model.GC_LIBlong + FOM_LIBshort * model.GC_LIBshort + \
            FOM_geo * model.GC_geo + FOM_nuclear * model.GC_nuclear
    
    capacity_emissions = emissions_GC_solar * model.GC_solar + emissions_GC_wind * model.GC_wind + emissions_GC_offw * model.GC_offw + \
             emissions_GC_conventional * model.GC_conventional + emissions_GC_RoR * model.GC_RoR + emissions_GC_fusion * model.GC_fusion + \
             emissions_GC_ngct * model.GC_ngct + emissions_GC_ngcc * model.GC_ngcc + emissions_GC_ngccs * model.GC_ngccs + \
             emissions_GC_LIB * model.GC_LIB + emissions_GC_PHS * model.GC_PHS + \
             emissions_GC_LIBlong * model.GC_LIBlong + emissions_GC_LIBshort * model.GC_LIBshort + \
             emissions_GC_geo * model.GC_geo + emissions_GC_nuclear * model.GC_nuclear

    if five_years == 'yes':
        capacity_costs *= 7
        transmission_costs *= 7
        FOM_costs *= 7
        capacity_emissions *= 7

    # setting operation-related costs
    VOM_costs = (VOM_ngct * sum(model.output_ngct[i] for i in model.hour) + VOM_ngcc * sum(model.output_ngcc[i] for i in model.hour) + VOM_ngccs * sum(model.output_ngccs[i] for i in model.hour) + \
            VOM_fusion * sum(model.output_fusion[i] for i in model.hour) + VOM_nuclear * sum(model.output_nuclear[i] for i in model.hour)) / 1000

    fuel_costs = (fuelcost_ngct * heatrate_ngct * sum(model.output_ngct[i] for i in model.hour) + fuelcost_ngcc * heatrate_ngcc * sum(model.output_ngcc[i] for i in model.hour) + \
                 fuelcost_ngccs * heatrate_ngccs * sum(model.output_ngccs[i] for i in model.hour) + fuelcost_nuclear * heatrate_nuclear * sum(model.output_nuclear[i] for i in model.hour)) / 1000

    operational_emissions = emissions_output_ngct * sum(model.output_ngct[i] for i in model.hour) + emissions_output_ngcc * sum(model.output_ngcc[i] for i in model.hour) + \
                            emissions_output_ngccs * sum(model.output_ngccs[i] for i in model.hour) + emissions_output_fusion * sum(model.output_fusion[i] for i in model.hour) + \
                            emissions_output_geo * sum(model.output_geo[i] for i in model.hour) + emissions_output_nuclear * sum(model.output_nuclear[i] for i in model.hour)

    emissions_captured_costs = carbon_captured_ngccs * sum(model.output_ngccs[i] for i in model.hour) * cost_carbon_storage
    emissions_costs = (capacity_emissions + operational_emissions) * e_tax
    objective_function = capacity_costs + FOM_costs + VOM_costs + fuel_costs + emissions_costs + emissions_captured_costs + transmission_costs
    model.cost = pe.Objective(sense=pe.minimize, expr=objective_function)
    # model.cost = pe.Objective(sense=pe.minimize, expr=capacity_emissions + operational_emissions)
    
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
    model.fusion_output_constraint = pe.ConstraintList()
    fusion_maintenance_schedules = pd.read_csv("maintenance_schedules_by_region.csv")
    fusion_maintenance_schedule = fusion_maintenance_schedules[region]
    fusion_maintenance_schedule_extended = pd.concat([fusion_maintenance_schedule] * 7, ignore_index=True)
    fusion_maintenance_schedule_extended = fusion_maintenance_schedule_extended.reset_index(drop=True)
    
    model.geo_output_constraint = pe.ConstraintList()
    model.nuclear_output_constraint = pe.ConstraintList()
    model.baseload_nuclear_constraint = pe.ConstraintList()
    for hour_number in model.hour:
        model.power_must_be_served.add(model.ren_2_D[hour_number] + model.therm_2_D[hour_number] + (model.LIB_2_D[hour_number] + model.LIBshort_2_D[hour_number] + model.LIBlong_2_D[hour_number]) * eta_d_LIB + model.PHS_2_D[hour_number] * eta_d_PHS == model.D[hour_number])

        model.increase_in_battery_lte_CPC.add(model.ren_2_LIB[hour_number] + model.therm_2_LIB[hour_number] <= model.GC_LIB)
        model.increase_in_batteryshort_lte_CPC.add(model.ren_2_LIBshort[hour_number] + model.therm_2_LIBshort[hour_number] <= model.GC_LIBshort)
        model.increase_in_batterylong_lte_CPC.add(model.ren_2_LIBlong[hour_number] + model.therm_2_LIBlong[hour_number] <= model.GC_LIBlong)
        model.increase_in_phs_lte_CPC.add(model.ren_2_PHS[hour_number] + model.therm_2_PHS[hour_number] <= model.GC_PHS)
        model.decrease_in_battery_lte_DPC.add(model.LIB_2_D[hour_number] <= model.GC_LIB)
        model.decrease_in_batteryshort_lte_DPC.add(model.LIBshort_2_D[hour_number] <= model.GC_LIBshort)
        model.decrease_in_batterylong_lte_DPC.add(model.LIBlong_2_D[hour_number] <= model.GC_LIBlong)
        model.decrease_in_phs_lte_DPC.add(model.PHS_2_D[hour_number] <= model.GC_PHS)

        model.finding_ren_G.add(model.ren_2_C[hour_number] + model.ren_2_D[hour_number] + model.ren_2_LIBshort[hour_number] + model.ren_2_LIBlong[hour_number] + \
             model.ren_2_LIB[hour_number] + model.ren_2_PHS[hour_number] == (1 - TD_losses) * \
            (model.GC_solar * G_solar_perkW[hour_number] + model.GC_wind * G_wind_perkW[hour_number] + model.GC_offw * G_offw_perkW[hour_number] + \
             model.GC_RoR * G_RoR_perkW[hour_number] + model.output_conventional[hour_number]))
        model.finding_therm_G.add(model.therm_2_D[hour_number] + model.therm_2_LIB[hour_number] + model.therm_2_LIBshort[hour_number] + \
             model.therm_2_LIBlong[hour_number] + model.therm_2_PHS[hour_number] == (1 - TD_losses) * \
            (model.output_ngct[hour_number] + model.output_ngcc[hour_number] + model.output_ngccs[hour_number] + model.output_fusion[hour_number] + \
             model.output_geo[hour_number] + model.output_nuclear[hour_number]))

        model.LIB_storage_limit.add(model.LIB_level[hour_number] <= model.GC_LIB * 4)
        model.LIBshort_storage_limit.add(model.LIBshort_level[hour_number] <= model.GC_LIBshort * 2)
        model.LIBlong_storage_limit.add(model.LIBlong_level[hour_number] <= model.GC_LIBlong * 8)
        model.PHS_storage_limit.add(model.PHS_level[hour_number] <= model.GC_PHS * 10)

        model.ngct_output_constraint.add(model.GC_ngct - model.GC_ngct_early_retires >= model.output_ngct[hour_number])
        model.ngcc_output_constraint.add(model.GC_ngcc - model.GC_ngcc_early_retires >= model.output_ngcc[hour_number])
        model.ngccs_output_constraint.add(model.GC_ngccs >= model.output_ngccs[hour_number])
        model.conventional_output_constraint.add(model.GC_conventional >= model.output_conventional[hour_number])
        model.geo_output_constraint.add(model.GC_geo >= model.output_geo[hour_number])
        model.nuclear_output_constraint.add(model.GC_nuclear >= model.output_nuclear[hour_number])
        model.baseload_nuclear_constraint.add(0.927 * model.GC_nuclear == model.output_nuclear[hour_number])
        model.fusion_output_constraint.add(model.GC_fusion * fusion_maintenance_schedule_extended[hour_number] >= model.output_fusion[hour_number])
        if baseload == 'yes':
            model.fusion_output_constraint.add(model.GC_fusion * 0.7 <= model.output_fusion[hour_number])
            model.fusion_output_constraint.add(model.GC_fusion >= model.output_fusion[hour_number])
        else:
            model.fusion_output_constraint.add(model.GC_fusion >= model.output_fusion[hour_number])

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
    model.setting_batteryshort_0_equal_to_battery_last = pe.Constraint(expr=model.LIBshort_level[0] == model.LIBshort_level[hours_of_optimization - 1])
    model.setting_batterylong_0_equal_to_battery_last = pe.Constraint(expr=model.LIBlong_level[0] == model.LIBlong_level[hours_of_optimization - 1])
    model.setting_phs_0_equal_to_phs_last = pe.Constraint(expr=model.PHS_level[0] == model.PHS_level[hours_of_optimization - 1])
    #model.fusion_CF = pe.Constraint(expr = sum(model.output_fusion[i] for i in model.hour) / hours_of_optimization <= 0.85 * model.GC_fusion)

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
        
    if region == 'California':
        demand_reduction_factor = 82253372
    elif region == 'Southwest':
        demand_reduction_factor = 40255874
    elif region == 'Southeast':
        demand_reduction_factor = 63019545
    elif region == 'Texas':
        demand_reduction_factor = 83025393
    elif region == 'Northeast':
        demand_reduction_factor = 58579211
    elif region == 'Atlantic':
        demand_reduction_factor = 161519725
    elif region == 'Northwest':
        demand_reduction_factor = 77723410
    elif region == 'North Central':
        demand_reduction_factor = 67653219
    elif region == 'Central':
        demand_reduction_factor = 68764899
        
    installs_df = pd.read_csv(os.path.join(PATH, 'installed_and_retire_capacities', 'installed_capacities_kW_' + region + '.csv'), index_col=0)
    retires_df = pd.read_csv(os.path.join(PATH, 'installed_and_retire_capacities', 'retire_capacities_kW_' + region + '.csv'), index_col=0)
    solar_2050_installs = (installs_df['solar'].sum() - retires_df['solar'].sum()) / demand_reduction_factor
    wind_2050_installs = (installs_df['wind'].sum() - retires_df['wind'].sum()) / demand_reduction_factor
    offw_2050_installs = (installs_df['offw'].sum() - retires_df['offw'].sum()) / demand_reduction_factor
    RoR_2050_installs = (installs_df['RoR'].sum() - retires_df['RoR'].sum()) / demand_reduction_factor
    conventional_2050_installs = (installs_df['hydro'].sum() - retires_df['hydro'].sum()) / demand_reduction_factor
    nuclear_2050_installs = (installs_df['nuclear'].sum() - retires_df['nuclear'].sum()) / demand_reduction_factor
    fusion_2050_installs = (installs_df['fusion'].sum() - retires_df['fusion'].sum()) / demand_reduction_factor
    geo_2050_installs = (installs_df['geo'].sum() - retires_df['geo'].sum()) / demand_reduction_factor
    ngccs_2050_installs = (installs_df['ngccs'].sum() - retires_df['ngccs'].sum()) / demand_reduction_factor
    ngcc_2050_installs = (installs_df['ngcc'].sum() - retires_df['ngcc'].sum()) / demand_reduction_factor
    ngct_2050_installs = (installs_df['ngct'].sum() - retires_df['ngct'].sum()) / demand_reduction_factor
    LIBshort_2050_installs = (installs_df['LIBshort'].sum() - retires_df['LIBshort'].sum()) / demand_reduction_factor
    LIB_2050_installs = (installs_df['LIB'].sum() - retires_df['LIB'].sum()) / demand_reduction_factor
    LIBlong_2050_installs = (installs_df['LIBlong'].sum() - retires_df['LIBlong'].sum()) / demand_reduction_factor
    PHS_2050_installs = (installs_df['PHS'].sum() - retires_df['PHS'].sum()) / demand_reduction_factor
    if consider_current_infrustructure == 'yes':
        model.solar_min = pe.Constraint(expr=model.GC_solar >= solar_2050_installs)
        model.wind_min = pe.Constraint(expr=model.GC_wind >= (installs_df['wind'].sum() - retires_df['wind'].sum()) / demand_reduction_factor)
        model.offw_min = pe.Constraint(expr=model.GC_offw >= (installs_df['offw'].sum() - retires_df['offw'].sum()) / demand_reduction_factor)
        model.RoR_min = pe.Constraint(expr=model.GC_RoR >= (installs_df['RoR'].sum() - retires_df['RoR'].sum()) / demand_reduction_factor)
        model.conventional_min = pe.Constraint(expr=model.GC_conventional >= (installs_df['hydro'].sum() - retires_df['hydro'].sum()) / demand_reduction_factor)
        model.nuclear_min = pe.Constraint(expr=model.GC_nuclear >= (installs_df['nuclear'].sum() - retires_df['nuclear'].sum()) / demand_reduction_factor)
        model.fusion_min = pe.Constraint(expr=model.GC_fusion >= (installs_df['fusion'].sum() - retires_df['fusion'].sum()) / demand_reduction_factor)
        model.geo_min = pe.Constraint(expr=model.GC_geo >= (installs_df['geo'].sum() - retires_df['geo'].sum()) / demand_reduction_factor)
        model.ngccs_min = pe.Constraint(expr=model.GC_ngccs >= (installs_df['ngccs'].sum() - retires_df['ngccs'].sum()) / demand_reduction_factor)
        model.ngcc_min = pe.Constraint(expr=model.GC_ngcc >= (installs_df['ngcc'].sum() - retires_df['ngcc'].sum()) / demand_reduction_factor)
        model.ngct_min = pe.Constraint(expr=model.GC_ngct >= (installs_df['ngct'].sum() - retires_df['ngct'].sum()) / demand_reduction_factor)
        model.LIBshort_min = pe.Constraint(expr=model.GC_LIBshort >= (installs_df['LIBshort'].sum() - retires_df['LIBshort'].sum()) / demand_reduction_factor)
        model.LIB_min = pe.Constraint(expr=model.GC_LIB >= (installs_df['LIB'].sum() - retires_df['LIB'].sum()) / demand_reduction_factor)
        model.LIBlong_min = pe.Constraint(expr=model.GC_LIBlong >= (installs_df['LIBlong'].sum() - retires_df['LIBlong'].sum()) / demand_reduction_factor)
        model.PHS_min = pe.Constraint(expr=model.GC_PHS >= (installs_df['PHS'].sum() - retires_df['PHS'].sum()) / demand_reduction_factor)

    if region == 'California':
        demand_reduction_factor = 82253372
        PHS_expansion_potential = 324133 * 1000  # kW
        RoR_expansion_potential = 3360 * 1000  # kW
        conventional_expansion_potential = 11016 * 1000  # kW
        offw_expansion_potential = 587800000  # kW
        wind_expansion_potential = 34000000  # kW
        geo_expansion_potential = 17000000  # kW
        solar_expansion_potential = 4197679565  # kW
    elif region == 'Southwest':
        demand_reduction_factor = 40255874
        PHS_expansion_potential = 554313 * 1000  # kW
        RoR_expansion_potential = 1432 * 1000  # kW
        conventional_expansion_potential = 4186 * 1000  # kW
        offw_expansion_potential = 0  # kW
        wind_expansion_potential = 503000000  # kW
        geo_expansion_potential = 3000000  # kW
        solar_expansion_potential = 12337092354.0497  # kW
    elif region == 'Southeast':
        demand_reduction_factor = 63019545
        PHS_expansion_potential = 33584 * 1000  # kW
        RoR_expansion_potential = 1226 * 1000  # kW
        conventional_expansion_potential = 6461 * 1000  # kW
        offw_expansion_potential = 60400000  # kW
        wind_expansion_potential = 2000000  # kW
        geo_expansion_potential = 0  # kW
        solar_expansion_potential = 5285108398.70515  # kW
    elif region == 'Texas':
        demand_reduction_factor = 83025393
        PHS_expansion_potential = 37115 * 1000  # kW
        RoR_expansion_potential = 1367 * 1000  # kW
        conventional_expansion_potential = 1372 * 1000  # kW
        offw_expansion_potential = 278400000  # kW
        wind_expansion_potential = 1902000000  # kW
        geo_expansion_potential = 0  # kW
        solar_expansion_potential = 20625551648.634  # kW
    elif region == 'Northeast':
        demand_reduction_factor = 58579211
        PHS_expansion_potential = 16768 * 1000  # kW
        RoR_expansion_potential = 3992 * 1000  # kW
        conventional_expansion_potential = 7160 * 1000  # kW
        offw_expansion_potential = 539200000  # kW
        wind_expansion_potential = 45000000  # kW
        geo_expansion_potential = 0  # kW
        solar_expansion_potential = 1831772119.90073  # kW
    elif region == 'Atlantic':
        demand_reduction_factor = 161519725
        PHS_expansion_potential = 69709 * 1000  # kW
        RoR_expansion_potential = 6134 * 1000  # kW
        conventional_expansion_potential = 6176 * 1000  # kW
        offw_expansion_potential = 318400000  # kW
        wind_expansion_potential = 66000000  # kW
        geo_expansion_potential = 0  # kW
        solar_expansion_potential = 6062773540.48102  # kW
    elif region == 'Northwest':
        demand_reduction_factor = 77723410
        PHS_expansion_potential = 209510 * 1000  # kW
        RoR_expansion_potential = 26580 * 1000  # kW
        conventional_expansion_potential = 39523 * 1000  # kW
        offw_expansion_potential = 341800000  # kW
        wind_expansion_potential = 1966000000  # kW
        geo_expansion_potential = 13750000  # kW
        solar_expansion_potential = 22970481722.9524  # kW
    elif region == 'North Central':
        demand_reduction_factor = 67653219
        PHS_expansion_potential = 0 * 1000  # kW
        RoR_expansion_potential = 2156 * 1000  # kW
        conventional_expansion_potential = 1901 * 1000  # kW
        offw_expansion_potential = 620200000  # kW
        wind_expansion_potential = 1223000000  # kW
        geo_expansion_potential = 0  # kW
        solar_expansion_potential = 17337746320.165  # kW
    elif region == 'Central':
        demand_reduction_factor = 68764899
        PHS_expansion_potential = 8174 * 1000  # kW
        RoR_expansion_potential = 5993 * 1000  # kW
        conventional_expansion_potential = 6891 * 1000  # kW
        offw_expansion_potential = 385500000  # kW
        wind_expansion_potential = 682000000  # kW
        geo_expansion_potential = 0  # kW
        solar_expansion_potential = 16550309530.7519  # kW

    if no_limits == 'no':
        if PHS_2050_installs > PHS_expansion_potential / demand_reduction_factor:
            model.PHS_max = pe.Constraint(expr=model.GC_PHS == PHS_2050_installs)
        else:
            model.PHS_max = pe.Constraint(expr=model.GC_PHS <= PHS_expansion_potential / demand_reduction_factor)
        if RoR_2050_installs > RoR_expansion_potential / demand_reduction_factor:        
            model.RoR_max = pe.Constraint(expr=model.GC_RoR == RoR_2050_installs)
        else:
            model.RoR_max = pe.Constraint(expr=model.GC_RoR <= RoR_expansion_potential / demand_reduction_factor)
        if conventional_2050_installs > conventional_expansion_potential / demand_reduction_factor:    
            model.conventional_max = pe.Constraint(expr=model.GC_conventional == conventional_2050_installs)
        else:
            model.conventional_max = pe.Constraint(expr=model.GC_conventional <= conventional_expansion_potential / demand_reduction_factor) 
        if offw_2050_installs > offw_expansion_potential / demand_reduction_factor:   
            model.offw_max = pe.Constraint(expr=model.GC_offw == offw_2050_installs)
        else:
            model.offw_max = pe.Constraint(expr=model.GC_offw <= offw_expansion_potential / demand_reduction_factor)
        if wind_2050_installs > wind_expansion_potential / demand_reduction_factor:   
            model.wind_max = pe.Constraint(expr=model.GC_wind == wind_2050_installs)
        else:
            model.wind_max = pe.Constraint(expr=model.GC_wind <= wind_expansion_potential / demand_reduction_factor)
        if geo_2050_installs > geo_expansion_potential / demand_reduction_factor:          
            model.geo_max = pe.Constraint(expr=model.GC_geo == geo_2050_installs)
        else:
            model.geo_max = pe.Constraint(expr=model.GC_geo <= geo_expansion_potential / demand_reduction_factor)
        if solar_2050_installs > solar_expansion_potential / demand_reduction_factor:  
            model.solar_max = pe.Constraint(expr=model.GC_solar == solar_2050_installs)
        else:
            model.solar_max = pe.Constraint(expr=model.GC_solar <= solar_expansion_potential / demand_reduction_factor)
    
    if nuclear_buildout == 'no':
        model.nuclear_size_limit = pe.Constraint(expr=model.GC_nuclear == (installs_df['nuclear'].sum() - retires_df['nuclear'].sum()) / demand_reduction_factor)     
                  
    if forced_fusion == 'yes':
        model.no_fusion = pe.Constraint(expr = model.GC_fusion >= 0.1)
    elif no_fusion == 'yes':
        model.no_fusion = pe.Constraint(expr=model.GC_fusion == 0)
    elif exact_fusion == 'yes':
        model.no_fusion = pe.Constraint(expr=model.GC_fusion == 0.1)
        
    solver = po.SolverFactory('gurobi', solver_io='python')
    result = solver.solve(model, tee=True)

    # data post-processing
    """demand satisfied from:"""
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

    """outputting CF profiles"""
    CF_curves = pd.DataFrame(index=range(hours_of_optimization))
    conventional_CF_curves = pd.DataFrame()
    CF_curves['solar'] = G_solar_perkW
    CF_curves['wind'] = G_wind_perkW
    CF_curves['offw'] = G_offw_perkW
    CF_curves['RoR'] = G_RoR_perkW
    conventional_CF_curves['conventional'] = CF_monthly_conventional
    CF_curves.to_csv(os.path.join(case_location, r'CF_curves.csv'))
    conventional_CF_curves.to_csv(os.path.join(case_location, r'conventional_CF_curves.csv'))

    """energy_storage_levels"""
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

    """generation to:"""
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

    """dispatchable output"""
    output_conventional = pd.DataFrame.from_dict(model.output_conventional.extract_values(), orient='index', columns=[str(model.hour)])
    output_ngct = pd.DataFrame.from_dict(model.output_ngct.extract_values(), orient='index', columns=[str(model.hour)])
    output_ngcc = pd.DataFrame.from_dict(model.output_ngcc.extract_values(), orient='index', columns=[str(model.hour)])
    output_ngccs = pd.DataFrame.from_dict(model.output_ngccs.extract_values(), orient='index', columns=[str(model.hour)])
    output_fusion = pd.DataFrame.from_dict(model.output_fusion.extract_values(), orient='index', columns=[str(model.hour)])
    output_geo = pd.DataFrame.from_dict(model.output_geo.extract_values(), orient='index', columns=[str(model.hour)])
    output_nuclear = pd.DataFrame.from_dict(model.output_nuclear.extract_values(), orient='index', columns=[str(model.hour)])

    dispatchable_output = pd.DataFrame(index=range(hours_of_optimization))
    dispatchable_output['conventional'] = output_conventional
    dispatchable_output['nuclear'] = output_nuclear
    dispatchable_output['fusion'] = output_fusion
    dispatchable_output['geo'] = output_geo
    dispatchable_output['ngccs'] = output_ngccs
    dispatchable_output['ngcc'] = output_ngcc
    dispatchable_output['ngct'] = output_ngct
    dispatchable_output.to_csv(os.path.join(case_location, r'dispatchable_output.csv'))

    """tech sizing"""
    GC_solar = pe.value(model.GC_solar)
    GC_wind = pe.value(model.GC_wind)
    GC_offw = pe.value(model.GC_offw)
    GC_conventional = pe.value(model.GC_conventional)
    GC_RoR = pe.value(model.GC_RoR)
    GC_fusion = pe.value(model.GC_fusion)
    GC_ngct = pe.value(model.GC_ngct - model.GC_ngct_early_retires)
    GC_ngcc = pe.value(model.GC_ngcc - model.GC_ngcc_early_retires)
    GC_ngccs = pe.value(model.GC_ngccs)
    GC_LIB = pe.value(model.GC_LIB)
    GC_PHS = pe.value(model.GC_PHS)
    GC_nuclear = pe.value(model.GC_nuclear)
    GC_geo = pe.value(model.GC_geo)
    GC_LIBshort = pe.value(model.GC_LIBshort)
    GC_LIBlong = pe.value(model.GC_LIBlong)
    GC_ngct_early_retires = pe.value(model.GC_ngct_early_retires)
    GC_ngcc_early_retires = pe.value(model.GC_ngcc_early_retires)

    tech_sizes = pd.DataFrame()
    tech_sizes.loc[0, 'solar'] = GC_solar
    tech_sizes.loc[0, 'wind'] = GC_wind
    tech_sizes.loc[0, 'offw'] = GC_offw
    tech_sizes.loc[0, 'RoR'] = GC_RoR
    tech_sizes.loc[0, 'conventional'] = GC_conventional
    tech_sizes.loc[0, 'nuclear'] = GC_nuclear
    tech_sizes.loc[0, 'fusion'] = GC_fusion
    tech_sizes.loc[0, 'geo'] = GC_geo
    tech_sizes.loc[0, 'ngccs'] = GC_ngccs
    tech_sizes.loc[0, 'ngcc'] = GC_ngcc
    tech_sizes.loc[0, 'ngct'] = GC_ngct

    tech_sizes.loc[0, 'LIBshort'] = GC_LIBshort
    tech_sizes.loc[0, 'LIB'] = GC_LIB
    tech_sizes.loc[0, 'LIBlong'] = GC_LIBlong
    tech_sizes.loc[0, 'PHS'] = GC_PHS
    tech_sizes.to_csv(os.path.join(case_location, r'tech_sizes.csv'))
    
    early_retires_sizes = pd.DataFrame()
    early_retires_sizes.loc[0, 'ngct'] = GC_ngct_early_retires
    early_retires_sizes.loc[0, 'ngcc'] = GC_ngcc_early_retires
    early_retires_sizes.to_csv(os.path.join(case_location, r'early_retires_sizes.csv'))
    
    """emissions breakdown by type"""
    operational_emissions = pe.value(operational_emissions) / 8760
    capacity_emissions = pe.value(capacity_emissions) / 8760

    if five_years == 'yes':
        operational_emissions /= 7
        capacity_emissions /= 7

    emissions_breakdown_by_type = pd.DataFrame()
    emissions_breakdown_by_type.loc[0, 'operations'] = operational_emissions
    emissions_breakdown_by_type.loc[0, 'capacity'] = capacity_emissions    
    emissions_breakdown_by_type.to_csv(os.path.join(case_location, r'emissions_breakdown_by_type.csv'))

    """emissions breakdown by tech"""
    solar_capacity_emissions = float(emissions_GC_solar * pe.value(model.GC_solar))
    wind_capacity_emissions = float(emissions_GC_wind * pe.value(model.GC_wind))
    offw_capacity_emissions = float(emissions_GC_offw * pe.value(model.GC_offw))
    conventional_capacity_emissions = float(emissions_GC_conventional * pe.value(model.GC_conventional))
    RoR_capacity_emissions = float(emissions_GC_RoR * pe.value(model.GC_RoR))
    fusion_capacity_emissions = float(emissions_GC_fusion * pe.value(model.GC_fusion))
    nuclear_capacity_emissions = float(emissions_GC_nuclear * pe.value(model.GC_nuclear))
    ngct_capacity_emissions = float(emissions_GC_ngct * pe.value(model.GC_ngct))
    ngcc_capacity_emissions = float(emissions_GC_ngcc * pe.value(model.GC_ngcc))
    ngccs_capacity_emissions = float(emissions_GC_ngccs * pe.value(model.GC_ngccs))
    LIB_capacity_emissions = float(emissions_GC_LIB * pe.value(model.GC_LIB))
    LIBshort_capacity_emissions = float(emissions_GC_LIBshort * pe.value(model.GC_LIBshort))
    LIBlong_capacity_emissions = float(emissions_GC_LIBlong * pe.value(model.GC_LIBlong))
    PHS_capacity_emissions = float(emissions_GC_PHS * pe.value(model.GC_PHS))
    geo_capacity_emissions = float(emissions_GC_geo * pe.value(model.GC_geo))   
    
    ngct_operation_emissions = float(output_ngct.sum() * emissions_output_ngct)
    ngcc_operation_emissions = float(output_ngcc.sum() * emissions_output_ngcc)
    ngccs_operation_emissions = float(output_ngccs.sum() * emissions_output_ngccs)
    nuclear_operation_emissions = float(output_nuclear.sum() * emissions_output_nuclear)
    geo_operation_emissions = float(output_geo.sum() * emissions_output_geo)
    fusion_operation_emissions = float(output_fusion.sum() * emissions_output_fusion)

    if five_years == 'yes':
        ngct_operation_emissions /= 7
        ngcc_operation_emissions /= 7
        ngccs_operation_emissions /= 7
        nuclear_operation_emissions /= 7
        geo_operation_emissions /= 7
        fusion_operation_emissions /= 7

    emissions_by_tech = pd.Series(dtype='float64')
    emissions_by_tech['solar'] = solar_capacity_emissions / 8760 
    emissions_by_tech['wind'] = wind_capacity_emissions / 8760 
    emissions_by_tech['offw'] = offw_capacity_emissions / 8760 
    emissions_by_tech['conventional'] = conventional_capacity_emissions / 8760 
    emissions_by_tech['RoR'] = RoR_capacity_emissions / 8760 
    emissions_by_tech['LIB'] = LIB_capacity_emissions / 8760 
    emissions_by_tech['LIBshort'] = LIBshort_capacity_emissions / 8760 
    emissions_by_tech['LIBlong'] = LIBlong_capacity_emissions / 8760 
    emissions_by_tech['PHS'] = PHS_capacity_emissions / 8760 
    emissions_by_tech['fusion'] = (fusion_capacity_emissions + fusion_operation_emissions) / 8760 
    emissions_by_tech['ngccs'] = (ngccs_operation_emissions + ngccs_capacity_emissions) / 8760
    emissions_by_tech['ngcc'] = (ngcc_operation_emissions + ngcc_capacity_emissions) / 8760
    emissions_by_tech['ngct'] = (ngct_operation_emissions + ngct_capacity_emissions) / 8760
    emissions_by_tech['nuclear'] = (nuclear_operation_emissions + nuclear_capacity_emissions) / 8760
    emissions_by_tech['geo'] = (geo_operation_emissions + geo_capacity_emissions) / 8760    
    emissions_by_tech.transpose().to_frame().to_csv(os.path.join(case_location, r'emissions_breakdown_by_tech.csv'))

    """cost breakdown by type"""
    capacity_costs = pe.value(capacity_costs) / 8760 * 1000
    FOM_costs = pe.value(FOM_costs) / 8760 * 1000
    VOM_costs = pe.value(VOM_costs) / 8760 * 1000
    fuel_costs = pe.value(fuel_costs) / 8760 * 1000
    emissions_tax = pe.value(emissions_costs) / 8760 * 1000
    emissions_captured_costs = pe.value(emissions_captured_costs) / 8760 * 1000
    transmission_costs = pe.value(transmission_costs) / 8760 * 1000
    delivery_costs = delivery_cost

    if five_years == 'yes':
        capacity_costs /= 7
        transmission_costs /= 7
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
    cost_breakdown_by_type.loc[0, 'transmission'] = transmission_costs
    cost_breakdown_by_type.loc[0, 'delivery'] = delivery_costs
    cost_breakdown_by_type.to_csv(os.path.join(case_location, r'cost_breakdown_by_type.csv'))

    """cost breakdown by tech"""
    solar_capacity_costs = GC_solar * (capital_solar + FOM_solar + transmission_solar)
    wind_capacity_costs = GC_wind * (capital_wind + FOM_wind + transmission_wind)
    offw_capacity_costs = GC_offw * (capital_offw + FOM_offw + transmission_offw)
    conventional_capacity_costs = GC_conventional * (capital_conventional + FOM_conventional + transmission_conventional)
    RoR_capacity_costs = GC_RoR * (capital_RoR + FOM_RoR + transmission_RoR)
    fusion_capacity_costs = GC_fusion * (capital_fusion + FOM_fusion + transmission_fusion)
    ngct_capacity_costs = GC_ngct * (capital_ngct + FOM_ngct + transmission_ngct) + GC_ngct_early_retires * (capital_ngct + transmission_ngct)
    ngcc_capacity_costs = GC_ngcc * (capital_ngcc + FOM_ngcc + transmission_ngcc) + GC_ngcc_early_retires * (capital_ngcc + transmission_ngcc)
    ngccs_capacity_costs = GC_ngccs * (capital_ngccs + FOM_ngccs + transmission_ngccs)
    LIB_capacity_costs = GC_LIB * (capital_LIB + FOM_LIB + transmission_LIB)
    PHS_capacity_costs = GC_PHS * (capital_PHS + FOM_PHS + transmission_PHS)
    geo_capacity_costs = GC_geo * (capital_geo + FOM_geo + transmission_geo)
    nuclear_capacity_costs = GC_nuclear * (capital_nuclear + FOM_nuclear + transmission_nuclear)
    LIBlong_capacity_costs = GC_LIBlong * (capital_LIBlong + FOM_LIBlong + transmission_LIBlong)
    LIBshort_capacity_costs = GC_LIBshort * (capital_LIBshort + FOM_LIBshort + transmission_LIBshort)

    fusion_operation_costs = float(output_fusion.sum() * VOM_fusion) / 1000
    ngct_operation_costs = float(output_ngct.sum() * (VOM_ngct + fuelcost_ngct * heatrate_ngct)) / 1000
    ngcc_operation_costs = float(output_ngcc.sum() * (VOM_ngcc + fuelcost_ngcc * heatrate_ngcc)) / 1000
    ngccs_operation_costs = float(output_ngccs.sum() * (VOM_ngccs + fuelcost_ngccs * heatrate_ngccs)) / 1000
    nuclear_operation_costs = float(output_nuclear.sum() * (VOM_nuclear + fuelcost_nuclear * heatrate_nuclear)) / 1000

    ngccs_carbon_capture_costs = float(output_ngccs.sum() * cost_carbon_storage * carbon_captured_ngccs)

    if five_years == 'yes':
        fusion_operation_costs /= 7
        ngct_operation_costs /= 7
        ngcc_operation_costs /= 7
        ngccs_operation_costs /= 7
        ngccs_carbon_capture_costs /= 7
        nuclear_operation_costs /= 7

    cost_by_tech = pd.Series(dtype='float64')
    cost_by_tech['solar'] = (solar_capacity_costs) / 8760 * 1000
    cost_by_tech['wind'] = (wind_capacity_costs) / 8760 * 1000
    cost_by_tech['offw'] = (offw_capacity_costs) / 8760 * 1000
    cost_by_tech['RoR'] = (RoR_capacity_costs) / 8760 * 1000
    cost_by_tech['conventional'] = (conventional_capacity_costs) / 8760 * 1000
    cost_by_tech['nuclear'] = (nuclear_capacity_costs + nuclear_operation_costs) / 8760 * 1000
    cost_by_tech['fusion'] = (fusion_capacity_costs + fusion_operation_costs) / 8760 * 1000
    cost_by_tech['geo'] = (geo_capacity_costs) / 8760 * 1000
    cost_by_tech['ngccs'] = (ngccs_capacity_costs + ngccs_operation_costs + ngccs_carbon_capture_costs) / 8760 * 1000 + emissions_by_tech['ngccs'] * e_tax / 8760 * 1000
    cost_by_tech['ngcc'] = (ngcc_capacity_costs + ngcc_operation_costs) / 8760 * 1000 + emissions_by_tech['ngcc'] * e_tax / 8760 * 1000
    cost_by_tech['ngct'] = (ngct_capacity_costs + ngct_operation_costs) / 8760 * 1000 + emissions_by_tech['ngct'] * e_tax / 8760 * 1000             

    cost_by_tech['LIBshort'] = (LIBshort_capacity_costs) / 8760 * 1000
    cost_by_tech['LIB'] = (LIB_capacity_costs) / 8760 * 1000
    cost_by_tech['LIBlong'] = (LIBlong_capacity_costs) / 8760 * 1000
    cost_by_tech['PHS'] = (PHS_capacity_costs) / 8760 * 1000
    cost_by_tech['delivery'] = delivery_cost
    cost_by_tech.transpose().to_frame().to_csv(os.path.join(case_location, r'cost_breakdown_by_tech.csv'))
    
    #tracking CFs
    generation_df = pd.DataFrame(0, index = ['annual'], columns = ['solar', 'wind', 'offw', 'RoR', 'conventional', 'nuclear', 'fusion', 'geo', 'ngccs', 'ngcc', 'ngct'])
    generation_df.loc['annual', 'solar'] = GC_solar * CF_curves.loc[:, 'solar'].mean()
    generation_df.loc['annual', 'wind'] = GC_wind * CF_curves.loc[:, 'wind'].mean()
    generation_df.loc['annual', 'offw'] = GC_offw * CF_curves.loc[:, 'offw'].mean()
    generation_df.loc['annual', 'RoR'] = GC_RoR * CF_curves.loc[:, 'RoR'].mean()
    generation_df.loc['annual', 'conventional'] = GC_conventional * conventional_CF_curves.loc[:, 'conventional'].mean()
    generation_df.loc['annual', 'nuclear'] = dispatchable_output['nuclear'].mean()
    generation_df.loc['annual', 'fusion'] = dispatchable_output['fusion'].mean()
    generation_df.loc['annual', 'geo'] = dispatchable_output['geo'].mean()
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

def single_case(region, emissions_cap_float, fusion_OCC):
    
    emissions_cap = str(emissions_cap_float)

    # settings
    baseload = 'no'
    forced_fusion = 'no'
    no_limits = 'no'
    no_fusion = 'no'
    exact_fusion = 'no'
    consider_current_infrustructure = 'yes'
    nuclear_buildout = 'no'

    region = region
    optimize_shares = 'yes'
    year = '2013'  # year
    area_width = '360'  # '240',#
    sites = '169'  # '81',#
    cap = 'yes'
    e_cap = emissions_cap
    e_tax = 0

    if baseload == 'yes':
        case_name = region + '_' + emissions_cap + '_gCO2_' + str(fusion_OCC) + '_fusion_CAPEX_baseload_fusion'
    elif forced_fusion == 'yes':
        case_name = region + '_' + emissions_cap + '_gCO2_' + str(fusion_OCC) + '_fusion_CAPEX_forced_fusion'
    elif no_limits == 'yes':
        case_name = region + '_' + emissions_cap + '_gCO2_' + str(fusion_OCC) + '_fusion_CAPEX_no_limits'
    elif no_fusion == 'yes':
        case_name = region + '_' + emissions_cap + '_gCO2_' + str(fusion_OCC) + '_fusion_CAPEX_no_fusion'
    elif exact_fusion == 'yes':
        case_name = region + '_' + emissions_cap + '_gCO2_' + str(fusion_OCC) + '_fusion_CAPEX_exact_fusion'
    elif consider_current_infrustructure == 'no':
        case_name = region + '_' + emissions_cap + '_gCO2_' + str(fusion_OCC) + '_fusion_CAPEX_greenfield'
    elif nuclear_buildout == 'yes':
        case_name = region + '_' + emissions_cap + '_gCO2_' + str(fusion_OCC) + '_fusion_CAPEX_w_nuclear_buildout'
    else:
        case_name = region + '_' + emissions_cap + '_gCO2_' + str(fusion_OCC) + '_fusion_CAPEX_150%_FOM'

    case_location = os.path.join(PATH, region, case_name)


    if os.path.isfile(os.path.join(case_location, 'tech_sizes.csv')) == True:
        print('skip_' + region + '_at_' + emissions_cap)
    else:
        if os.path.isdir(case_location):
            print('folder exists')
        else:
            os.makedirs(case_location)
        print('run_' + region + '_at_' + emissions_cap)
        run(region, optimize_shares, year, area_width, sites, cap, e_cap, e_tax, case_location, baseload, forced_fusion, no_limits, no_fusion, exact_fusion, fusion_OCC, consider_current_infrustructure, nuclear_buildout)

    return

