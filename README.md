# IG-LCA_analysis
### Description

This project contains all code and data needed to run Ideal Grid for LCA analysis as seen in *The elephant in the room: embodied emissions in our power sector* in *Nature Communications*.  This linear optimization minimizes power sector total cost given system constraints.  For more detail on this model, please reference *Highlighting regional decarbonization challenges with novel capacity expansion model* in *Cleaner Energy Systems*.

### Input Data

Note that the below table describes csv file names and contents for all source data.  

| Name | Description | Units |
|------|-------------|-------|
| LoadUpdate_2033 | 2033 hourly normalized load for all regions | kWh / average kWh |
| *region*\_hourly_RoR_hydro_cf_curve\_*year* | RoR hourly CF for the specified *year* and *region* | % |
| *region*\_offshore_wind | Seven years of hourly offshore wind CF data for the specified *region* | % |
| G_data | Seven years of hourly wind and solar CFs for each region | % |
| monthly_hydro_CFs_*year* | Monthly conventional hydro CFs for each region for specfified *year* | % |

Please reference Farnsworth and Gencer's *Embodied emissions in the US power sector* in *Nature Communications* for more details on source and methodology of this data.

### Building Cases

Case settings can be specified in *LCA_case_settings* and optimization can be adjusted in *LCA_version*.  Note that this code is structured to be run on MIT's SuperCloud and Lincoln Laboratory Supercomputing Center. Adjustements will be necessary to run this code using other cloud computing services.
