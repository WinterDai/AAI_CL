set_library_unit -time  1ns -cap  1pf

set_design_mode -process 5

set_multi_cpu_usage -localCpu 16
set_message -id {VOLTUS_SCHD-0075} -severity error ;#The via definition must be defined before it is referenced 
set_message -id {IMPVAC-116} -severity error ; # Signal EM checking continue even No EM rule found in QRC tech or ICT EM file.

setExtractRCMode -lefTechFileMap /projects/TC70_LPDDR6_N5P/libs/QRC/N5_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT.lefTechFileMap


##### read lef
set LEF {}
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/PRTF_Innovus_5nm_014_Cad_V13a/PRTF/PRTF_Innovus_5nm_014_Cad_V13a/PR_tech/Cadence/LefHeader/Standard/VHV/PRTF_Innovus_N5_15M_1X1Xb1Xe1Ya1Yb5Y2Yy2Z_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_H210_SHDMIM.13a.tlef
  lappend LEF /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_10w10s.lef
  lappend LEF /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_1w2s.lef
  lappend LEF /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w1s.lef
  lappend LEF /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w2s_em.lef
  lappend LEF /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w2s.lef
  lappend LEF /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w3s_em.lef
  lappend LEF /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w3s.lef
  lappend LEF /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_8w5s.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lef/tcbn05_bwph210l6p51cnod_base_svt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lef/tcbn05_bwph210l6p51cnod_base_svt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lef/tcbn05_bwph210l6p51cnod_base_lvt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lef/tcbn05_bwph210l6p51cnod_base_lvt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_lvtll_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_lvtll.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvtll_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvtll.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lef/tcbn05_bwph210l6p51cnod_base_elvt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lef/tcbn05_bwph210l6p51cnod_base_elvt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lef/tcbn05_bwph210l6p51cnod_pm_svt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lef/tcbn05_bwph210l6p51cnod_pm_svt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_lvt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_lvt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lef/tcbn05_bwph210l6p51cnod_pm_lvtll_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lef/tcbn05_bwph210l6p51cnod_pm_lvtll.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_ulvt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_ulvt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lef/tcbn05_bwph210l6p51cnod_pm_ulvtll_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lef/tcbn05_bwph210l6p51cnod_pm_ulvtll.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_elvt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_elvt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_svt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_svt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_lvt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_lvt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lef/tcbn05_bwph210l6p51cnod_lvl_lvtll_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lef/tcbn05_bwph210l6p51cnod_lvl_lvtll.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_ulvt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_ulvt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lef/tcbn05_bwph210l6p51cnod_lvl_ulvtll_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lef/tcbn05_bwph210l6p51cnod_lvl_ulvtll.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_elvt_par.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_elvt.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lef/cdns_ddr1100_h.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lef/PLLTS5FFPLAFRACN.lef
  lappend LEF /proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lef/PLLTS5FFPLJFRACR2.lef
  lappend LEF /projects/TC70_LPDDR6_N5P/libs/customcell/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base.antenna.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lef/cdns_ddr_custom_decap_unit_cells.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/LEF/ts1n05mblvta16384x39m16qwbzhodcp.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lef/mt/15m/15M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_5Y_VHVHV_2YY2Z/lef/tphn05_12gpio_15lm.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12lup_120a/lef/mt/15m/15M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_5Y_VHVHV_2YY2Z/lef/tpmn05_12lup_15lm.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12esd_120b/lef/mt/15m/15M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_5Y_VHVHV_2YY2Z/lef/tpmn05_12esd_15lm.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lef/cdns_ddr_noisegen_v.antenna.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lef/cdns_lpddr6_testio.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5v/TSMC/tpbn05v_cu_round_bump_100a/lef/fc/fc_bot/APRDL/lef/tpbn05v_cu_round_bump.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/TSMC/N5_DTCD_library_kit_v1d3.1/lef/N5_DTCD_M11/N5_DTCD_v1d2.lef
  lappend LEF /process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_custom_mimcap_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_130P_UBM80_DR_r100.20251208/lef/cdns_ddr1100_custom_mimcap_h.lef

read_lib -lef  $LEF

##### view definition
read_view_definition /projects/TC70_LPDDR6_N5P/work/tv_chip/zhaozhao/signoff/signoff-1211b/scr/tv_chip_ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static_viewdefinition.tcl

##### import design
set verilog_list ""
 lappend verilog_list dbs/tv_chip.innovusOUTwD0.enc.dat/tv_chip.v.gz
 lappend verilog_list /projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/Y2025-M12-D03-H16/netlist/cdns_lp6_x48_ew_phy_top.v.gz
 lappend verilog_list /projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/Y2025-M12-D02-H11/netlist/cdns_lp6_x48_ew_phy_as_top.v.gz
 lappend verilog_list /projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/Y2025-M12-D02-H09/netlist/cdns_lp6_x48_ew_phy_ds_top.v.gz
 lappend verilog_list /projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/Y2025-M12-D04-H21/netlist/cadence_mc_ew_controller.v.gz
 lappend verilog_list /projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/Y2025-M11-D18-H20/netlist/databahn_data_pat_gen.v.gz
read_verilog $verilog_list

set_top_module tv_chip

set def_list ""
 lappend def_list dbs/tv_chip.innovusOUTwD0.def.gz
 lappend def_list /projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/Y2025-M12-D03-H16/def/cdns_lp6_x48_ew_phy_top.def.gz
 lappend def_list /projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/Y2025-M12-D02-H11/def/cdns_lp6_x48_ew_phy_as_top.def.gz
 lappend def_list /projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/Y2025-M12-D02-H09/def/cdns_lp6_x48_ew_phy_ds_top.def.gz
 lappend def_list /projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/Y2025-M12-D04-H21/def/cadence_mc_ew_controller.def.gz
 lappend def_list /projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/Y2025-M11-D18-H20/def/databahn_data_pat_gen.def.gz
read_def -preserve_shape $def_list 
#RDL DEFs will read by command set_rail_analysis_mode near the end of this file



setDelayCalMode -engine aae -SIAware true
setAnalysisMode -cppr both -analysisType onChipVariation -clockPropagation sdcControl 
##### MMMC : specify which spef(s) to read into which rc corner

spefIn  -rc_corner cworst_CCworst_125c \
       [list \
		/projects/TC70_LPDDR6_N5P/work/tv_chip/zhaozhao/signoff/signoff-1211b/spef/tv_chip_cworst_CCworst_125c.spef.gz \
		/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/Y2025-M12-D03-H16/spef/cdns_lp6_x48_ew_phy_top_cworst_CCworst_125c.spef.gz \
		/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/Y2025-M12-D02-H11/spef/cdns_lp6_x48_ew_phy_as_top_cworst_CCworst_125c.spef.gz \
		/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/Y2025-M12-D02-H09/spef/cdns_lp6_x48_ew_phy_ds_top_cworst_CCworst_125c.spef.gz \
		/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/Y2025-M12-D04-H21/spef/cadence_mc_ew_controller_cworst_CCworst_125c.spef.gz \
		/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/Y2025-M11-D18-H20/spef/databahn_data_pat_gen_cworst_CCworst_125c.spef.gz \
       ]
report_annotated_parasitics -list_not_annotated -list_real_net -list_broken_net


set PGLIB {}
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/tech_ffgnp_0p825v_125c_cbest_CCbest_T/techonly.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/sc-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/sc-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/sc-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/sc-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/sc-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/sc-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/pm-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/pm-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/pm-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/pm-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/pm-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/pm-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/noisegen_ffgnp_0p825v_125c_cbest_CCbest_T/macros_cdns_ddr_noisegen_v.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/lvl-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/lvl-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/lvl-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/lvl-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/lvl-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/lvl-ffgnp_0p825v_125c_cbest_CCbest_T/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/dcc_ffgnp_0p825v_125c_cbest_CCbest_T/macros_cdns_ddr_cinv_32X_tcbn05_bwph210l6p51cnod_base_ulvt.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/dcc_ffgnp_0p825v_125c_cbest_CCbest_T/macros_cdns_ddr_cinv_64X_tcbn05_bwph210l6p51cnod_base_ulvt.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/esd_ffgnp_0p825v_125c_cbest_CCbest_T/macros_ESD_PCLAMP_CORE_N1_H_M8.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/esd_ffgnp_0p825v_125c_cbest_CCbest_T/macros_ESD_PCLAMP_CORE_N1_V_M8.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/esd_ffgnp_0p825v_125c_cbest_CCbest_T/macros_ESD_PCLAMP_IO_P1_H_M8.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/esd_ffgnp_0p825v_125c_cbest_CCbest_T/macros_ESD_PCLAMP_IO_P1_V_M8.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/esd_ffgnp_0p825v_125c_cbest_CCbest_T/macros_LUP_GR_CELL1_FB1_G_H.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/esd_ffgnp_0p825v_125c_cbest_CCbest_T/macros_LUP_GR_CELL1_FB1_G_V.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/esd_ffgnp_0p825v_125c_cbest_CCbest_T/macros_LUP_GR_CELL_FB1_G_H.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/esd_ffgnp_0p825v_125c_cbest_CCbest_T/macros_LUP_GR_CELL_FB1_G_V.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/gpio_ffgnp_0p825v_125c_cbest_CCbest_T/macros_PDCAP05600D_H.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/gpio_ffgnp_0p825v_125c_cbest_CCbest_T/macros_PDDWUW08SCDG_H.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/gpio_ffgnp_0p825v_125c_cbest_CCbest_T/macros_PVDD1CDGM_H.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/gpio_ffgnp_0p825v_125c_cbest_CCbest_T/macros_PVDD2CDGM_H.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/gpio_ffgnp_0p825v_125c_cbest_CCbest_T/macros_PVDD2POCM_H.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/gpio_ffgnp_0p825v_125c_cbest_CCbest_T/macros_PCORNER_V.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/gpio_ffgnp_0p825v_125c_cbest_CCbest_T/macros_PENDCAP_H.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/sram_ffgnp_0p825v_125c_cbest_CCbest_T/macros_TS1N05MBLVTA16384X39M16QWBZHODCP.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/pll_ffgnp_0p825v_125c_cbest_CCbest_T/macros_PLLTS5FFPLAFRACN.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/pll_ffgnp_0p825v_125c_cbest_CCbest_T/macros_PLLTS5FFPLJFRACR2.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/decap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr_custom_decap_core_1x1.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/decap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr_custom_decap_core_2x2.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/decap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr_custom_decap_core_4x4.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/decap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr_custom_decap_core_gated_1x1.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/decap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr_custom_decap_core_gated_2x2.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/decap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr_custom_decap_core_gated_4x4.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/decap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr_custom_decap_io_1x1.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/decap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr_custom_decap_io_2x2.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/decap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr_custom_decap_io_4x4.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/testio_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_lpddr6_testio.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/ddr1100_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr1100_custom_caslice_h.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/ddr1100_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr1100_custom_cmnslice_h.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/ddr1100_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr1100_custom_dataslice_h.cl 
  lappend PGLIB /projects/TC70_LPDDR6_N5P/libs/pgv/AMS/mimcap_ffgnp_0p825v_125c_cbest_CCbest_T/cdns_ddr1100_custom_mimcap_h.cl 

### corner mapping #####
global corner
set current_view [lindex [all_setup_analysis_views] 0]
switch -regexp -- $current_view {
    .*_ss.*[vV]*_?125c.*  {set corner WC} 
    .*_ss.*[vV]*_?m40c.*  {set corner WCL} 
    .*_ss.*[vV]*_?0c.*    {set corner WCZ} 
    .*_ss.*[vV]*_?135c.*  {set corner TI135} 
    .*_ff.*[vV]*_?125c.*  {set corner ML} 
    .*_ff.*[vV]*_?m40c.*  {set corner LT} 
    .*_ff.*[vV]*_?0c.*    {set corner BC} 
    .*_ff.*[vV]*_?135c.*  {set corner TI135} 
    .*_tt.*[vV]*_?85c.*   {set corner TC85} 
    .*_tt.*[vV]*_?25c.*   {set corner TC} 
    .*_tt.*[vV]*_?105c.*  {set corner TC105} 
    .*_nn.*[vV]*_?85c.*   {set corner TC85} 
    .*_nn.*[vV]*_?25c.*   {set corner TC} 
    .*_nn.*[vV]*_?105c.*  {set corner TC105} 
}

##### read constraint 

set ND1_sdc_files ""
lappend ND1_sdc_files /projects/TC70_LPDDR6_N5P/input/latest/sta_signoff_ND1_0p75v/constraints/tv_chip/user_setup_top.ets 
lappend ND1_sdc_files /projects/TC70_LPDDR6_N5P/input/latest/sta_signoff_ND1_0p75v/constraints/tv_chip/user_setup_tv_chip.ets 
lappend ND1_sdc_files /projects/TC70_LPDDR6_N5P/input/latest/sta_signoff_ND1_0p75v/constraints/tv_chip/tv_chip.con.ets 
update_constraint_mode -name ND1 -sdc_files $ND1_sdc_files 


##### standard wbPowerCal
set_default_switching_activity -input_activity 0.15 -period 0.625


set_power_include_file /projects/TC70_LPDDR6_N5P/wb_local/workbench/kits/signoff/pwr_includefile.inc

source /projects/TC70_LPDDR6_N5P/wb_local/workbench/tools/voltus/userEnableFullDelayLineInVoltus.tcl
userEnableFullDelayLineInVoltus

source /projects/TC70_LPDDR6_N5P/wb_local/workbench/tools/voltus/userAnnotateRegulatorCurrentPLL.tcl

#set_power for IO with only DEFAULT MODE
source /projects/TC70_LPDDR6_N5P/wb_local/workbench/tools/voltus/userSetPowerForDefaultModeOnlyIO.tcl
userSetPowerForDefaultModeOnlyIO ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static static

set_power_analysis_mode -reset
set_power_analysis_mode -create_binary_db false \
                        -method static \
                        -write_static_currents true \
                        -disable_static false \
                        -static_netlist def \
                        -power_grid_library $PGLIB 

set_power_output_dir dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static
report_power -rail_analysis_format VS -outfile dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/static_power.rpt
report_power                          -outfile dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/static_power.rail.rpt
report_power -hierarchy 5             -outfile dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/static_power.hier.rpt
report_power -no_wrap -net -hierarchy 100 -outfile dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/static_power.instance.net.rpt

##### standard wbRailAnalysis
exec mkdir -p tmp

foreach i [glob -nocomplain  ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/static_*ptiavg] {
  if {![string match *general* $i] && ![string match *default* $i] && ![string match *VREF* $i]} {
     set_power_data -format current -scale 1 $i
  }
}

set_pg_nets -net VDD -voltage 0.825 -threshold 0.8085
set_pg_nets -net VDD2 -voltage 0.825 -threshold 0.8085
set_pg_nets -net VDDPST -voltage 1.32 -threshold 1.2936
set_pg_nets -net VDDQ -voltage 0.57 -threshold 0.5586
set_pg_nets -net VDDQXC -voltage 1.12 -threshold 1.0976000000000001
set_pg_nets -net VDDQ2 -voltage 0.57 -threshold 0.5586
set_pg_nets -net VDDQX2 -voltage 1.12 -threshold 1.0976000000000001
set_pg_nets -net VDDHVPLL_FRAC0 -voltage 1.2 -threshold 1.176
set_pg_nets -net VDDPOSTPLL_FRAC0 -voltage 0.825 -threshold 0.8085
set_pg_nets -net VDDREFPLL_FRAC0 -voltage 0.825 -threshold 0.8085
set_pg_nets -net VDDHVPLL_FRAC1 -voltage 1.2 -threshold 1.176
set_pg_nets -net VDDPOSTPLL_FRAC1 -voltage 0.825 -threshold 0.8085
set_pg_nets -net VDDREFPLL_FRAC1 -voltage 0.825 -threshold 0.8085
set_pg_nets -net VDDHVPLL_FRAC2 -voltage 1.2 -threshold 1.176
set_pg_nets -net VDDPOSTPLL_FRAC2 -voltage 0.825 -threshold 0.8085
set_pg_nets -net VDDREFPLL_FRAC2 -voltage 0.825 -threshold 0.8085
set_pg_nets -net VDDM_SRAM -voltage 0.825 -threshold 0.8085
set_pg_nets -net VSS -voltage 0     -threshold 0.015

set_rail_analysis_domain -name PD -pwrnets { VDD VDD2 VDDPST VDDQ VDDQXC VDDQ2 VDDQX2 VDDHVPLL_FRAC0 VDDPOSTPLL_FRAC0 VDDREFPLL_FRAC0 VDDHVPLL_FRAC1 VDDPOSTPLL_FRAC1 VDDREFPLL_FRAC1 VDDHVPLL_FRAC2 VDDPOSTPLL_FRAC2 VDDREFPLL_FRAC2 VDDM_SRAM } -gndnets {VSS}

set_rail_analysis_mode \
  -rdl_def_list {{/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/pgv/def/cdns_ddr1100_h.def 0 207.48 N} {/projects/TC70_LPDDR6_N5P/libs/ddrio/cdns_ddr1100_custom_dataslice_h.def 2159.85 2343.992 S}} \
  -method static \
  -ignore_shorts true \
  -temp_directory_name ./tmp \
  -temperature 125 \
  -em_temperature 105 \
  -ict_em_models /process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/ICT_EM_v1d2p1a/cln5_1p15m+ut-alrdl_1x1xb1xe1ya1yb5y2yy2z_shdmim.ictem \
  -extraction_tech_file /process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/rcworst/Tech/rcworst_CCworst_T/qrcTechFile \
  -enable_2d_partition_extraction true \
  -process_techgen_em_rules true \
  -accuracy hd \
  -vsrc_search_distance 50 \
  -enable_rlrp_analysis true \
  -report_via_current_direction false \
  -power_grid_library $PGLIB 

set_power_pads -net VDD -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDD.vsrc
set_power_pads -net VDD2 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDD2.vsrc
set_power_pads -net VDDPST -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDPST.vsrc
set_power_pads -net VDDQ -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDQ.vsrc
set_power_pads -net VDDQXC -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDQXC.vsrc
set_power_pads -net VDDQ2 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDQ2.vsrc
set_power_pads -net VDDQX2 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDQX2.vsrc
set_power_pads -net VDDHVPLL_FRAC0 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDHVPLL_FRAC0.vsrc
set_power_pads -net VDDPOSTPLL_FRAC0 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDPOSTPLL_FRAC0.vsrc
set_power_pads -net VDDREFPLL_FRAC0 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDREFPLL_FRAC0.vsrc
set_power_pads -net VDDHVPLL_FRAC1 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDHVPLL_FRAC1.vsrc
set_power_pads -net VDDPOSTPLL_FRAC1 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDPOSTPLL_FRAC1.vsrc
set_power_pads -net VDDREFPLL_FRAC1 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDREFPLL_FRAC1.vsrc
set_power_pads -net VDDHVPLL_FRAC2 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDHVPLL_FRAC2.vsrc
set_power_pads -net VDDPOSTPLL_FRAC2 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDPOSTPLL_FRAC2.vsrc
set_power_pads -net VDDREFPLL_FRAC2 -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDREFPLL_FRAC2.vsrc
set_power_pads -net VDDM_SRAM -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VDDM_SRAM.vsrc
set_power_pads -net VSS -format xy -file /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/tvchipvsrc/VSS.vsrc

analyze_rail -type domain -results_directory ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static PD

##report the resistance from VDD/VSS source
set cell [lsort -u [dbGet [dbGet top.insts.pgInstTerms.net.name *VDDR -p3].cell.name cdns_ddr_reg*]]
if {$cell != "0x0"} {
    analyze_resistance -cell $cell -net VDD -output_dir ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static -output reg_VDD_VDDR.resistance.rpt
    analyze_resistance -cell $cell -net VSS -output_dir ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static -output reg_VSS_VDDR.resistance.rpt
    ##remove big files to save space
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/*
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/REFF
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/*DB
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/Reports/REFFDB
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/Reports/*/*.rlrp_inst
}

set cell [lsort -u [dbGet [dbGet top.insts.pgInstTerms.net.name *VDDR6 -p3].cell.name cdns_ddr_reg*]]
if {$cell != "0x0"} {
    analyze_resistance -cell $cell -net VDD -output_dir ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static -output reg_VDD_VDDR6.resistance.rpt
    analyze_resistance -cell $cell -net VSS -output_dir ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static -output reg_VSS_VDDR6.resistance.rpt
    ##remove big files to save space
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/*
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/REFF
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/*DB
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/Reports/REFFDB
    rm -rf ./dbs/ND1_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold_static/*_reff_*/Reports/*/*.rlrp_inst
}

exit
