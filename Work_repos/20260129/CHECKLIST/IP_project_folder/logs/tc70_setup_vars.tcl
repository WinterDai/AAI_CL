###TOOL VARS###
set INNOVUS(MODULE_CMD)                                                    "module unload innovus genus ext quantus pegasus pvs;module load innovus/221/22.16-s080_1 genus/221/22.11-e068_1 quantus/211/21.11.012-s732 pegasus/232/23.25.008-e831"
set INNOVUS(QUEUE)                                                         "pd -R \"select\[(OSREL==EE70)||(OSREL==EE80)\]\""
set INNOVUS(EXEC_CMD)                                                      "innovus -64"
set INNOVUS(UI)                                                            legacy
set INNOVUS(DONT_USE)                                                      /projects/workbench/versions/current/workbench/process/tsmc5/innovus_options_paste/dont_use.tsmcN5.paste
set INNOVUS(INCR_SETUP)                                                    /projects/TC70_LPDDR6_N5P/common_scripts/FLOW/INNOVUS_tsmc5_setup.local.paste
set INNOVUS(POWER_OPT_VIEW)                                                func_func_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
set INNOVUS(POWER_EFFORT)                                                  high
set INNOVUS(OCV_PORT_FROM_STA)                                             /projects/TC70_LPDDR6_N5P/setup/yaml/MMMC_OCV_setting_extract_from_STA.innovus.tcl

set QRC(MODULE_CMD)                                                        "module unload quantus ext; module load quantus/211/21.11.012-s732"
set QRC(EXEC_CMD)                                                          "qrc -64"
set QRC(QUEUE)                                                             pd
set QRC(CPU)                                                               4
set QRC(TECHLIBFILE)                                                       /projects/TC70_LPDDR6_N5P/libs/QRC/N5_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT.technology_library_file
set QRC(MAXFILESIZE)                                                       20000000000
set QRC(MFILLTYPE)                                                         floating
set QRC(RCFORMAT)                                                          extended
set QRC(LAYERMAP)                                                          "{PO none} {PW none} {NW none} {OD none} {M0 M0} {M1 M1} {M2 M2} {M3 M3} {M4 M4} {M5 M5} {M6 M6} {M7 M7} {M8 M8} {M9 M9} {M10 M10} {M11 M11} {M12 M12} {M13 M13} {M14 M14} {M15 M15} {AP AP} {BPC BPC} {MPC MPC} {TPC TPC} {VIA0 VIA0} {VIA1 VIA1} {VIA2 VIA2} {VIA3 VIA3} {VIA4 VIA4} {VIA5 VIA5} {VIA6 VIA6} {VIA7 VIA7} {VIA8 VIA8} {VIA9 VIA9} {VIA10 VIA10} {VIA11 VIA11} {VIA12 VIA12} {VIA13 VIA13} {VIA14 VIA14} {RV RV}"
set QRC(GDS_LAYER_MAP)                                                     "{{PO 17}} {{OD 6}} {{M0 330}} {{M1 331}} {{M2 332}} {{M3 333}} {{M4 334}} {{M5 335}} {{M6 336}} {{M7 337}} {{M8 338}} {{M9 339}} {{M10 340}} {{M11 341}} {{M12 342}} {{M13 343}} {{M14 344}} {{M15 345}} {{AP 74}} {{BPC 262}} {{MPC 261}} {{TPC 260}} {{VIA0 350}} {{VIA1 351}} {{VIA2 352}} {{VIA3 353}} {{VIA4 354}} {{VIA5 355}} {{VIA6 356}} {{VIA7 357}} {{VIA8 358}} {{VIA9 359}} {{VIA10 360}}  {{VIA11 361}} {{VIA12 362}} {{VIA13 363}} {{VIA14 364}} {{RV 85}}"

set PVS(MODULE_CMD)                                                        "module unload pegasus pvs; module load pegasus/232/23.25.008-e831"
set PVS(EXEC_CMD)                                                          pegasus
set PVS(QUEUE)                                                             pd
set PVS(CPU)                                                               8

set PEGASUS(MODULE_CMD)                                                    "module unload pegasus pvs; module load pegasus/232/23.25.008-e831"
set PEGASUS(EXEC_CMD)                                                      pegasus
set PEGASUS(QUEUE)                                                         pd
set PEGASUS(CPU)                                                           8

set TEMPUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/221/22.16-s083_1"
set TEMPUS(EXEC_CMD)                                                       "tempus -64"
set TEMPUS(CPU)                                                            4
set TEMPUS(QUEUE)                                                          pd
set TEMPUS(CON_MODE)                                                       ddr
set TEMPUS(REPORT_NET_DELAYS)                                              yes
set TEMPUS(TOOLS_DIR)                                                      /projects/TC70_LPDDR6_N5P/input/latest/sta_signoff/tool

set VOLTUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/231/23.12-s092_1"
set VOLTUS(EXEC_CMD)                                                       "voltus -64"
set VOLTUS(CPU)                                                            16
set VOLTUS(EM_LIFE_YEAR)                                                   10
set VOLTUS(PERIOD)                                                         0.625
set VOLTUS(TEMPERATURE)                                                    125
set VOLTUS(EM_TEMPERATURE)                                                 105
set VOLTUS(QUEUE)                                                          pd
set VOLTUS(CON_MODE)                                                       ddr
set VOLTUS(SPICEMODEL)                                                     /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5/ir_em.scs
set VOLTUS(MODELS_DIR)                                                     /process/tsmcN5/data/g/PDK/tsmc5g.a.13/models/spectre_v1d2_2p5
set VOLTUS(TSMCPDK_OS_INSTALL_PATH)                                        /process/tsmcN5/data/g/PDK/tsmc5g_plus.a.10/eDesigner
set VOLTUS(ICTEM)                                                          /process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/ICT_EM_v1d2p1a/cln5_1p15m+ut-alrdl_1x1xb1xe1ya1yb5y2yy2z_shdmim.ictem
set VOLTUS(LEFDEF_LAYERMAP)                                                /projects/TC70_LPDDR6_N5P/libs/map/N5_15M_voltus_lefdef.layermap
set VOLTUS(GDS_LAYERMAP)                                                   /projects/TC70_LPDDR6_N5P/libs/map/N5_15M_voltus_gds.layermap
set VOLTUS(PG_LIBS_DIR)                                                    /projects/TC70_LPDDR6_N5P/libs/pgv
set VOLTUS(PG_LIBS_MODES)                                                  "ssgnp_0p765v_125c_cworst_CCworst_T tt_0p85v_85c_typical ffgnp_0p935v_125c_cbest_CCbest_T ssgnp_0p675v_125c_cworst_CCworst_T ffgnp_0p825v_125c_cbest_CCbest_T tt_0p75v_85c_typical ffgnp_0p77v_125c_cbest_CCbest_T tt_0p7v_85c_typical ssgnp_0p63v_125c_cworst_CCworst_T"

set FV(MODULE_CMD)                                                         "module unload confrml; module load confrml/241/24.10.100"
set FV(EXEC_CMD)                                                           "lec -64 -xl"
set FV(CPU)                                                                4
set FV(QUEUE)                                                              pd

set CLP(MODULE_CMD)                                                        "module unload confrml; module load confrml/241/24.10.100"
set CLP(EXEC_CMD)                                                          "lec -64 -lp -verify -XL"

set DDR(MODULE_CMD)                                                        "module unload ssv; module load ssv/221/22.16-s083_1"
set DDR(EXEC_CMD)                                                          "tempus -64"

set MVS(MODULE_CMD)                                                        "module unload mvs pvs pegasus;module load mvs/191/19.11.000 pvs/191/19.12.000"

set IPTAG(IP_WRITER)                                                       /projects/workbench/versions/IP_tag/IP_WRITER/RHE4_Linux/IP_writer_Cadence.Linux
set IPTAG(IP_CHECKER)                                                      /projects/workbench/versions/IP_tag/IP_CHECKER/RHE4_Linux/IP_checker.Linux

###MISC VARS###
set MISC(DESIGN_PROCESS)                                                   tsmc5
set MISC(CON_MODE)                                                         ddr
set MISC(GDSUNITS)                                                         2000
set MISC(GDSMAP)                                                           /projects/TC70_LPDDR6_N5P/libs/map/PRTF_Innovus_N5_gdsout_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy2Z_SHDMIM.13a.map
set MISC(QRC_LAYERMAP)                                                     /projects/TC70_LPDDR6_N5P/libs/QRC/N5_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT.lefTechFileMap
set MISC(OUTPUT_FORMAT)                                                    GDS
set MISC(RCTYPE)                                                           coupledRc
set MISC(tQuantusModelFile)                                                /projects/TC70_LPDDR6_N5P/libs/QRC/N5_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT.bin
set MISC(VT_TYPE)                                                          {CNODSVT CNODLVT CNODULVT CNODELVT CNODLVTLL CNODULVTLL}

##Design config Vars###
set CONFIG(cdns_lp6_x48_ew_phy_as_top,LEF_TOP_LAYER)                       16
set CONFIG(cdns_lp6_x48_ew_phy_as_top,LEF_PG_LAYERS)                       "15 16"
set CONFIG(cdns_lp6_x48_ew_phy_as_top,MAX_ROUTING_LAYER)                   15
set CONFIG(cdns_lp6_x48_ew_phy_as_top,CTS_NDR_RULE)                        ndr_2w2s
set CONFIG(cdns_lp6_x48_ew_phy_as_top,CTS_TOP_PREFER_TOP_LAYER)            12
set CONFIG(cdns_lp6_x48_ew_phy_as_top,CTS_TOP_PREFER_BOTTOM_LAYER)         7
set CONFIG(cdns_lp6_x48_ew_phy_as_top,CTS_TRUNK_PREFER_TOP_LAYER)          12
set CONFIG(cdns_lp6_x48_ew_phy_as_top,CTS_TRUNK_PREFER_BOTTOM_LAYER)       9
set CONFIG(cdns_lp6_x48_ew_phy_as_top,CTS_LEAF_PREFER_TOP_LAYER)           8
set CONFIG(cdns_lp6_x48_ew_phy_as_top,CTS_LEAF_PREFER_BOTTOM_LAYER)        7
set CONFIG(cdns_lp6_x48_ew_phy_as_top,QUEUE)                               pd
set CONFIG(cdns_lp6_x48_ew_phy_as_top,CPU)                                 16
set CONFIG(cdns_lp6_x48_ew_phy_as_top,MEM)                                 [expr 16  * 1024]
set CONFIG(cdns_lp6_x48_ew_phy_as_top,PWR_NET)                             "VDD VDDG VDDG_HM VDD_PLL VDDQ VDDQXD"
set CONFIG(cdns_lp6_x48_ew_phy_as_top,GND_NET)                             "VSS"
set CONFIG(cdns_lp6_x48_ew_phy_as_top,MACRO)                               "cdns_dcc cdns_ddr1100"
set CONFIG(cdns_lp6_x48_ew_phy_as_top,SUB_BLOCK_LIB_MODE)                  "func scanshift"

set CONFIG(cdns_lp6_x48_ew_phy_ds_top,LEF_TOP_LAYER)                       16
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,LEF_PG_LAYERS)                       "15 16"
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,MAX_ROUTING_LAYER)                   15
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,CTS_NDR_RULE)                        ndr_2w2s
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,CTS_TOP_PREFER_TOP_LAYER)            12
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,CTS_TOP_PREFER_BOTTOM_LAYER)         7
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,CTS_TRUNK_PREFER_TOP_LAYER)          12
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,CTS_TRUNK_PREFER_BOTTOM_LAYER)       9
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,CTS_LEAF_PREFER_TOP_LAYER)           8
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,CTS_LEAF_PREFER_BOTTOM_LAYER)        7
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,QUEUE)                               pd
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,CPU)                                 16
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,MEM)                                 [expr 16  * 1024]
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,PWR_NET)                             "VDD VDDG VDDG_HM VDD_PLL VDD_SENSE VDDQ VDDQ_SENSE VDDQXD"
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,GND_NET)                             "VSS"
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,MACRO)                               "cdns_dcc cdns_ddr1100"
set CONFIG(cdns_lp6_x48_ew_phy_ds_top,SUB_BLOCK_LIB_MODE)                  "func scanshift"

set CONFIG(cdns_lp6_x48_ew_phy_top,LEF_TOP_LAYER)                          17
set CONFIG(cdns_lp6_x48_ew_phy_top,LEF_PG_LAYERS)                          "17"
set CONFIG(cdns_lp6_x48_ew_phy_top,MAX_ROUTING_LAYER)                      15
set CONFIG(cdns_lp6_x48_ew_phy_top,CTS_NDR_RULE)                           ndr_2w2s
set CONFIG(cdns_lp6_x48_ew_phy_top,CTS_TOP_PREFER_TOP_LAYER)               12
set CONFIG(cdns_lp6_x48_ew_phy_top,CTS_TOP_PREFER_BOTTOM_LAYER)            7
set CONFIG(cdns_lp6_x48_ew_phy_top,CTS_TRUNK_PREFER_TOP_LAYER)             12
set CONFIG(cdns_lp6_x48_ew_phy_top,CTS_TRUNK_PREFER_BOTTOM_LAYER)          9
set CONFIG(cdns_lp6_x48_ew_phy_top,CTS_LEAF_PREFER_TOP_LAYER)              8
set CONFIG(cdns_lp6_x48_ew_phy_top,CTS_LEAF_PREFER_BOTTOM_LAYER)           7
set CONFIG(cdns_lp6_x48_ew_phy_top,QUEUE)                                  pd
set CONFIG(cdns_lp6_x48_ew_phy_top,CPU)                                    16
set CONFIG(cdns_lp6_x48_ew_phy_top,PWR_NET)                                "VDD VDDG VDDG_HM VDD_PLL_A0_AS VDD_PLL_A0_DS0 VDD_PLL_A0_DS1 VDD_PLL_A1_AS VDD_PLL_A1_DS0 VDD_PLL_A1_DS1 VDD_SENSE VDDQ VDDQ_SENSE VDDQXC VDDQXD"
set CONFIG(cdns_lp6_x48_ew_phy_top,GND_NET)                                "VSS"
set CONFIG(cdns_lp6_x48_ew_phy_top,PWR_BUMP)                               PAD130PITCH_POWER
set CONFIG(cdns_lp6_x48_ew_phy_top,GND_BUMP)                               PAD130PITCH_GROUND
set CONFIG(cdns_lp6_x48_ew_phy_top,VSRC_LAYER)                             AP
set CONFIG(cdns_lp6_x48_ew_phy_top,MACRO)                                  "cdns_ddr1100 cdns_dcc cdns_custom_decap bump esd tcd mim"
set CONFIG(cdns_lp6_x48_ew_phy_top,SUB_BLOCKS)                             "cdns_lp6_x48_ew_phy_as_top cdns_lp6_x48_ew_phy_ds_top"
set CONFIG(cdns_lp6_x48_ew_phy_top,SUB_BLOCK_LIB_MODE)                     "func scanshift"

set CONFIG(cadence_mc_ew_controller,LEF_TOP_LAYER)                         14
set CONFIG(cadence_mc_ew_controller,LEF_PG_LAYERS)                         "13 14"
set CONFIG(cadence_mc_ew_controller,MAX_ROUTING_LAYER)                     13
set CONFIG(cadence_mc_ew_controller,CTS_NDR_RULE)                          ndr_2w2s
set CONFIG(cadence_mc_ew_controller,CTS_TOP_PREFER_TOP_LAYER)              12
set CONFIG(cadence_mc_ew_controller,CTS_TOP_PREFER_BOTTOM_LAYER)           7
set CONFIG(cadence_mc_ew_controller,CTS_TRUNK_PREFER_TOP_LAYER)            12
set CONFIG(cadence_mc_ew_controller,CTS_TRUNK_PREFER_BOTTOM_LAYER)         9
set CONFIG(cadence_mc_ew_controller,CTS_LEAF_PREFER_TOP_LAYER)             8
set CONFIG(cadence_mc_ew_controller,CTS_LEAF_PREFER_BOTTOM_LAYER)          7
set CONFIG(cadence_mc_ew_controller,QUEUE)                                 pd
set CONFIG(cadence_mc_ew_controller,CPU)                                   16
set CONFIG(cadence_mc_ew_controller,MEM)                                   [expr 16  * 1024]
set CONFIG(cadence_mc_ew_controller,PWR_NET)                               "VDD"
set CONFIG(cadence_mc_ew_controller,GND_NET)                               "VSS"
set CONFIG(cadence_mc_ew_controller,SUB_BLOCK_LIB_MODE)                    "func"

set CONFIG(databahn_data_pat_gen,LEF_TOP_LAYER)                            10
set CONFIG(databahn_data_pat_gen,LEF_PG_LAYERS)                            "9 10"
set CONFIG(databahn_data_pat_gen,MAX_ROUTING_LAYER)                        9
set CONFIG(databahn_data_pat_gen,CTS_NDR_RULE)                             ndr_2w2s
set CONFIG(databahn_data_pat_gen,CTS_TOP_PREFER_TOP_LAYER)                 9
set CONFIG(databahn_data_pat_gen,CTS_TOP_PREFER_BOTTOM_LAYER)              6
set CONFIG(databahn_data_pat_gen,CTS_TRUNK_PREFER_TOP_LAYER)               9
set CONFIG(databahn_data_pat_gen,CTS_TRUNK_PREFER_BOTTOM_LAYER)            6
set CONFIG(databahn_data_pat_gen,CTS_LEAF_PREFER_TOP_LAYER)                9
set CONFIG(databahn_data_pat_gen,CTS_LEAF_PREFER_BOTTOM_LAYER)             6
set CONFIG(databahn_data_pat_gen,QUEUE)                                    pd
set CONFIG(databahn_data_pat_gen,CPU)                                      8
set CONFIG(databahn_data_pat_gen,MEM)                                      [expr 16  * 1024]
set CONFIG(databahn_data_pat_gen,PWR_NET)                                  "VDD"
set CONFIG(databahn_data_pat_gen,GND_NET)                                  "VSS"
set CONFIG(databahn_data_pat_gen,SUB_BLOCK_LIB_MODE)                       "func"

set CONFIG(tv_chip,LEF_TOP_LAYER)                                          17
set CONFIG(tv_chip,LEF_PG_LAYERS)                                          "17"
set CONFIG(tv_chip,MAX_ROUTING_LAYER)                                      15
set CONFIG(tv_chip,CTS_NDR_RULE)                                           ndr_2w2s
set CONFIG(tv_chip,CTS_TOP_PREFER_TOP_LAYER)                               12
set CONFIG(tv_chip,CTS_TOP_PREFER_BOTTOM_LAYER)                            7
set CONFIG(tv_chip,CTS_TRUNK_PREFER_TOP_LAYER)                             12
set CONFIG(tv_chip,CTS_TRUNK_PREFER_BOTTOM_LAYER)                          9
set CONFIG(tv_chip,CTS_LEAF_PREFER_TOP_LAYER)                              8
set CONFIG(tv_chip,CTS_LEAF_PREFER_BOTTOM_LAYER)                           7
set CONFIG(tv_chip,QUEUE)                                                  pd
set CONFIG(tv_chip,CPU)                                                    16
set CONFIG(tv_chip,PWR_NET)                                                "VDD VDDM_SRAM VDD_PLL_A0_AS VDD_PLL_A0_DS0 VDD_PLL_A0_DS1 VDD_PLL_A1_AS VDD_PLL_A1_DS0 VDD_PLL_A1_DS1 VDDG_HM_CHIP VDD_SENSE VDDQ VDDQ_SENSE VDDQXC VDDQXD VDD2 VDDQ2 VDDQX2 VDDPST VDD_PLL_DSHM VDDHVPLL_FRAC0 VDDPOSTPLL_FRAC0 VDDREFPLL_FRAC0 VDDHVPLL_FRAC1 VDDPOSTPLL_FRAC1 VDDREFPLL_FRAC1 VDDHVPLL_FRAC2 VDDREFPLL_FRAC2 VDDPOSTPLL_FRAC2"
set CONFIG(tv_chip,GND_NET)                                                "VSS POCCTRL POCCTRLD ESD"
set CONFIG(tv_chip,PWR_BUMP)                                               PAD130PITCH_POWER
set CONFIG(tv_chip,GND_BUMP)                                               PAD130PITCH_GROUND
set CONFIG(tv_chip,VSRC_LAYER)                                             AP
set CONFIG(tv_chip,MACRO)                                                  "cdns_ddr1100 fracn_pll fracr_pll cdns_dcc cdns_custom_decap sram gpio esd noise_gen cdns_testio bump tcd mim"
set CONFIG(tv_chip,SUB_BLOCKS)                                             "cdns_lp6_x48_ew_phy_top cadence_mc_ew_controller databahn_data_pat_gen"
set CONFIG(tv_chip,SUB_BLOCK_LIB_MODE)                                     "func scanshift"

set ALL_CONFIG_VARS                                                        "QUEUE GND_BUMP CTS_LEAF_PREFER_BOTTOM_LAYER CPU CTS_NDR_RULE CTS_TRUNK_PREFER_BOTTOM_LAYER MEM VSRC_LAYER PWR_BUMP SUB_BLOCKS LEF_TOP_LAYER CTS_LEAF_PREFER_TOP_LAYER SUB_BLOCK_LIB_MODE PWR_NET CTS_TOP_PREFER_TOP_LAYER MACRO CTS_TOP_PREFER_BOTTOM_LAYER CTS_TRUNK_PREFER_TOP_LAYER GND_NET LEF_PG_LAYERS MAX_ROUTING_LAYER"
##SPECIAL CELLS###
set SPECIAL_CELL(ANTENNACELLNAME)                                          "ANTENNABWP210H6P51CNODSVT"
set SPECIAL_CELL(TIECELLHI)                                                "TIEHXPBWP210H6P51CNODSVT"
set SPECIAL_CELL(TIECELLLO)                                                "TIELXNBWP210H6P51CNODSVT"
set SPECIAL_CELL(TIECELLMAXFANOUT)                                         3
set SPECIAL_CELL(TIECELLMAXDISTANCE)                                       10
set SPECIAL_CELL(DCAP_LIST)                                                "DCAP64XPBWP210H6P51CNODSVT DCAP32XPBWP210H6P51CNODSVT DCAP16XPBWP210H6P51CNODSVT DCAP8XPBWP210H6P51CNODSVT DCAP4XPBWP210H6P51CNODSVT DCAP64XPBWP210H6P51CNODLVTLL DCAP32XPBWP210H6P51CNODLVTLL DCAP16XPBWP210H6P51CNODLVTLL DCAP8XPBWP210H6P51CNODLVTLL DCAP4XPBWP210H6P51CNODLVTLL DCAP64XPBWP210H6P51CNODLVT DCAP32XPBWP210H6P51CNODLVT DCAP16XPBWP210H6P51CNODLVT DCAP8XPBWP210H6P51CNODLVT DCAP4XPBWP210H6P51CNODLVT"
set SPECIAL_CELL(FILL_LIST)                                                "FILL64BWP210H6P51CNODSVT FILL32BWP210H6P51CNODSVT FILL16BWP210H6P51CNODSVT FILL12BWP210H6P51CNODSVT FILL8BWP210H6P51CNODSVT FILL4BWP210H6P51CNODSVT FILL3BWP210H6P51CNODSVT FILL2BWP210H6P51CNODSVT FILL1BWP210H6P51CNODSVT FILL64BWP210H6P51CNODLVTLL FILL32BWP210H6P51CNODLVTLL FILL16BWP210H6P51CNODLVTLL FILL12BWP210H6P51CNODLVTLL FILL8BWP210H6P51CNODLVTLL FILL4BWP210H6P51CNODLVTLL FILL3BWP210H6P51CNODLVTLL FILL2BWP210H6P51CNODLVTLL FILL1BWP210H6P51CNODLVTLL FILL64BWP210H6P51CNODLVT FILL32BWP210H6P51CNODLVT FILL16BWP210H6P51CNODLVT FILL12BWP210H6P51CNODLVT FILL8BWP210H6P51CNODLVT FILL4BWP210H6P51CNODLVT FILL3BWP210H6P51CNODLVT FILL2BWP210H6P51CNODLVT FILL1BWP210H6P51CNODLVT FILL64BWP210H6P51CNODULVTLL FILL32BWP210H6P51CNODULVTLL FILL16BWP210H6P51CNODULVTLL FILL12BWP210H6P51CNODULVTLL FILL8BWP210H6P51CNODULVTLL FILL4BWP210H6P51CNODULVTLL FILL3BWP210H6P51CNODULVTLL FILL2BWP210H6P51CNODULVTLL FILL1BWP210H6P51CNODULVTLL FILL64BWP210H6P51CNODULVT FILL32BWP210H6P51CNODULVT FILL16BWP210H6P51CNODULVT FILL12BWP210H6P51CNODULVT FILL8BWP210H6P51CNODULVT FILL4BWP210H6P51CNODULVT FILL3BWP210H6P51CNODULVT FILL2BWP210H6P51CNODULVT FILL1BWP210H6P51CNODULVT"
set SPECIAL_CELL(INCLUDE_PHYSICAL_CELL)                                    "*CAP* GFILL*"
set SPECIAL_CELL(EXCLUDE_CELL)                                             "*FILL* TAPCELL* BOUNDARY* *WALL* *_FEOL* *_BEOL* *DTCD* PCORNER_V PENDCAP_H cdns_ddr*_spacer_1u* LUP_1D8_GR_FB1_H"
set SPECIAL_CELL(CLOCK_GATING_CELL)                                        "CKLNQD4BWP210H6P51CNODULVT CKLNQD6BWP210H6P51CNODULVT CKLNQD8BWP210H6P51CNODULVT"
set SPECIAL_CELL(CLOCK_INVERTER_CELL)                                      "DCCKN*ULVT"
set SPECIAL_CELL(CLOCK_BUFFER_CELL)                                        "DCCKB*ULVT"
set SPECIAL_CELL(CLOCK_LOGIC_CELL)                                         "CK*ULVT"

###LIB SET NAMES####
set LIBSET_NAMES {}
lappend LIBSET_NAMES func_ssgnp_0p765v_125c_cworst_CCworst_T_setup
lappend LIBSET_NAMES func_ssgnp_0p765v_m40c_cworst_CCworst_T_setup
lappend LIBSET_NAMES func_ffgnp_0p935v_125c_cbest_CCbest_T_hold
lappend LIBSET_NAMES func_ffgnp_0p935v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES func_ssgnp_0p765v_125c_cworst_CCworst_T_hold
lappend LIBSET_NAMES func_ssgnp_0p765v_m40c_cworst_CCworst_T_hold
lappend LIBSET_NAMES func_tt_0p85v_25c_typical_setup
lappend LIBSET_NAMES func_tt_0p85v_85c_typical_setup
lappend LIBSET_NAMES func_ssgnp_0p675v_125c_cworst_CCworst_T_setup
lappend LIBSET_NAMES func_ssgnp_0p675v_m40c_cworst_CCworst_T_setup
lappend LIBSET_NAMES func_ffgnp_0p825v_125c_cbest_CCbest_T_hold
lappend LIBSET_NAMES func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES func_ssgnp_0p675v_125c_cworst_CCworst_T_hold
lappend LIBSET_NAMES func_ssgnp_0p675v_m40c_cworst_CCworst_T_hold
lappend LIBSET_NAMES func_tt_0p75v_25c_typical_setup
lappend LIBSET_NAMES func_tt_0p75v_85c_typical_setup
lappend LIBSET_NAMES func_ssgnp_0p63v_125c_cworst_CCworst_T_setup
lappend LIBSET_NAMES func_ssgnp_0p63v_m40c_cworst_CCworst_T_setup
lappend LIBSET_NAMES func_ffgnp_0p77v_125c_cbest_CCbest_T_hold
lappend LIBSET_NAMES func_ffgnp_0p77v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES func_ssgnp_0p63v_125c_cworst_CCworst_T_hold
lappend LIBSET_NAMES func_ssgnp_0p63v_m40c_cworst_CCworst_T_hold
lappend LIBSET_NAMES func_tt_0p7v_25c_typical_setup
lappend LIBSET_NAMES func_tt_0p7v_85c_typical_setup
lappend LIBSET_NAMES scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_setup
lappend LIBSET_NAMES scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_setup
lappend LIBSET_NAMES scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_hold
lappend LIBSET_NAMES scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_hold
lappend LIBSET_NAMES scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_hold
lappend LIBSET_NAMES scanshift_tt_0p85v_25c_typical_setup
lappend LIBSET_NAMES scanshift_tt_0p85v_85c_typical_setup
lappend LIBSET_NAMES scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_setup
lappend LIBSET_NAMES scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_setup
lappend LIBSET_NAMES scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_hold
lappend LIBSET_NAMES scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_hold
lappend LIBSET_NAMES scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_hold
lappend LIBSET_NAMES scanshift_tt_0p75v_25c_typical_setup
lappend LIBSET_NAMES scanshift_tt_0p75v_85c_typical_setup
lappend LIBSET_NAMES scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_setup
lappend LIBSET_NAMES scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_setup
lappend LIBSET_NAMES scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_hold
lappend LIBSET_NAMES scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_hold
lappend LIBSET_NAMES scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_hold
lappend LIBSET_NAMES scanshift_tt_0p7v_25c_typical_setup
lappend LIBSET_NAMES scanshift_tt_0p7v_85c_typical_setup
##>>>LIB FILES<<<###
##0:LEFS FILES:
set LEFS(STD)                                                              "/process/tsmcN5/data/stdcell/n5/TSMC/PRTF_Innovus_5nm_014_Cad_V13a/PRTF/PRTF_Innovus_5nm_014_Cad_V13a/PR_tech/Cadence/LefHeader/Standard/VHV/PRTF_Innovus_N5_15M_1X1Xb1Xe1Ya1Yb5Y2Yy2Z_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_H210_SHDMIM.13a.tlef /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_10w10s.lef /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_1w2s.lef /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w1s.lef /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w2s_em.lef /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w2s.lef /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w3s_em.lef /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_2w3s.lef /projects/TC70_LPDDR6_N5P/libs/ndr/ndr_8w5s.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lef/tcbn05_bwph210l6p51cnod_base_svt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lef/tcbn05_bwph210l6p51cnod_base_svt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lef/tcbn05_bwph210l6p51cnod_base_lvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lef/tcbn05_bwph210l6p51cnod_base_lvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_lvtll_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_lvtll.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvtll_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvtll.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lef/tcbn05_bwph210l6p51cnod_base_elvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lef/tcbn05_bwph210l6p51cnod_base_elvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lef/tcbn05_bwph210l6p51cnod_pm_svt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lef/tcbn05_bwph210l6p51cnod_pm_svt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_lvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_lvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lef/tcbn05_bwph210l6p51cnod_pm_lvtll_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lef/tcbn05_bwph210l6p51cnod_pm_lvtll.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_ulvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_ulvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lef/tcbn05_bwph210l6p51cnod_pm_ulvtll_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lef/tcbn05_bwph210l6p51cnod_pm_ulvtll.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_elvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lef/tcbn05_bwph210l6p51cnod_pm_elvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_svt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_svt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_lvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_lvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lef/tcbn05_bwph210l6p51cnod_lvl_lvtll_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lef/tcbn05_bwph210l6p51cnod_lvl_lvtll.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_ulvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_ulvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lef/tcbn05_bwph210l6p51cnod_lvl_ulvtll_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lef/tcbn05_bwph210l6p51cnod_lvl_ulvtll.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_elvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lef/tcbn05_bwph210l6p51cnod_lvl_elvt.lef"
set LEFS(MACRO,cdns_ddr1100)                                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lef/cdns_ddr1100_h.lef"
set LEFS(MACRO,cdns_dcc)                                                   "/projects/TC70_LPDDR6_N5P/libs/customcell/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base.antenna.lef"
set LEFS(MACRO,fracn_pll)                                                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lef/PLLTS5FFPLAFRACN.lef"
set LEFS(MACRO,fracr_pll)                                                  "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lef/PLLTS5FFPLJFRACR2.lef"
set LEFS(MACRO,cdns_custom_decap)                                          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lef/cdns_ddr_custom_decap_unit_cells.lef"
set LEFS(MACRO,noise_gen)                                                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lef/cdns_ddr_noisegen_v.antenna.lef"
set LEFS(MACRO,sram)                                                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/LEF/ts1n05mblvta16384x39m16qwbzhodcp.lef"
set LEFS(MACRO,cdns_testio)                                                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lef/cdns_lpddr6_testio.lef"
set LEFS(MACRO,gpio)                                                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lef/mt/15m/15M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_5Y_VHVHV_2YY2Z/lef/tphn05_12gpio_15lm.lef"
set LEFS(MACRO,bump)                                                       "/process/tsmcN5/data/stdcell/n5v/TSMC/tpbn05v_cu_round_bump_100a/lef/fc/fc_bot/APRDL/lef/tpbn05v_cu_round_bump.lef"
set LEFS(MACRO,tcd)                                                        "/process/tsmcN5/data/stdcell/n5/TSMC/N5_DTCD_library_kit_v1d3.1/lef/N5_DTCD_M11/N5_DTCD_v1d2.lef"
set LEFS(MACRO,esd)                                                        "/process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12lup_120a/lef/mt/15m/15M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_5Y_VHVHV_2YY2Z/lef/tpmn05_12lup_15lm.lef /process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12esd_120b/lef/mt/15m/15M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_5Y_VHVHV_2YY2Z/lef/tpmn05_12esd_15lm.lef"
set LEFS(MACRO,mim)                                                        "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_custom_mimcap_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_130P_UBM80_DR_r100.20251208/lef/cdns_ddr1100_custom_mimcap_h.lef"
set LEFS(DESIGN,cdns_lp6_x48_ew_phy_as_top)                                "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlef/cdns_lp6_x48_ew_phy_as_top.lef"
set LEFS(DESIGN,cdns_lp6_x48_ew_phy_ds_top)                                "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlef/cdns_lp6_x48_ew_phy_ds_top.lef"
set LEFS(DESIGN,cdns_lp6_x48_ew_phy_top)                                   "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlef/cdns_lp6_x48_ew_phy_top.lef"
set LEFS(DESIGN,cadence_mc_ew_controller)                                  "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlef/cadence_mc_ew_controller.lef"
set LEFS(DESIGN,databahn_data_pat_gen)                                     "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlef/databahn_data_pat_gen.lef"

##1:CDLS FILES:
set CDLS(STD)                                                              "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spice/tcbn05_bwph210l6p51cnod_base_elvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spice/tcbn05_bwph210l6p51cnod_base_lvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spice/tcbn05_bwph210l6p51cnod_base_lvtll.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spice/tcbn05_bwph210l6p51cnod_base_svt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spice/tcbn05_bwph210l6p51cnod_base_ulvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spice/tcbn05_bwph210l6p51cnod_base_ulvtll.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spice/tcbn05_bwph210l6p51cnod_pm_elvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spice/tcbn05_bwph210l6p51cnod_pm_lvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spice/tcbn05_bwph210l6p51cnod_pm_lvtll.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spice/tcbn05_bwph210l6p51cnod_pm_svt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spice/tcbn05_bwph210l6p51cnod_pm_ulvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spice/tcbn05_bwph210l6p51cnod_pm_ulvtll.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spice/tcbn05_bwph210l6p51cnod_lvl_elvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spice/tcbn05_bwph210l6p51cnod_lvl_lvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spice/tcbn05_bwph210l6p51cnod_lvl_lvtll.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spice/tcbn05_bwph210l6p51cnod_lvl_svt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spice/tcbn05_bwph210l6p51cnod_lvl_ulvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spice/tcbn05_bwph210l6p51cnod_lvl_ulvtll.spi"
set CDLS(MACRO,cdns_ddr1100)                                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/cdl/cdns_ddr1100_h.cdl"
set CDLS(MACRO,cdns_dcc)                                                   "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/cdl/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base.cdl"
set CDLS(MACRO,fracn_pll)                                                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/netlist/PLLTS5FFPLAFRACN.cdl"
set CDLS(MACRO,fracr_pll)                                                  "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/netlist/PLLTS5FFPLJFRACR2.cdl"
set CDLS(MACRO,cdns_custom_decap)                                          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/cdl/cdns_ddr_custom_decap_unit_cells.cdl"
set CDLS(MACRO,noise_gen)                                                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/cdl/cdns_ddr_noisegen_v.cdl"
set CDLS(MACRO,sram)                                                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/SPICE/ts1n05mblvta16384x39m16qwbzhodcp.spi"
set CDLS(MACRO,cdns_testio)                                                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/cdl/cdns_lpddr6_testio.cdl"
set CDLS(MACRO,gpio)                                                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/spice/tphn05_12gpio.spi"
set CDLS(MACRO,esd)                                                        "/process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12lup_120a/spice/tpmn05_12lup.spi /process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12esd_120b/spice/tpmn05_12esd.spi"
set CDLS(MACRO,mim)                                                        "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_custom_mimcap_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_130P_UBM80_DR_r100.20251208/cdl/cdns_ddr1100_custom_mimcap_h.cdl"
set CDLS(DESIGN,cdns_lp6_x48_ew_phy_as_top)                                "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/latest/cdl/cdns_lp6_x48_ew_phy_as_top.cdl"
set CDLS(DESIGN,cdns_lp6_x48_ew_phy_ds_top)                                "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/latest/cdl/cdns_lp6_x48_ew_phy_ds_top.cdl"
set CDLS(DESIGN,cdns_lp6_x48_ew_phy_top)                                   "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/latest/cdl/cdns_lp6_x48_ew_phy_top.cdl"
set CDLS(DESIGN,cadence_mc_ew_controller)                                  "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/latest/cdl/cadence_mc_ew_controller.cdl"
set CDLS(DESIGN,databahn_data_pat_gen)                                     "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/latest/cdl/databahn_data_pat_gen.cdl"

##2:GDS FILES:
set GDS(STD)                                                               "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/gds/tcbn05_bwph210l6p51cnod_base_elvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/gds/tcbn05_bwph210l6p51cnod_base_lvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/gds/tcbn05_bwph210l6p51cnod_base_lvtll.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/gds/tcbn05_bwph210l6p51cnod_base_svt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/gds/tcbn05_bwph210l6p51cnod_base_ulvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/gds/tcbn05_bwph210l6p51cnod_base_ulvtll.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/gds/tcbn05_bwph210l6p51cnod_pm_elvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/gds/tcbn05_bwph210l6p51cnod_pm_lvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/gds/tcbn05_bwph210l6p51cnod_pm_lvtll.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/gds/tcbn05_bwph210l6p51cnod_pm_svt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/gds/tcbn05_bwph210l6p51cnod_pm_ulvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/gds/tcbn05_bwph210l6p51cnod_pm_ulvtll.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/gds/tcbn05_bwph210l6p51cnod_lvl_elvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/gds/tcbn05_bwph210l6p51cnod_lvl_lvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/gds/tcbn05_bwph210l6p51cnod_lvl_lvtll.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/gds/tcbn05_bwph210l6p51cnod_lvl_svt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/gds/tcbn05_bwph210l6p51cnod_lvl_ulvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/gds/tcbn05_bwph210l6p51cnod_lvl_ulvtll.gds"
set GDS(MACRO,cdns_ddr1100)                                                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/gds/cdns_ddr1100_h.gds.gz"
set GDS(MACRO,cdns_dcc)                                                    "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/gds/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base.gds"
set GDS(MACRO,fracn_pll)                                                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/gds/PLLTS5FFPLAFRACN.gds"
set GDS(MACRO,fracr_pll)                                                   "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/gds/PLLTS5FFPLJFRACR2.gds"
set GDS(MACRO,cdns_custom_decap)                                           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/gds/cdns_ddr_custom_decap_unit_cells.gds"
set GDS(MACRO,noise_gen)                                                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/gds/cdns_ddr_noisegen_v.gds.gz"
set GDS(MACRO,sram)                                                        "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/GDSII/ts1n05mblvta16384x39m16qwbzhodcp.gds"
set GDS(MACRO,cdns_testio)                                                 "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/gds/cdns_lpddr6_testio.gds.gz"
set GDS(MACRO,gpio)                                                        "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/gds/mt/15m/15M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_5Y_VHVHV_2YY2Z/tphn05_12gpio.gds"
set GDS(MACRO,bump)                                                        "/process/tsmcN5/data/stdcell/n5v/TSMC/tpbn05v_cu_round_bump_100a/gds/fc/fc_bot/APRDL/tpbn05v_cu_round_bump.gds"
set GDS(MACRO,tcd)                                                         "/process/tsmcN5/data/stdcell/n5/TSMC/N5_DTCD_library_kit_v1d3.1/gds/N5P_DTCD_full_stack_general_v0d5_190612.gds"
set GDS(MACRO,esd)                                                         "/process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12lup_120a/gds/mt/15m/15M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_5Y_VHVHV_2YY2Z/tpmn05_12lup.gds /process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12esd_120b/gds/mt/15m/15M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_5Y_VHVHV_2YY2Z/tpmn05_12esd.gds"
set GDS(MACRO,mim)                                                         "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_custom_mimcap_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_130P_UBM80_DR_r100.20251208/gds/cdns_ddr1100_custom_mimcap_h.gds"
set GDS(DESIGN,cdns_lp6_x48_ew_phy_as_top)                                 "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/latest/gds/cdns_lp6_x48_ew_phy_as_top.nomerged.gds.gz"
set GDS(DESIGN,cdns_lp6_x48_ew_phy_ds_top)                                 "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/latest/gds/cdns_lp6_x48_ew_phy_ds_top.nomerged.gds.gz"
set GDS(DESIGN,cdns_lp6_x48_ew_phy_top)                                    "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/latest/gds/cdns_lp6_x48_ew_phy_top.uniquify.gds.gz"
set GDS(DESIGN,cadence_mc_ew_controller)                                   "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/latest/gds/cadence_mc_ew_controller.nomerged.gds.gz"
set GDS(DESIGN,databahn_data_pat_gen)                                      "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/latest/gds/databahn_data_pat_gen.nomerged.gds.gz"

##3:LIB FILES:

###STD LIBs###
set LIB_STD(ssgnp_0p765v_125c_cworst_CCworst_T)                            "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz"
set LIB_STD(ssgnp_0p765v_m40c_cworst_CCworst_T)                            "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz"
set LIB_STD(ffgnp_0p935v_125c_cbest_CCbest_T)                              "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz"
set LIB_STD(ffgnp_0p935v_m40c_cbest_CCbest_T)                              "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p935v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz"
set LIB_STD(tt_0p85v_85c_typical)                                          "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svttt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvttt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvttt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvttt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svttt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvttt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvttt_0p85v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svttt_0p85v_0p85v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p85v_0p85v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p85v_0p85v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p85v_0p85v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p85v_0p85v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p85v_0p85v_85c_typical_lvf_p_ccs.lib.gz"
set LIB_STD(tt_0p85v_25c_typical)                                          "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svttt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvttt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvttt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvttt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svttt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvttt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvttt_0p85v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svttt_0p85v_0p85v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p85v_0p85v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p85v_0p85v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p85v_0p85v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p85v_0p85v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p85v_0p85v_25c_typical_lvf_p_ccs.lib.gz"
set LIB_STD(ssgnp_0p675v_125c_cworst_CCworst_T)                            "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz"
set LIB_STD(ssgnp_0p675v_m40c_cworst_CCworst_T)                            "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz"
set LIB_STD(ffgnp_0p825v_125c_cbest_CCbest_T)                              "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz"
set LIB_STD(ffgnp_0p825v_m40c_cbest_CCbest_T)                              "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz"
set LIB_STD(tt_0p75v_85c_typical)                                          "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p75v_85c_typical_lvf_p_ccs.lib.gz"
set LIB_STD(tt_0p75v_25c_typical)                                          "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p75v_25c_typical_lvf_p_ccs.lib.gz"
set LIB_STD(ssgnp_0p63v_125c_cworst_CCworst_T)                             "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_lvf_p_ccs.lib.gz"
set LIB_STD(ssgnp_0p63v_m40c_cworst_CCworst_T)                             "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_lvf_p_ccs.lib.gz"
set LIB_STD(ffgnp_0p77v_125c_cbest_CCbest_T)                               "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz"
set LIB_STD(ffgnp_0p77v_m40c_cbest_CCbest_T)                               "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p77v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_lvf_p_ccs.lib.gz"
set LIB_STD(tt_0p7v_85c_typical)                                           "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svttt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvttt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvttt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvttt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svttt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvttt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvttt_0p7v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p7v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p7v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p7v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p7v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p7v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p7v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svttt_0p7v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p7v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p7v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p7v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p7v_0p75v_85c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p7v_0p75v_85c_typical_lvf_p_ccs.lib.gz"
set LIB_STD(tt_0p7v_25c_typical)                                           "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svttt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvttt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvttt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvttt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_svttt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_elvttt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_pm_lvttt_0p7v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p7v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p7v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p7v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p7v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p7v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p7v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_svttt_0p7v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p7v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p7v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p7v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p7v_0p75v_25c_typical_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/lvf/ccs/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p7v_0p75v_25c_typical_lvf_p_ccs.lib.gz"
###MACRO LIBs###
set LIB_MACRO(ssgnp_0p765v_125c_cworst_CCworst_T,cdns_ddr1100)             "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ss_0p765v_0p470v_125c.lib"
set LIB_MACRO(ssgnp_0p765v_m40c_cworst_CCworst_T,cdns_ddr1100)             "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ss_0p765v_0p470v_m40c.lib"
set LIB_MACRO(ffgnp_0p935v_125c_cbest_CCbest_T,cdns_ddr1100)               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ff_0p935v_0p570v_125c.lib"
set LIB_MACRO(ffgnp_0p935v_m40c_cbest_CCbest_T,cdns_ddr1100)               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ff_0p935v_0p570v_125c.lib"
set LIB_MACRO(tt_0p85v_85c_typical,cdns_ddr1100)                           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_tt_0p850v_0p500v_85c.lib"
set LIB_MACRO(tt_0p85v_25c_typical,cdns_ddr1100)                           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_tt_0p850v_0p500v_25c.lib"
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,cdns_ddr1100)             "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ss_0p675v_0p470v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,cdns_ddr1100)             "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ss_0p675v_0p470v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,cdns_ddr1100)               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ff_0p825v_0p570v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,cdns_ddr1100)               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ff_0p825v_0p570v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,cdns_ddr1100)                           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_tt_0p750v_0p500v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,cdns_ddr1100)                           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_tt_0p750v_0p500v_25c.lib"
set LIB_MACRO(ssgnp_0p63v_125c_cworst_CCworst_T,cdns_ddr1100)              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ss_0p630v_0p470v_125c.lib"
set LIB_MACRO(ssgnp_0p63v_m40c_cworst_CCworst_T,cdns_ddr1100)              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ss_0p630v_0p470v_m40c.lib"
set LIB_MACRO(ffgnp_0p77v_125c_cbest_CCbest_T,cdns_ddr1100)                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ff_0p770v_0p570v_125c.lib"
set LIB_MACRO(ffgnp_0p77v_m40c_cbest_CCbest_T,cdns_ddr1100)                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_ff_0p770v_0p570v_125c.lib"
set LIB_MACRO(tt_0p7v_85c_typical,cdns_ddr1100)                            "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_tt_0p700v_0p500v_85c.lib"
set LIB_MACRO(tt_0p7v_25c_typical,cdns_ddr1100)                            "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1100_h_t5g_x48_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_130P_UBM80_DC_r100_v1p11.20251208/lib/cdns_ddr1100_h_lpddr6_tt_0p700v_0p500v_25c.lib"

set LIB_MACRO(ssgnp_0p765v_125c_cworst_CCworst_T,cdns_dcc)                 "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ssgnp_cworst_CCworst_T_0p765v_125c.lib"
set LIB_MACRO(ssgnp_0p765v_m40c_cworst_CCworst_T,cdns_dcc)                 "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ssgnp_cworst_CCworst_T_0p765v_m40c.lib"
set LIB_MACRO(ffgnp_0p935v_125c_cbest_CCbest_T,cdns_dcc)                   "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ffgnp_cbest_CCbest_0p935v_125c.lib"
set LIB_MACRO(ffgnp_0p935v_m40c_cbest_CCbest_T,cdns_dcc)                   "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ffgnp_cbest_CCbest_0p935v_125c.lib"
set LIB_MACRO(tt_0p85v_85c_typical,cdns_dcc)                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_tt_typical_0p85v_85c.lib"
set LIB_MACRO(tt_0p85v_25c_typical,cdns_dcc)                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_tt_typical_0p85v_25c.lib"
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,cdns_dcc)                 "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ssgnp_cworst_CCworst_T_0p675v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,cdns_dcc)                 "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ssgnp_cworst_CCworst_T_0p675v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,cdns_dcc)                   "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ffgnp_cbest_CCbest_0p825v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,cdns_dcc)                   "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ffgnp_cbest_CCbest_0p825v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,cdns_dcc)                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_tt_typical_0p75v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,cdns_dcc)                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_tt_typical_0p75v_25c.lib"
set LIB_MACRO(ssgnp_0p63v_125c_cworst_CCworst_T,cdns_dcc)                  "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ssgnp_cworst_CCworst_T_0p63v_125c.lib"
set LIB_MACRO(ssgnp_0p63v_m40c_cworst_CCworst_T,cdns_dcc)                  "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ssgnp_cworst_CCworst_T_0p63v_m40c.lib"
set LIB_MACRO(ffgnp_0p77v_125c_cbest_CCbest_T,cdns_dcc)                    "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ffgnp_cbest_CCbest_0p77v_125c.lib"
set LIB_MACRO(ffgnp_0p77v_m40c_cbest_CCbest_T,cdns_dcc)                    "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ffgnp_cbest_CCbest_0p77v_125c.lib"
set LIB_MACRO(tt_0p7v_85c_typical,cdns_dcc)                                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_tt_typical_0p7v_85c.lib"
set LIB_MACRO(tt_0p7v_25c_typical,cdns_dcc)                                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_15M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_5Y_vhvhv_2Yy_r300.20250905/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_tt_typical_0p7v_25c.lib"

set LIB_MACRO(ssgnp_0p765v_125c_cworst_CCworst_T,fracn_pll)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_SSGNP_0P765V_125C_Cworst_CCworst_T.lib"
set LIB_MACRO(ssgnp_0p765v_m40c_cworst_CCworst_T,fracn_pll)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_SSGNP_0P765V_M40C_Cworst_CCworst_T.lib"
set LIB_MACRO(ffgnp_0p935v_125c_cbest_CCbest_T,fracn_pll)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_FFGNP_0P935V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(ffgnp_0p935v_m40c_cbest_CCbest_T,fracn_pll)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_FFGNP_0P935V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(tt_0p85v_85c_typical,fracn_pll)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_TT_0P85V_85C_Typical.lib"
set LIB_MACRO(tt_0p85v_25c_typical,fracn_pll)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_TT_0P85V_25C_Typical.lib"
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,fracn_pll)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_SSGNP_0P675V_125C_Cworst_CCworst_T.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,fracn_pll)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_SSGNP_0P675V_M40C_Cworst_CCworst_T.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,fracn_pll)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,fracn_pll)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(tt_0p75v_85c_typical,fracn_pll)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_TT_0P75V_85C_Typical.lib"
set LIB_MACRO(tt_0p75v_25c_typical,fracn_pll)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_TT_0P75V_25C_Typical.lib"
set LIB_MACRO(ssgnp_0p63v_125c_cworst_CCworst_T,fracn_pll)                 "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_SSGNP_0P675V_125C_Cworst_CCworst_T.lib"
set LIB_MACRO(ssgnp_0p63v_m40c_cworst_CCworst_T,fracn_pll)                 "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_SSGNP_0P675V_M40C_Cworst_CCworst_T.lib"
set LIB_MACRO(ffgnp_0p77v_125c_cbest_CCbest_T,fracn_pll)                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(ffgnp_0p77v_m40c_cbest_CCbest_T,fracn_pll)                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(tt_0p7v_85c_typical,fracn_pll)                               "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_TT_0P75V_85C_Typical.lib"
set LIB_MACRO(tt_0p7v_25c_typical,fracn_pll)                               "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_TT_0P75V_25C_Typical.lib"

set LIB_MACRO(ssgnp_0p765v_125c_cworst_CCworst_T,fracr_pll)                "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_SSGNP_0P765V_125C_Cworst_CCworst_T.lib"
set LIB_MACRO(ssgnp_0p765v_m40c_cworst_CCworst_T,fracr_pll)                "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_SSGNP_0P765V_M40C_Cworst_CCworst_T.lib"
set LIB_MACRO(ffgnp_0p935v_125c_cbest_CCbest_T,fracr_pll)                  "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_FFGNP_0P935V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(ffgnp_0p935v_m40c_cbest_CCbest_T,fracr_pll)                  "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_FFGNP_0P935V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(tt_0p85v_85c_typical,fracr_pll)                              "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_TT_0P85V_85C_Typical.lib"
set LIB_MACRO(tt_0p85v_25c_typical,fracr_pll)                              "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_TT_0P85V_25C_Typical.lib"
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,fracr_pll)                "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_SSGNP_0P675V_125C_Cworst_CCworst_T.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,fracr_pll)                "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_SSGNP_0P675V_M40C_Cworst_CCworst_T.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,fracr_pll)                  "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,fracr_pll)                  "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(tt_0p75v_85c_typical,fracr_pll)                              "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_TT_0P75V_85C_Typical.lib"
set LIB_MACRO(tt_0p75v_25c_typical,fracr_pll)                              "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_TT_0P75V_25C_Typical.lib"
set LIB_MACRO(ssgnp_0p63v_125c_cworst_CCworst_T,fracr_pll)                 "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_SSGNP_0P675V_125C_Cworst_CCworst_T.lib"
set LIB_MACRO(ssgnp_0p63v_m40c_cworst_CCworst_T,fracr_pll)                 "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_SSGNP_0P675V_M40C_Cworst_CCworst_T.lib"
set LIB_MACRO(ffgnp_0p77v_125c_cbest_CCbest_T,fracr_pll)                   "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(ffgnp_0p77v_m40c_cbest_CCbest_T,fracr_pll)                   "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(tt_0p7v_85c_typical,fracr_pll)                               "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_TT_0P75V_85C_Typical.lib"
set LIB_MACRO(tt_0p7v_25c_typical,fracr_pll)                               "/proj/vorm/pll_sc/ts5ffp/PLLTS5FFPLJFRACR2_2022_10_18_v1p1p0p1p1_BE/PLLTS5FFPLJFRACR2/lib/PLLTS5FFPLJFRACR2_TT_0P75V_25C_Typical.lib"

set LIB_MACRO(ssgnp_0p765v_125c_cworst_CCworst_T,cdns_custom_decap)        "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ss_0p675v_0p47v_125c.lib"
set LIB_MACRO(ssgnp_0p765v_m40c_cworst_CCworst_T,cdns_custom_decap)        "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ss_0p675v_0p47v_m40c.lib"
set LIB_MACRO(ffgnp_0p935v_125c_cbest_CCbest_T,cdns_custom_decap)          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ff_0p825v_0p57v_125c.lib"
set LIB_MACRO(ffgnp_0p935v_m40c_cbest_CCbest_T,cdns_custom_decap)          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ff_0p825v_0p57v_125c.lib"
set LIB_MACRO(tt_0p85v_85c_typical,cdns_custom_decap)                      "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_tt_0p85v_0p5v_85c.lib"
set LIB_MACRO(tt_0p85v_25c_typical,cdns_custom_decap)                      "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_tt_0p85v_0p5v_25c.lib"
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,cdns_custom_decap)        "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ss_0p675v_0p47v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,cdns_custom_decap)        "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ss_0p675v_0p47v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,cdns_custom_decap)          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ff_0p825v_0p57v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,cdns_custom_decap)          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ff_0p825v_0p57v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,cdns_custom_decap)                      "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_tt_0p75v_0p5v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,cdns_custom_decap)                      "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_tt_0p75v_0p5v_25c.lib"
set LIB_MACRO(ssgnp_0p63v_125c_cworst_CCworst_T,cdns_custom_decap)         "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ss_0p63v_0p47v_125c.lib"
set LIB_MACRO(ssgnp_0p63v_m40c_cworst_CCworst_T,cdns_custom_decap)         "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ss_0p63v_0p47v_m40c.lib"
set LIB_MACRO(ffgnp_0p77v_125c_cbest_CCbest_T,cdns_custom_decap)           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ff_0p77v_0p57v_125c.lib"
set LIB_MACRO(ffgnp_0p77v_m40c_cbest_CCbest_T,cdns_custom_decap)           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ff_0p77v_0p57v_125c.lib"
set LIB_MACRO(tt_0p7v_85c_typical,cdns_custom_decap)                       "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_tt_0p7v_0p5v_85c.lib"
set LIB_MACRO(tt_0p7v_25c_typical,cdns_custom_decap)                       "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_tt_0p7v_0p5v_25c.lib"

set LIB_MACRO(ssgnp_0p765v_125c_cworst_CCworst_T,noise_gen)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ss_0p765v_0p47v_125c.lib"
set LIB_MACRO(ssgnp_0p765v_m40c_cworst_CCworst_T,noise_gen)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ss_0p765v_0p47v_m40c.lib"
set LIB_MACRO(ffgnp_0p935v_125c_cbest_CCbest_T,noise_gen)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ff_0p935v_0p57v_125c.lib"
set LIB_MACRO(ffgnp_0p935v_m40c_cbest_CCbest_T,noise_gen)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ff_0p935v_0p57v_125c.lib"
set LIB_MACRO(tt_0p85v_85c_typical,noise_gen)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_tt_0p85v_0p5v_85c.lib"
set LIB_MACRO(tt_0p85v_25c_typical,noise_gen)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_tt_0p85v_0p5v_25c.lib"
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,noise_gen)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ss_0p675v_0p47v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,noise_gen)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ss_0p675v_0p47v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,noise_gen)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ff_0p825v_0p57v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,noise_gen)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ff_0p825v_0p57v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,noise_gen)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_tt_0p75v_0p5v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,noise_gen)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_tt_0p75v_0p5v_25c.lib"
set LIB_MACRO(ssgnp_0p63v_125c_cworst_CCworst_T,noise_gen)                 "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ss_0p63v_0p47v_125c.lib"
set LIB_MACRO(ssgnp_0p63v_m40c_cworst_CCworst_T,noise_gen)                 "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ss_0p63v_0p47v_m40c.lib"
set LIB_MACRO(ffgnp_0p77v_125c_cbest_CCbest_T,noise_gen)                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ff_0p77v_0p57v_125c.lib"
set LIB_MACRO(ffgnp_0p77v_m40c_cbest_CCbest_T,noise_gen)                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_ff_0p77v_0p57v_125c.lib"
set LIB_MACRO(tt_0p7v_85c_typical,noise_gen)                               "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_tt_0p7v_0p5v_85c.lib"
set LIB_MACRO(tt_0p7v_25c_typical,noise_gen)                               "/process/tsmcN5/data/stdcell/n5gp/CDNS/cdns_ddr_noisegen_v_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_r200_v1p1.20251125/lib/cdns_ddr_noisegen_v_lpddr5x_tt_0p7v_0p5v_25c.lib"

set LIB_MACRO(ssgnp_0p765v_125c_cworst_CCworst_T,sram)                     "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ssgnp_0p765v_0p675v_125c_cworst_ccworst_t.lib"
set LIB_MACRO(ssgnp_0p765v_m40c_cworst_CCworst_T,sram)                     "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ssgnp_0p765v_0p675v_m40c_cworst_ccworst_t.lib"
set LIB_MACRO(ffgnp_0p935v_125c_cbest_CCbest_T,sram)                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ffgnp_0p935v_0p825v_125c_cbest_ccbest.lib"
set LIB_MACRO(ffgnp_0p935v_m40c_cbest_CCbest_T,sram)                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ffgnp_0p935v_0p825v_125c_cbest_ccbest.lib"
set LIB_MACRO(tt_0p85v_85c_typical,sram)                                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_tt_0p850v_0p750v_85c_typical.lib"
set LIB_MACRO(tt_0p85v_25c_typical,sram)                                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_tt_0p850v_0p750v_25c_typical.lib"
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,sram)                     "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ssgnp_0p675v_0p675v_125c_cworst_ccworst_t.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,sram)                     "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ssgnp_0p675v_0p675v_m40c_cworst_ccworst_t.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,sram)                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ffgnp_0p825v_0p825v_125c_cbest_ccbest.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,sram)                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ffgnp_0p825v_0p825v_125c_cbest_ccbest.lib"
set LIB_MACRO(tt_0p75v_85c_typical,sram)                                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_tt_0p750v_0p750v_85c_typical.lib"
set LIB_MACRO(tt_0p75v_25c_typical,sram)                                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_tt_0p750v_0p750v_25c_typical.lib"
set LIB_MACRO(ssgnp_0p63v_125c_cworst_CCworst_T,sram)                      "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ssgnp_0p630v_0p675v_125c_cworst_ccworst_t.lib"
set LIB_MACRO(ssgnp_0p63v_m40c_cworst_CCworst_T,sram)                      "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ssgnp_0p630v_0p675v_m40c_cworst_ccworst_t.lib"
set LIB_MACRO(ffgnp_0p77v_125c_cbest_CCbest_T,sram)                        "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ffgnp_0p770v_0p825v_125c_cbest_ccbest.lib"
set LIB_MACRO(ffgnp_0p77v_m40c_cbest_CCbest_T,sram)                        "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_ffgnp_0p770v_0p825v_125c_cbest_ccbest.lib"
set LIB_MACRO(tt_0p7v_85c_typical,sram)                                    "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_tt_0p700v_0p750v_85c_typical.lib"
set LIB_MACRO(tt_0p7v_25c_typical,sram)                                    "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhodcp_110c/CCS/ts1n05mblvta16384x39m16qwbzhodcp_tt_0p700v_0p750v_25c_typical.lib"

set LIB_MACRO(ssgnp_0p765v_125c_cworst_CCworst_T,cdns_testio)              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ss_0p765v_0p470v_125c.lib"
set LIB_MACRO(ssgnp_0p765v_m40c_cworst_CCworst_T,cdns_testio)              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ss_0p765v_0p470v_m40c.lib"
set LIB_MACRO(ffgnp_0p935v_125c_cbest_CCbest_T,cdns_testio)                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ff_0p935v_0p570v_125c.lib"
set LIB_MACRO(ffgnp_0p935v_m40c_cbest_CCbest_T,cdns_testio)                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ff_0p935v_0p570v_125c.lib"
set LIB_MACRO(tt_0p85v_85c_typical,cdns_testio)                            "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_tt_0p850v_0p500v_85c.lib"
set LIB_MACRO(tt_0p85v_25c_typical,cdns_testio)                            "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_tt_0p850v_0p500v_25c.lib"
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,cdns_testio)              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ss_0p675v_0p470v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,cdns_testio)              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ss_0p675v_0p470v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,cdns_testio)                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ff_0p825v_0p570v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,cdns_testio)                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ff_0p825v_0p570v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,cdns_testio)                            "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_tt_0p750v_0p500v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,cdns_testio)                            "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_tt_0p750v_0p500v_25c.lib"
set LIB_MACRO(ssgnp_0p63v_125c_cworst_CCworst_T,cdns_testio)               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ss_0p630v_0p470v_125c.lib"
set LIB_MACRO(ssgnp_0p63v_m40c_cworst_CCworst_T,cdns_testio)               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ss_0p630v_0p470v_m40c.lib"
set LIB_MACRO(ffgnp_0p77v_125c_cbest_CCbest_T,cdns_testio)                 "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ff_0p770v_0p570v_125c.lib"
set LIB_MACRO(ffgnp_0p77v_m40c_cbest_CCbest_T,cdns_testio)                 "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_ff_0p770v_0p570v_125c.lib"
set LIB_MACRO(tt_0p7v_85c_typical,cdns_testio)                             "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_tt_0p700v_0p500v_85c.lib"
set LIB_MACRO(tt_0p7v_25c_typical,cdns_testio)                             "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_lpddr6_testio_t5g_15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT_r100_v1p2.20251208/lib/cdns_testio_lpddr6_tt_0p700v_0p500v_25c.lib"

set LIB_MACRO(ssgnp_0p765v_125c_cworst_CCworst_T,gpio)                     "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiossgnp0p675v1p08v125c.lib"
set LIB_MACRO(ssgnp_0p765v_m40c_cworst_CCworst_T,gpio)                     "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiossgnp0p675v1p08vm40c.lib"
set LIB_MACRO(ffgnp_0p935v_125c_cbest_CCbest_T,gpio)                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpioffgnp0p825v1p32v125c.lib"
set LIB_MACRO(ffgnp_0p935v_m40c_cbest_CCbest_T,gpio)                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpioffgnp0p825v1p32v125c.lib"
set LIB_MACRO(tt_0p85v_85c_typical,gpio)                                   "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiott0p75v1p2v85c.lib"
set LIB_MACRO(tt_0p85v_25c_typical,gpio)                                   "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiott0p75v1p2v25c.lib"
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,gpio)                     "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiossgnp0p675v1p08v125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,gpio)                     "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiossgnp0p675v1p08vm40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,gpio)                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpioffgnp0p825v1p32v125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,gpio)                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpioffgnp0p825v1p32v125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,gpio)                                   "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiott0p75v1p2v85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,gpio)                                   "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiott0p75v1p2v25c.lib"
set LIB_MACRO(ssgnp_0p63v_125c_cworst_CCworst_T,gpio)                      "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiossgnp0p675v1p08v125c.lib"
set LIB_MACRO(ssgnp_0p63v_m40c_cworst_CCworst_T,gpio)                      "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiossgnp0p675v1p08vm40c.lib"
set LIB_MACRO(ffgnp_0p77v_125c_cbest_CCbest_T,gpio)                        "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpioffgnp0p825v1p32v125c.lib"
set LIB_MACRO(ffgnp_0p77v_m40c_cbest_CCbest_T,gpio)                        "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpioffgnp0p825v1p32v125c.lib"
set LIB_MACRO(tt_0p7v_85c_typical,gpio)                                    "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiott0p75v1p2v85c.lib"
set LIB_MACRO(tt_0p7v_25c_typical,gpio)                                    "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiott0p75v1p2v25c.lib"





###Design LIBs###
###>>>cdns_lp6_x48_ew_phy_as_top<<<###
set LIB_PRECTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p765v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p765v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.func.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p765v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p765v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p935v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p935v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p63v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p63v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p77v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p77v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_as_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_as_top/prlib/cdns_lp6_x48_ew_phy_as_top.scanshift.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##

###>>>cdns_lp6_x48_ew_phy_ds_top<<<###
set LIB_PRECTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p765v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p765v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.func.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p765v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p765v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p935v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p935v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p63v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p63v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p77v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p77v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_ds_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_ds_top/prlib/cdns_lp6_x48_ew_phy_ds_top.scanshift.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##

###>>>cdns_lp6_x48_ew_phy_top<<<###
set LIB_PRECTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p765v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p765v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.func.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p765v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p765v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p935v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p935v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p63v_125c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p63v_m40c_cworst_CCworst_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p77v_125c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p77v_m40c_cbest_CCbest_T,scanshift,cdns_lp6_x48_ew_phy_top) "/projects/TC70_LPDDR6_N5P/output/cdns_lp6_x48_ew_phy_top/prlib/cdns_lp6_x48_ew_phy_top.scanshift.ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##

###>>>cadence_mc_ew_controller<<<###
set LIB_PRECTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,cadence_mc_ew_controller) "/projects/TC70_LPDDR6_N5P/output/cadence_mc_ew_controller/prlib/cadence_mc_ew_controller.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##

###>>>databahn_data_pat_gen<<<###
set LIB_PRECTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p765v_125c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p765v_m40c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p935v_125c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p935v_m40c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
set LIB_POSTCTS(ssgnp_0p63v_125c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p63v_m40c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p77v_125c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p77v_m40c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC70_LPDDR6_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##

##4:OASIS FILES:
###RC CORNERS####
set MCMM(MMMC_RC_CORNERS) {}
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cworst_CCworst_T_125c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/cworst/Tech/cworst_CCworst_T/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcworst_CCworst_T_125c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/rcworst/Tech/rcworst_CCworst_T/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cworst_CCworst_T_m40c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/cworst/Tech/cworst_CCworst_T/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcworst_CCworst_T_m40c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/rcworst/Tech/rcworst_CCworst_T/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cbest_CCbest_125c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/cbest/Tech/cbest_CCbest/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cworst_CCworst_125c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/cworst/Tech/cworst_CCworst/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcbest_CCbest_125c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/rcbest/Tech/rcbest_CCbest/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcworst_CCworst_125c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/rcworst/Tech/rcworst_CCworst/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cbest_CCbest_m40c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/cbest/Tech/cbest_CCbest/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cworst_CCworst_m40c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/cworst/Tech/cworst_CCworst/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcbest_CCbest_m40c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/rcbest/Tech/rcbest_CCbest/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcworst_CCworst_m40c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/rcworst/Tech/rcworst_CCworst/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	typical_25c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/typical/Tech/typical/qrcTechFile \
	25 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	typical_85c \
	/process/tsmcN5/data/g/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/fs_v1d2p4a/typical/Tech/typical/qrcTechFile \
	85 \
	]
###OCV TABLES####
set MCMM(OCV_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_T_setup) {}
set MCMM(OCV_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup) {}
set MCMM(OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup) {}
set MCMM(OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup) {}
set MCMM(OCV_ffgnp_0p935v_125c_cbest_CCbest_T_cbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p935v_125c_cbest_CCbest_T_cworst_CCworst_hold) {}
set MCMM(OCV_ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p935v_125c_cbest_CCbest_T_rcworst_CCworst_hold) {}
set MCMM(OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_cworst_CCworst_hold) {}
set MCMM(OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_rcbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_rcworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_hold) {}
set MCMM(OCV_tt_0p85v_25c_typical_typical_setup) {}
set MCMM(OCV_tt_0p85v_85c_typical_typical_setup) {}
set MCMM(OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup) {}
set MCMM(OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup) {}
set MCMM(OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup) {}
set MCMM(OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup) {}
set MCMM(OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold) {}
set MCMM(OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold) {}
set MCMM(OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold) {}
set MCMM(OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold) {}
set MCMM(OCV_tt_0p75v_25c_typical_typical_setup) {}
set MCMM(OCV_tt_0p75v_85c_typical_typical_setup) {}
set MCMM(OCV_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_T_setup) {}
set MCMM(OCV_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup) {}
set MCMM(OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup) {}
set MCMM(OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup) {}
set MCMM(OCV_ffgnp_0p77v_125c_cbest_CCbest_T_cbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p77v_125c_cbest_CCbest_T_cworst_CCworst_hold) {}
set MCMM(OCV_ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p77v_125c_cbest_CCbest_T_rcworst_CCworst_hold) {}
set MCMM(OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_cworst_CCworst_hold) {}
set MCMM(OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_rcbest_CCbest_hold) {}
set MCMM(OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_rcworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_hold) {}
set MCMM(OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_hold) {}
set MCMM(OCV_tt_0p7v_25c_typical_typical_setup) {}
set MCMM(OCV_tt_0p7v_85c_typical_typical_setup) {}
###SOCV SETS####
set MCMM(MMMC_SOCV_SETS) {}
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p765v_125c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p765v_m40c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p765v_125c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p765v_m40c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_tt_0p85v_25c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p85v_0p85v_25c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_tt_0p85v_85c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p85v_0p85v_85c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_tt_0p75v_25c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p75v_25c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_tt_0p75v_85c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p75v_85c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p63v_125c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p63v_m40c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p63v_125c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p63v_m40c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_tt_0p7v_25c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p7v_0p75v_25c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_tt_0p7v_85c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p7v_0p75v_85c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p935v_0p935v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p765v_0p765v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_tt_0p85v_25c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p85v_0p85v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p85v_0p85v_25c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_tt_0p85v_85c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p85v_0p85v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p85v_0p85v_85c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_tt_0p75v_25c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p75v_25c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_tt_0p75v_85c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p75v_85c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllffgnp_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p825v_0p77v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllffgnp_0p77v_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtllssgnp_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p675v_0p63v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtllssgnp_0p63v_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_tt_0p7v_25c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p7v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p7v_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p7v_0p75v_25c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scanshift_tt_0p7v_85c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_elvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_lvtlltt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_svttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvttt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_pm_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_pm_ulvtlltt_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p75v_0p7v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_elvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_elvttt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvttt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_lvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_lvtlltt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_svt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_svttt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvt_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvttt_0p7v_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_lvl_ulvtll_120c/spm/socv/tcbn05_bwph210l6p51cnod_lvl_ulvtlltt_0p7v_0p75v_85c_typical_sp.socv \
	]
###Delay Corners####

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner0) OCV_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner0) [list \
		func_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_T_setup \
		func_ssgnp_0p765v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_125c_cworst_CCworst_T \
		cworst_CCworst_T_125c \
		1.0 \
		0.765 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner1) OCV_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner1) [list \
		func_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		func_ssgnp_0p765v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_125c_cworst_CCworst_T \
		rcworst_CCworst_T_125c \
		1.0 \
		0.765 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner2) OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner2) [list \
		func_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup \
		func_ssgnp_0p765v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_m40c_cworst_CCworst_T \
		cworst_CCworst_T_m40c \
		1.0 \
		0.765 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner3) OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner3) [list \
		func_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		func_ssgnp_0p765v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_m40c_cworst_CCworst_T \
		rcworst_CCworst_T_m40c \
		1.0 \
		0.765 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner4) OCV_ffgnp_0p935v_125c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner4) [list \
		func_ffgnp_0p935v_125c_cbest_CCbest_T_cbest_CCbest_hold \
		func_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_125c_cbest_CCbest_T \
		cbest_CCbest_125c \
		1.0 \
		0.935 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner5) OCV_ffgnp_0p935v_125c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner5) [list \
		func_ffgnp_0p935v_125c_cbest_CCbest_T_cworst_CCworst_hold \
		func_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_125c_cbest_CCbest_T \
		cworst_CCworst_125c \
		1.0 \
		0.935 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner6) OCV_ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner6) [list \
		func_ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold \
		func_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_125c_cbest_CCbest_T \
		rcbest_CCbest_125c \
		1.0 \
		0.935 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner7) OCV_ffgnp_0p935v_125c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner7) [list \
		func_ffgnp_0p935v_125c_cbest_CCbest_T_rcworst_CCworst_hold \
		func_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_125c_cbest_CCbest_T \
		rcworst_CCworst_125c \
		1.0 \
		0.935 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner8) OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner8) [list \
		func_ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold \
		func_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_m40c_cbest_CCbest_T \
		cbest_CCbest_m40c \
		1.0 \
		0.935 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner9) OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner9) [list \
		func_ffgnp_0p935v_m40c_cbest_CCbest_T_cworst_CCworst_hold \
		func_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_m40c_cbest_CCbest_T \
		cworst_CCworst_m40c \
		1.0 \
		0.935 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner10) OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner10) [list \
		func_ffgnp_0p935v_m40c_cbest_CCbest_T_rcbest_CCbest_hold \
		func_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_m40c_cbest_CCbest_T \
		rcbest_CCbest_m40c \
		1.0 \
		0.935 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner11) OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner11) [list \
		func_ffgnp_0p935v_m40c_cbest_CCbest_T_rcworst_CCworst_hold \
		func_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_m40c_cbest_CCbest_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.935 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner12) OCV_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner12) [list \
		func_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_hold \
		func_ssgnp_0p765v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_125c_cworst_CCworst_T \
		cworst_CCworst_125c \
		1.0 \
		0.765 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner13) OCV_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner13) [list \
		func_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_hold \
		func_ssgnp_0p765v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_125c_cworst_CCworst_T \
		rcworst_CCworst_125c \
		1.0 \
		0.765 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner14) OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner14) [list \
		func_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_hold \
		func_ssgnp_0p765v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_m40c_cworst_CCworst_T \
		cworst_CCworst_m40c \
		1.0 \
		0.765 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner15) OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner15) [list \
		func_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_hold \
		func_ssgnp_0p765v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_m40c_cworst_CCworst_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.765 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner16) OCV_tt_0p85v_25c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner16) [list \
		func_tt_0p85v_25c_typical_typical_setup \
		func_tt_0p85v_25c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p85v_25c_typical_ccs \
		tt_0p85v_25c_typical \
		typical_25c \
		1.0 \
		0.85 \
		25 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner17) OCV_tt_0p85v_85c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner17) [list \
		func_tt_0p85v_85c_typical_typical_setup \
		func_tt_0p85v_85c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p85v_85c_typical_ccs \
		tt_0p85v_85c_typical \
		typical_85c \
		1.0 \
		0.85 \
		85 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner18) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner18) [list \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner19) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner19) [list \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner20) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner20) [list \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner21) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner21) [list \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner22) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner22) [list \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner23) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner23) [list \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner24) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner24) [list \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner25) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner25) [list \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner26) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner26) [list \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner27) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner27) [list \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner28) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner28) [list \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner29) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner29) [list \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner30) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner30) [list \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner31) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner31) [list \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner32) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner32) [list \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner33) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner33) [list \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner34) OCV_tt_0p75v_25c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner34) [list \
		func_tt_0p75v_25c_typical_typical_setup \
		func_tt_0p75v_25c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_ccs \
		tt_0p75v_25c_typical \
		typical_25c \
		1.0 \
		0.75 \
		25 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner35) OCV_tt_0p75v_85c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner35) [list \
		func_tt_0p75v_85c_typical_typical_setup \
		func_tt_0p75v_85c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_ccs \
		tt_0p75v_85c_typical \
		typical_85c \
		1.0 \
		0.75 \
		85 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner36) OCV_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner36) [list \
		func_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_T_setup \
		func_ssgnp_0p63v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_125c_cworst_CCworst_T \
		cworst_CCworst_T_125c \
		1.0 \
		0.63 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner37) OCV_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner37) [list \
		func_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		func_ssgnp_0p63v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_125c_cworst_CCworst_T \
		rcworst_CCworst_T_125c \
		1.0 \
		0.63 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner38) OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner38) [list \
		func_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup \
		func_ssgnp_0p63v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_m40c_cworst_CCworst_T \
		cworst_CCworst_T_m40c \
		1.0 \
		0.63 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner39) OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner39) [list \
		func_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		func_ssgnp_0p63v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_m40c_cworst_CCworst_T \
		rcworst_CCworst_T_m40c \
		1.0 \
		0.63 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner40) OCV_ffgnp_0p77v_125c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner40) [list \
		func_ffgnp_0p77v_125c_cbest_CCbest_T_cbest_CCbest_hold \
		func_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_125c_cbest_CCbest_T \
		cbest_CCbest_125c \
		1.0 \
		0.77 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner41) OCV_ffgnp_0p77v_125c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner41) [list \
		func_ffgnp_0p77v_125c_cbest_CCbest_T_cworst_CCworst_hold \
		func_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_125c_cbest_CCbest_T \
		cworst_CCworst_125c \
		1.0 \
		0.77 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner42) OCV_ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner42) [list \
		func_ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold \
		func_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_125c_cbest_CCbest_T \
		rcbest_CCbest_125c \
		1.0 \
		0.77 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner43) OCV_ffgnp_0p77v_125c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner43) [list \
		func_ffgnp_0p77v_125c_cbest_CCbest_T_rcworst_CCworst_hold \
		func_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_125c_cbest_CCbest_T \
		rcworst_CCworst_125c \
		1.0 \
		0.77 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner44) OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner44) [list \
		func_ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold \
		func_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_m40c_cbest_CCbest_T \
		cbest_CCbest_m40c \
		1.0 \
		0.77 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner45) OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner45) [list \
		func_ffgnp_0p77v_m40c_cbest_CCbest_T_cworst_CCworst_hold \
		func_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_m40c_cbest_CCbest_T \
		cworst_CCworst_m40c \
		1.0 \
		0.77 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner46) OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner46) [list \
		func_ffgnp_0p77v_m40c_cbest_CCbest_T_rcbest_CCbest_hold \
		func_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_m40c_cbest_CCbest_T \
		rcbest_CCbest_m40c \
		1.0 \
		0.77 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner47) OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner47) [list \
		func_ffgnp_0p77v_m40c_cbest_CCbest_T_rcworst_CCworst_hold \
		func_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_m40c_cbest_CCbest_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.77 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner48) OCV_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner48) [list \
		func_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_hold \
		func_ssgnp_0p63v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_125c_cworst_CCworst_T \
		cworst_CCworst_125c \
		1.0 \
		0.63 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner49) OCV_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner49) [list \
		func_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_hold \
		func_ssgnp_0p63v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_125c_cworst_CCworst_T \
		rcworst_CCworst_125c \
		1.0 \
		0.63 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner50) OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner50) [list \
		func_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_hold \
		func_ssgnp_0p63v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_m40c_cworst_CCworst_T \
		cworst_CCworst_m40c \
		1.0 \
		0.63 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner51) OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner51) [list \
		func_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_hold \
		func_ssgnp_0p63v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_m40c_cworst_CCworst_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.63 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner52) OCV_tt_0p7v_25c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner52) [list \
		func_tt_0p7v_25c_typical_typical_setup \
		func_tt_0p7v_25c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p7v_25c_typical_ccs \
		tt_0p7v_25c_typical \
		typical_25c \
		1.0 \
		0.7 \
		25 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner53) OCV_tt_0p7v_85c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner53) [list \
		func_tt_0p7v_85c_typical_typical_setup \
		func_tt_0p7v_85c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p7v_85c_typical_ccs \
		tt_0p7v_85c_typical \
		typical_85c \
		1.0 \
		0.7 \
		85 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner54) OCV_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner54) [list \
		scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_T_setup \
		scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_125c_cworst_CCworst_T \
		cworst_CCworst_T_125c \
		1.0 \
		0.765 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner55) OCV_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner55) [list \
		scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_125c_cworst_CCworst_T \
		rcworst_CCworst_T_125c \
		1.0 \
		0.765 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner56) OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner56) [list \
		scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup \
		scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_m40c_cworst_CCworst_T \
		cworst_CCworst_T_m40c \
		1.0 \
		0.765 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner57) OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner57) [list \
		scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_m40c_cworst_CCworst_T \
		rcworst_CCworst_T_m40c \
		1.0 \
		0.765 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner58) OCV_ffgnp_0p935v_125c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner58) [list \
		scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_cbest_CCbest_hold \
		scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_125c_cbest_CCbest_T \
		cbest_CCbest_125c \
		1.0 \
		0.935 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner59) OCV_ffgnp_0p935v_125c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner59) [list \
		scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_cworst_CCworst_hold \
		scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_125c_cbest_CCbest_T \
		cworst_CCworst_125c \
		1.0 \
		0.935 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner60) OCV_ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner60) [list \
		scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_rcbest_CCbest_hold \
		scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_125c_cbest_CCbest_T \
		rcbest_CCbest_125c \
		1.0 \
		0.935 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner61) OCV_ffgnp_0p935v_125c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner61) [list \
		scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_rcworst_CCworst_hold \
		scanshift_ffgnp_0p935v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_125c_cbest_CCbest_T \
		rcworst_CCworst_125c \
		1.0 \
		0.935 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner62) OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner62) [list \
		scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_cbest_CCbest_hold \
		scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_m40c_cbest_CCbest_T \
		cbest_CCbest_m40c \
		1.0 \
		0.935 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner63) OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner63) [list \
		scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_cworst_CCworst_hold \
		scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_m40c_cbest_CCbest_T \
		cworst_CCworst_m40c \
		1.0 \
		0.935 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner64) OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner64) [list \
		scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_rcbest_CCbest_hold \
		scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_m40c_cbest_CCbest_T \
		rcbest_CCbest_m40c \
		1.0 \
		0.935 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner65) OCV_ffgnp_0p935v_m40c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner65) [list \
		scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_rcworst_CCworst_hold \
		scanshift_ffgnp_0p935v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p935v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p935v_m40c_cbest_CCbest_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.935 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner66) OCV_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner66) [list \
		scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_cworst_CCworst_hold \
		scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_125c_cworst_CCworst_T \
		cworst_CCworst_125c \
		1.0 \
		0.765 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner67) OCV_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner67) [list \
		scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_rcworst_CCworst_hold \
		scanshift_ssgnp_0p765v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_125c_cworst_CCworst_T \
		rcworst_CCworst_125c \
		1.0 \
		0.765 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner68) OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner68) [list \
		scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_cworst_CCworst_hold \
		scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_m40c_cworst_CCworst_T \
		cworst_CCworst_m40c \
		1.0 \
		0.765 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner69) OCV_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner69) [list \
		scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_rcworst_CCworst_hold \
		scanshift_ssgnp_0p765v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p765v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p765v_m40c_cworst_CCworst_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.765 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner70) OCV_tt_0p85v_25c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner70) [list \
		scanshift_tt_0p85v_25c_typical_typical_setup \
		scanshift_tt_0p85v_25c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p85v_25c_typical_ccs \
		tt_0p85v_25c_typical \
		typical_25c \
		1.0 \
		0.85 \
		25 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner71) OCV_tt_0p85v_85c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner71) [list \
		scanshift_tt_0p85v_85c_typical_typical_setup \
		scanshift_tt_0p85v_85c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p85v_85c_typical_ccs \
		tt_0p85v_85c_typical \
		typical_85c \
		1.0 \
		0.85 \
		85 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner72) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner72) [list \
		scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup \
		scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner73) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner73) [list \
		scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner74) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner74) [list \
		scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup \
		scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner75) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner75) [list \
		scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner76) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner76) [list \
		scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold \
		scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner77) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner77) [list \
		scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold \
		scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner78) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner78) [list \
		scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold \
		scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner79) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner79) [list \
		scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold \
		scanshift_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner80) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner80) [list \
		scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold \
		scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner81) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner81) [list \
		scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold \
		scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner82) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner82) [list \
		scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold \
		scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner83) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner83) [list \
		scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold \
		scanshift_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner84) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner84) [list \
		scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold \
		scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner85) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner85) [list \
		scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold \
		scanshift_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner86) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner86) [list \
		scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold \
		scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner87) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner87) [list \
		scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold \
		scanshift_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner88) OCV_tt_0p75v_25c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner88) [list \
		scanshift_tt_0p75v_25c_typical_typical_setup \
		scanshift_tt_0p75v_25c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_ccs \
		tt_0p75v_25c_typical \
		typical_25c \
		1.0 \
		0.75 \
		25 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner89) OCV_tt_0p75v_85c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner89) [list \
		scanshift_tt_0p75v_85c_typical_typical_setup \
		scanshift_tt_0p75v_85c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_ccs \
		tt_0p75v_85c_typical \
		typical_85c \
		1.0 \
		0.75 \
		85 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner90) OCV_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner90) [list \
		scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_T_setup \
		scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_125c_cworst_CCworst_T \
		cworst_CCworst_T_125c \
		1.0 \
		0.63 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner91) OCV_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner91) [list \
		scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_125c_cworst_CCworst_T \
		rcworst_CCworst_T_125c \
		1.0 \
		0.63 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner92) OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner92) [list \
		scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup \
		scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_m40c_cworst_CCworst_T \
		cworst_CCworst_T_m40c \
		1.0 \
		0.63 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner93) OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner93) [list \
		scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_m40c_cworst_CCworst_T \
		rcworst_CCworst_T_m40c \
		1.0 \
		0.63 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner94) OCV_ffgnp_0p77v_125c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner94) [list \
		scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_cbest_CCbest_hold \
		scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_125c_cbest_CCbest_T \
		cbest_CCbest_125c \
		1.0 \
		0.77 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner95) OCV_ffgnp_0p77v_125c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner95) [list \
		scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_cworst_CCworst_hold \
		scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_125c_cbest_CCbest_T \
		cworst_CCworst_125c \
		1.0 \
		0.77 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner96) OCV_ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner96) [list \
		scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_rcbest_CCbest_hold \
		scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_125c_cbest_CCbest_T \
		rcbest_CCbest_125c \
		1.0 \
		0.77 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner97) OCV_ffgnp_0p77v_125c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner97) [list \
		scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_rcworst_CCworst_hold \
		scanshift_ffgnp_0p77v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_125c_cbest_CCbest_T \
		rcworst_CCworst_125c \
		1.0 \
		0.77 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner98) OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner98) [list \
		scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_cbest_CCbest_hold \
		scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_m40c_cbest_CCbest_T \
		cbest_CCbest_m40c \
		1.0 \
		0.77 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner99) OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner99) [list \
		scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_cworst_CCworst_hold \
		scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_m40c_cbest_CCbest_T \
		cworst_CCworst_m40c \
		1.0 \
		0.77 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner100) OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner100) [list \
		scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_rcbest_CCbest_hold \
		scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_m40c_cbest_CCbest_T \
		rcbest_CCbest_m40c \
		1.0 \
		0.77 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner101) OCV_ffgnp_0p77v_m40c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner101) [list \
		scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_rcworst_CCworst_hold \
		scanshift_ffgnp_0p77v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p77v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p77v_m40c_cbest_CCbest_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.77 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner102) OCV_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner102) [list \
		scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_cworst_CCworst_hold \
		scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_125c_cworst_CCworst_T \
		cworst_CCworst_125c \
		1.0 \
		0.63 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner103) OCV_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner103) [list \
		scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_rcworst_CCworst_hold \
		scanshift_ssgnp_0p63v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_125c_cworst_CCworst_T \
		rcworst_CCworst_125c \
		1.0 \
		0.63 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner104) OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner104) [list \
		scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_cworst_CCworst_hold \
		scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_m40c_cworst_CCworst_T \
		cworst_CCworst_m40c \
		1.0 \
		0.63 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner105) OCV_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner105) [list \
		scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_rcworst_CCworst_hold \
		scanshift_ssgnp_0p63v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p63v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p63v_m40c_cworst_CCworst_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.63 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner106) OCV_tt_0p7v_25c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner106) [list \
		scanshift_tt_0p7v_25c_typical_typical_setup \
		scanshift_tt_0p7v_25c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p7v_25c_typical_ccs \
		tt_0p7v_25c_typical \
		typical_25c \
		1.0 \
		0.7 \
		25 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner107) OCV_tt_0p7v_85c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner107) [list \
		scanshift_tt_0p7v_85c_typical_typical_setup \
		scanshift_tt_0p7v_85c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p7v_85c_typical_ccs \
		tt_0p7v_85c_typical \
		typical_85c \
		1.0 \
		0.7 \
		85 \
		]
