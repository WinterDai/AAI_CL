lappend LIBSET_NAMES bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES bypass_tt_0p75v_85c_typical_setup
##>>>LIB FILES<<<###
##0:LEFS FILES:
set LEFS(STD)                                                              "/process/tsmcN7/data/stdcell/tsmc/n7/TSMC/PRTF_Innovus_7nm_001_Cad_V1.4s1a/PRTF/PRTF_Innovus_7nm_001_Cad_V14_1a/PR_tech/Cadence/LefHeader/Standard/VHV/PRTF_Innovus_N7_15M_1X1Xa1Ya5Y2Yy2Yx2R_UTRDL_M1P64_M2P40_M3P44_M4P76_M5P76_M6P76_M7P76_M8P76_M9P76_H300.14_1a.tlef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_base_svt_130b/lef/tcbn07_bwph300l8p64pd_base_svt_par.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_base_svt_130b/lef/tcbn07_bwph300l8p64pd_base_svt.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_base_lvt_130b/lef/tcbn07_bwph300l8p64pd_base_lvt_par.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_base_lvt_130b/lef/tcbn07_bwph300l8p64pd_base_lvt.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_base_ulvt_130b/lef/tcbn07_bwph300l8p64pd_base_ulvt_par.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_base_ulvt_130b/lef/tcbn07_bwph300l8p64pd_base_ulvt.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_ulvt_130b/lef/tcbn07_bwph300l8p64pd_pm_ulvt_par.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_ulvt_130b/lef/tcbn07_bwph300l8p64pd_pm_ulvt.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_lvt_130b/lef/tcbn07_bwph300l8p64pd_pm_lvt_par.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_lvt_130b/lef/tcbn07_bwph300l8p64pd_pm_lvt.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt_par.lef /process/tsmcN7/data/stdcell/tsmc/n7/TSMC/tcbn07_bwph300l8p64pd_pm_svt_130b/lef/tcbn07_bwph300l8p64pd_pm_svt.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w1s.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w2s_em.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w2s.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s_em.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w3s.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_10w10s.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_1w2s_M4.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ndr/ndr_2w2s_M4.lef /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/TechLEF/site.lef"
set LEFS(MACRO,cdns_ddrio)                                                 "/projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/ddrio/ddr520_h_p76.lef"
###MISC VARS###
set MISC(DESIGN_PROCESS)                                                   tsmc7
set MISC(CON_MODE)                                                         ddr
set MISC(GDSUNITS)                                                         2000
set MISC(GDSMAP)                                                           /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/map/PRTF_Innovus_N7_gdsout_15M_1X_h_1Xa_v_1Ya_h_5Y_vhvhv_2Yy2Yx2R.14_1a.map
set MISC(QRC_LAYERMAP)                                                     /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/QRC/N06_15M1X1Xa1Ya5Y2Yy2Yx2R_UT.lefTechFileMap
set MISC(OUTPUT_FORMAT)                                                    GDS
set MISC(RCTYPE)                                                           coupledRc
set MISC(VT_TYPE)                                                          {PDSVT PDLVT PDULVT}

###TOOL VARS###
set INNOVUS(MODULE_CMD)                                                    "module unload innovus quantus pegasus pvs genus; module load innovus/231/23.33-s082_1 quantus/231/23.10.000 pegasus/232/23.25.000 genus/201/20.10.000"
set INNOVUS(QUEUE)                                                         "pd -R \"select\[OSREL==EE70\]\""
set INNOVUS(EXEC_CMD)                                                      "innovus -64"
set INNOVUS(UI)                                                            legacy
set INNOVUS(DONT_USE)                                                      /projects/yunbao_N6_80bits_EW_PHY_OD_6400/workbench/process/tsmc7/innovus_options_paste/dont_use.tsmcN7.paste
set INNOVUS(POWER_OPT_VIEW)                                                func_func_ffgnp_0p935v_125c_cbest_CCbest_T_rcworst_CCworst_hold

set QRC(MODULE_CMD)                                                        "module unload quantus ext; module load quantus/231/23.10.000"
set QRC(EXEC_CMD)                                                          "qrc -64"
set QRC(QUEUE)                                                             pd
set QRC(CPU)                                                               4
set QRC(TECHLIBFILE)                                                       /projects/yunbao_N6_80bits_EW_PHY_OD_6400/libs/QRC/N06_15M1X1Xa1Ya5Y2Yy2Yx2R_UT.technology_library_file

set FV(MODULE_CMD)                                                         "module unload confrml; module load confrml/221/22.10.200"
set CLP(MODULE_CMD)                                                        "module unload confrml; module load confrml/221/22.10.200"
set TEMPUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/202/20.20.000"
set VOLTUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/202/20.20.000"
set QRC(MODULE_CMD)                                                        "module unload quantus ext; module load quantus/231/23.10.000"

set PVS(MODULE_CMD)                                                        "module unload pegasus pvs; module load pegasus/232/23.25.000"
set PEGASUS(MODULE_CMD)                                                    "module unload pegasus pvs; module load pegasus/232/23.25.000"
set MVS(MODULE_CMD)                                                        "module unload mvs pvs pegasus;module load mvs/191/19.11.000 pvs/191/19.12.000"
