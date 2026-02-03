###TOOL VARS###
set INNOVUS(MODULE_CMD)                                                    "module unload innovus genus ext quantus pegasus pvs;module load innovus/221/22.11-s119_1 genus/221/22.11-e068_1 quantus/211/21.11.012-s732 pegasus/232/23.25.008-e831"
set INNOVUS(QUEUE)                                                         "pd -R \"select\[(OSREL==EE70)||(OSREL==EE80)\]\""
set INNOVUS(EXEC_CMD)                                                      "innovus -64"
set INNOVUS(UI)                                                            legacy
set INNOVUS(DONT_USE)                                                      /projects/workbench/versions/current/workbench/process/tsmc5/innovus_options_paste/dont_use.tsmcN5.paste
set INNOVUS(INCR_SETUP)                                                    /projects/TC73_DDR5_12800_N5P/common_scripts/FLOW/INNOVUS_tsmc5_setup.local.paste
set INNOVUS(POWER_OPT_VIEW)                                                func_func_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
set INNOVUS(POWER_EFFORT)                                                  high
set INNOVUS(OCV_PORT_FROM_STA)                                             /projects/TC73_DDR5_12800_N5P/setup/yaml/MMMC_OCV_setting_extract_from_STA.innovus.tcl

set QRC(MODULE_CMD)                                                        "module unload quantus ext; module load quantus/211/21.11.012-s732"
set QRC(EXEC_CMD)                                                          "qrc -64"
set QRC(QUEUE)                                                             pd
set QRC(CPU)                                                               4
set QRC(TECHLIBFILE)                                                       /projects/TC73_DDR5_12800_N5P/libs/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT.technology_library_file
set QRC(MAXFILESIZE)                                                       20000000000
set QRC(MFILLTYPE)                                                         floating
set QRC(RCFORMAT)                                                          extended
set QRC(LAYERMAP)                                                          "{PO none} {PW none} {NW none} {OD none} {M0 M0} {M1 M1} {M2 M2} {M3 M3} {M4 M4} {M5 M5} {M6 M6} {M7 M7} {M8 M8} {M9 M9} {M10 M10} {M11 M11} {M12 M12} {M13 M13} {M14 M14} {M15 M15} {M16 M16} {AP AP} {BPC BPC} {MPC MPC} {TPC TPC} {VIA0 VIA0} {VIA1 VIA1} {VIA2 VIA2} {VIA3 VIA3} {VIA4 VIA4} {VIA5 VIA5} {VIA6 VIA6} {VIA7 VIA7} {VIA8 VIA8} {VIA9 VIA9} {VIA10 VIA10} {VIA11 VIA11} {VIA12 VIA12} {VIA13 VIA13} {VIA14 VIA14} {VIA15 VIA15} {RV RV}"
set QRC(GDS_LAYER_MAP)                                                     "{{PO 17}} {{OD 6}} {{M0 330}} {{M1 331}} {{M2 332}} {{M3 333}} {{M4 334}} {{M5 335}} {{M6 336}} {{M7 337}} {{M8 338}} {{M9 339}} {{M10 340}} {{M11 341}} {{M12 342}} {{M13 343}} {{M14 344}} {{M15 345}} {{M16 346}} {{AP 74}} {{BPC 262}} {{MPC 261}} {{TPC 260}} {{VIA0 350}} {{VIA1 351}} {{VIA2 352}} {{VIA3 353}} {{VIA4 354}} {{VIA5 355}} {{VIA6 356}} {{VIA7 357}} {{VIA8 358}} {{VIA9 359}} {{VIA10 360}}  {{VIA11 361}} {{VIA12 362}} {{VIA13 363}} {{VIA14 364}} {{VIA15 365}} {{RV 85}}"

set PVS(MODULE_CMD)                                                        "module unload pegasus pvs; module load pegasus/232/23.25.008-e831"
set PVS(EXEC_CMD)                                                          pegasus
set PVS(QUEUE)                                                             pd
set PVS(CPU)                                                               8

set PEGASUS(MODULE_CMD)                                                    "module unload pegasus pvs; module load pegasus/232/23.25.008-e831"
set PEGASUS(EXEC_CMD)                                                      pegasus
set PEGASUS(QUEUE)                                                         pd
set PEGASUS(CPU)                                                           8

set TEMPUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/211/21.15.000"
set TEMPUS(EXEC_CMD)                                                       "tempus -64"
set TEMPUS(CPU)                                                            4
set TEMPUS(QUEUE)                                                          pd
set TEMPUS(CON_MODE)                                                       ddr
set TEMPUS(REPORT_NET_DELAYS)                                              yes
set TEMPUS(TOOLS_DIR)                                                      /projects/TC73_DDR5_12800_N5P/input/latest/sta_signoff/tool

set VOLTUS(MODULE_CMD)                                                     "module unload ssv; module load ssv/221/22.17.000"
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
set VOLTUS(ICTEM)                                                          /process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/ictem_v1d2p1a/cln5_1p16m+ut-alrdl_1x1xb1xe1ya1yb6y2yy2r_shdmim.ictem
set VOLTUS(LEFDEF_LAYERMAP)                                                /projects/TC73_DDR5_12800_N5P/libs/map/N5_16M_voltus_lefdef.layermap
set VOLTUS(GDS_LAYERMAP)                                                   /projects/TC73_DDR5_12800_N5P/libs/map/N5_16M_voltus_gds.layermap
set VOLTUS(PG_LIBS_DIR)                                                    /projects/TC73_DDR5_12800_N5P/libs/pgv
set VOLTUS(PG_LIBS_MODES)                                                  "ssgnp_0p675v_125c_cworst_CCworst_T ffgnp_0p825v_125c_cbest_CCbest_T tt_0p75v_85c_typical"

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
set MISC(GDSMAP)                                                           /projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_gdsout_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhvh_2Yy2R_SHDMIM.13a.map
set MISC(QRC_LAYERMAP)                                                     /projects/TC73_DDR5_12800_N5P/libs/map/PRTF_Innovus_N5_qrc_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM.13a.map
set MISC(OUTPUT_FORMAT)                                                    GDS
set MISC(RCTYPE)                                                           coupledRc
set MISC(tQuantusModelFile)                                                /projects/TC73_DDR5_12800_N5P/libs/QRC/N5P_16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_tQuantus_model.bin
set MISC(VT_TYPE)                                                          {CNODSVT CNODLVT CNODULVT CNODELVT CNODLVTLL CNODULVTLL}

##Design config Vars###
set CONFIG(phy_top_wrapper,LEF_TOP_LAYER)                                  18
set CONFIG(phy_top_wrapper,LEF_PG_LAYERS)                                  "18"
set CONFIG(phy_top_wrapper,MAX_ROUTING_LAYER)                              17
set CONFIG(phy_top_wrapper,CPU)                                            16
set CONFIG(phy_top_wrapper,PWR_NET)                                        "VDD"
set CONFIG(phy_top_wrapper,GND_NET)                                        "VSS"
set CONFIG(phy_top_wrapper,SUB_BLOCKS)                                     "cdn_hs_phy_top"
set CONFIG(phy_top_wrapper,SUB_BLOCK_LIB_MODE)                             "func scan bypass"

set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,LEF_TOP_LAYER)                 17
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,LEF_PG_LAYERS)                 "17 16"
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,MAX_ROUTING_LAYER)             15
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,CTS_NDR_RULE)                  ndr_2w2s
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,CTS_TOP_PREFER_TOP_LAYER)      12
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,CTS_TOP_PREFER_BOTTOM_LAYER)   7
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,CTS_TRUNK_PREFER_TOP_LAYER)    12
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,CTS_TRUNK_PREFER_BOTTOM_LAYER) 9
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,CTS_LEAF_PREFER_TOP_LAYER)     8
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,CTS_LEAF_PREFER_BOTTOM_LAYER)  7
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,QUEUE)                         pd
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,CPU)                           16
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,MEM)                           [expr 16  * 1024]
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,PWR_NET)                       "VDD VDDR VDDQ_CK VDDQ VDDQ_CK_SENSE"
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,GND_NET)                       "VSS"
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,MACRO)                         "cdns_dcc cdns_ddr1000"
set CONFIG(CDN_204H_cdn_hs_phy_adrctl_slice,SUB_BLOCK_LIB_MODE)            "func scan bypass"

set CONFIG(CDN_204H_cdn_hs_phy_data_slice,LEF_TOP_LAYER)                   17
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,LEF_PG_LAYERS)                   "17 16"
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,MAX_ROUTING_LAYER)               15
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,CTS_NDR_RULE)                    ndr_2w2s
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,CTS_TOP_PREFER_TOP_LAYER)        12
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,CTS_TOP_PREFER_BOTTOM_LAYER)     7
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,CTS_TRUNK_PREFER_TOP_LAYER)      12
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,CTS_TRUNK_PREFER_BOTTOM_LAYER)   9
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,CTS_LEAF_PREFER_TOP_LAYER)       8
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,CTS_LEAF_PREFER_BOTTOM_LAYER)    7
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,QUEUE)                           pd
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,CPU)                             16
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,MEM)                             [expr 16  * 1024]
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,PWR_NET)                         "VDD VDD_PLL VDDQ VDD_SENSE VDDQ_SENSE"
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,GND_NET)                         "VSS"
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,MACRO)                           "cdns_dcc cdns_ddr1000"
set CONFIG(CDN_204H_cdn_hs_phy_data_slice,SUB_BLOCK_LIB_MODE)              "func scan bypass"

set CONFIG(cdn_hs_phy_top,LEF_TOP_LAYER)                                   18
set CONFIG(cdn_hs_phy_top,LEF_PG_LAYERS)                                   18
set CONFIG(cdn_hs_phy_top,MAX_ROUTING_LAYER)                               15
set CONFIG(cdn_hs_phy_top,CTS_NDR_RULE)                                    ndr_2w2s
set CONFIG(cdn_hs_phy_top,CTS_TOP_PREFER_TOP_LAYER)                        12
set CONFIG(cdn_hs_phy_top,CTS_TOP_PREFER_BOTTOM_LAYER)                     7
set CONFIG(cdn_hs_phy_top,CTS_TRUNK_PREFER_TOP_LAYER)                      12
set CONFIG(cdn_hs_phy_top,CTS_TRUNK_PREFER_BOTTOM_LAYER)                   9
set CONFIG(cdn_hs_phy_top,CTS_LEAF_PREFER_TOP_LAYER)                       8
set CONFIG(cdn_hs_phy_top,CTS_LEAF_PREFER_BOTTOM_LAYER)                    7
set CONFIG(cdn_hs_phy_top,QUEUE)                                           pd
set CONFIG(cdn_hs_phy_top,CPU)                                             16
set CONFIG(cdn_hs_phy_top,MEM)                                             [expr 400  * 1024]
set CONFIG(cdn_hs_phy_top,PWR_NET)                                         "VDD VDDR VDD_PLL_CA VDD_PLL_TOP VDD_PLL_DS0 VDD_PLL_DS1 VDD_PLL_DS2 VDD_PLL_DS3 VDD_PLL_DS4 VDD_PLL_DS5 VDD_PLL_DS6 VDD_PLL_DS7 VDD_PLL_DS8 VDD_PLL_DS9 VDDQ VDDQ_CK VDD_SENSE VDDQ_SENSE VDDQ_CK_SENSE"
set CONFIG(cdn_hs_phy_top,GND_NET)                                         "VSS"
set CONFIG(cdn_hs_phy_top,PWR_BUMP)                                        PAD130PITCH_POWER
set CONFIG(cdn_hs_phy_top,GND_BUMP)                                        PAD130PITCH_GROUND
set CONFIG(cdn_hs_phy_top,VSRC_LAYER)                                      AP
set CONFIG(cdn_hs_phy_top,MACRO)                                           "cdns_ddr1000 cdns_dcc cdns_custom_decap ddr1000_decap bump esd tcd deskew_pll"
set CONFIG(cdn_hs_phy_top,SUB_BLOCKS)                                      "CDN_204H_cdn_hs_phy_adrctl_slice CDN_204H_cdn_hs_phy_data_slice"
set CONFIG(cdn_hs_phy_top,SUB_BLOCK_LIB_MODE)                              "func scan bypass"

set CONFIG(cadence_mc_controller,LEF_TOP_LAYER)                            15
set CONFIG(cadence_mc_controller,LEF_PG_LAYERS)                            "15 14"
set CONFIG(cadence_mc_controller,MAX_ROUTING_LAYER)                        14
set CONFIG(cadence_mc_controller,CTS_NDR_RULE)                             ndr_2w2s
set CONFIG(cadence_mc_controller,CTS_TOP_PREFER_TOP_LAYER)                 12
set CONFIG(cadence_mc_controller,CTS_TOP_PREFER_BOTTOM_LAYER)              7
set CONFIG(cadence_mc_controller,CTS_TRUNK_PREFER_TOP_LAYER)               12
set CONFIG(cadence_mc_controller,CTS_TRUNK_PREFER_BOTTOM_LAYER)            9
set CONFIG(cadence_mc_controller,CTS_LEAF_PREFER_TOP_LAYER)                8
set CONFIG(cadence_mc_controller,CTS_LEAF_PREFER_BOTTOM_LAYER)             7
set CONFIG(cadence_mc_controller,QUEUE)                                    pd
set CONFIG(cadence_mc_controller,CPU)                                      16
set CONFIG(cadence_mc_controller,MEM)                                      [expr 16  * 1024]
set CONFIG(cadence_mc_controller,PWR_NET)                                  "VDD"
set CONFIG(cadence_mc_controller,GND_NET)                                  "VSS"
set CONFIG(cadence_mc_controller,SUB_BLOCK_LIB_MODE)                       "func"

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

set CONFIG(tv_chip,LEF_TOP_LAYER)                                          18
set CONFIG(tv_chip,LEF_PG_LAYERS)                                          "18"
set CONFIG(tv_chip,MAX_ROUTING_LAYER)                                      16
set CONFIG(tv_chip,CTS_NDR_RULE)                                           ndr_2w2s
set CONFIG(tv_chip,CTS_TOP_PREFER_TOP_LAYER)                               12
set CONFIG(tv_chip,CTS_TOP_PREFER_BOTTOM_LAYER)                            7
set CONFIG(tv_chip,CTS_TRUNK_PREFER_TOP_LAYER)                             12
set CONFIG(tv_chip,CTS_TRUNK_PREFER_BOTTOM_LAYER)                          9
set CONFIG(tv_chip,CTS_LEAF_PREFER_TOP_LAYER)                              8
set CONFIG(tv_chip,CTS_LEAF_PREFER_BOTTOM_LAYER)                           7
set CONFIG(tv_chip,QUEUE)                                                  pd
set CONFIG(tv_chip,CPU)                                                    16
set CONFIG(tv_chip,PWR_NET)                                                "VDD VDD_PLL_A0_AS VDD_PLL_A0_DS0 VDD_PLL_A0_DS1 VDD_PLL_A1_AS VDD_PLL_A1_DS0 VDD_PLL_A1_DS1 VDD_SENSE VDDQ VDDQ_SENSE VDDQX VDD2 VDDQ2 VDDQX2 VDDPST VDD_ISO VREF_L VREF_H VDDPLL_TOP VDD_PLL_DSHM VDDHV_PLL_FRAC0 VDDPOST_PLL_FRAC0 VDDREF_PLL_FRAC0 VDDHV_PLL_FRAC1 VDDPOST_PLL_FRAC1 VDDREF_PLL_FRAC1 VDDQ_CK_SENSE"
set CONFIG(tv_chip,GND_NET)                                                "VSS POCCTRL POCCTRLD ESD"
set CONFIG(tv_chip,PWR_BUMP)                                               PAD130PITCH_POWER
set CONFIG(tv_chip,GND_BUMP)                                               PAD130PITCH_GROUND
set CONFIG(tv_chip,VSRC_LAYER)                                             AP
set CONFIG(tv_chip,MACRO)                                                  "cdns_ddr1000 ddr1000_decap deskew_pll fracn_pll cdns_dcc cdns_custom_decap sram gpio esd noise_gen bump tcd"
set CONFIG(tv_chip,SUB_BLOCKS)                                             "cdn_hs_phy_top cadence_mc_controller databahn_data_pat_gen"
set CONFIG(tv_chip,SUB_BLOCK_LIB_MODE)                                     "func bypass"

set ALL_CONFIG_VARS                                                        "PWR_BUMP CPU GND_BUMP MAX_ROUTING_LAYER GND_NET PWR_NET CTS_NDR_RULE CTS_TRUNK_PREFER_BOTTOM_LAYER CTS_TOP_PREFER_BOTTOM_LAYER CTS_TRUNK_PREFER_TOP_LAYER MEM MACRO VSRC_LAYER LEF_TOP_LAYER CTS_TOP_PREFER_TOP_LAYER CTS_LEAF_PREFER_TOP_LAYER SUB_BLOCK_LIB_MODE QUEUE CTS_LEAF_PREFER_BOTTOM_LAYER SUB_BLOCKS LEF_PG_LAYERS"
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
lappend LIBSET_NAMES func_ssgnp_0p675v_125c_cworst_CCworst_T_setup
lappend LIBSET_NAMES func_ssgnp_0p675v_m40c_cworst_CCworst_T_setup
lappend LIBSET_NAMES func_ffgnp_0p825v_125c_cbest_CCbest_T_hold
lappend LIBSET_NAMES func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES func_ssgnp_0p675v_125c_cworst_CCworst_T_hold
lappend LIBSET_NAMES func_ssgnp_0p675v_m40c_cworst_CCworst_T_hold
lappend LIBSET_NAMES func_tt_0p75v_25c_typical_setup
lappend LIBSET_NAMES func_tt_0p75v_85c_typical_setup
lappend LIBSET_NAMES scan_ssgnp_0p675v_125c_cworst_CCworst_T_setup
lappend LIBSET_NAMES scan_ssgnp_0p675v_m40c_cworst_CCworst_T_setup
lappend LIBSET_NAMES scan_ffgnp_0p825v_125c_cbest_CCbest_T_hold
lappend LIBSET_NAMES scan_ffgnp_0p825v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES scan_ssgnp_0p675v_125c_cworst_CCworst_T_hold
lappend LIBSET_NAMES scan_ssgnp_0p675v_m40c_cworst_CCworst_T_hold
lappend LIBSET_NAMES scan_tt_0p75v_25c_typical_setup
lappend LIBSET_NAMES scan_tt_0p75v_85c_typical_setup
lappend LIBSET_NAMES bypass_ssgnp_0p675v_125c_cworst_CCworst_T_setup
lappend LIBSET_NAMES bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_setup
lappend LIBSET_NAMES bypass_ffgnp_0p825v_125c_cbest_CCbest_T_hold
lappend LIBSET_NAMES bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_hold
lappend LIBSET_NAMES bypass_ssgnp_0p675v_125c_cworst_CCworst_T_hold
lappend LIBSET_NAMES bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_hold
lappend LIBSET_NAMES bypass_tt_0p75v_25c_typical_setup
lappend LIBSET_NAMES bypass_tt_0p75v_85c_typical_setup
##>>>LIB FILES<<<###
##0:LEFS FILES:
set LEFS(STD)                                                              "/process/tsmcN5/data/stdcell/n5/TSMC/PRTF_Innovus_5nm_014_Cad_V13a/PRTF/PRTF_Innovus_5nm_014_Cad_V13a/PR_tech/Cadence/LefHeader/Standard/VHV/PRTF_Innovus_N5_16M_1X1Xb1Xe1Ya1Yb6Y2Yy2R_UTRDL_M1P34_M2P35_M3P42_M4P42_M5P76_M6P76_M7P76_M8P76_M9P76_M10P76_M11P76_M12P76_H210_SHDMIM.13a.tlef /projects/TC73_DDR5_12800_N5P/libs/ndr/ndr_10w10s.lef /projects/TC73_DDR5_12800_N5P/libs/ndr/ndr_9w5s.lef /projects/TC73_DDR5_12800_N5P/libs/ndr/ndr_1w2s.lef /projects/TC73_DDR5_12800_N5P/libs/ndr/ndr_2w1s.lef /projects/TC73_DDR5_12800_N5P/libs/ndr/ndr_2w2s_em.lef /projects/TC73_DDR5_12800_N5P/libs/ndr/ndr_2w2s.lef /projects/TC73_DDR5_12800_N5P/libs/ndr/ndr_2w3s_em.lef /projects/TC73_DDR5_12800_N5P/libs/ndr/ndr_2w3s.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lef/tcbn05_bwph210l6p51cnod_base_svt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lef/tcbn05_bwph210l6p51cnod_base_svt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lef/tcbn05_bwph210l6p51cnod_base_lvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lef/tcbn05_bwph210l6p51cnod_base_lvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_lvtll_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_lvtll.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvt.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvtll_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lef/tcbn05_bwph210l6p51cnod_base_ulvtll.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lef/tcbn05_bwph210l6p51cnod_base_elvt_par.lef /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lef/tcbn05_bwph210l6p51cnod_base_elvt.lef"
set LEFS(MACRO,ddr1000_decap)                                              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_custom_decap_cells_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v1p7.20251125/lef/cdns_ddr1000_custom_decap_cells_h.lef"
set LEFS(MACRO,cdns_ddr1000)                                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v2p17.20251126/lef/ddr1000_80bit_h.lef"
set LEFS(MACRO,cdns_dcc)                                                   "/projects/TC73_DDR5_12800_N5P/libs/customcell/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base.antenna.lef"
set LEFS(MACRO,deskew_pll)                                                 "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5HSDESKEWA_2025_07_31_v1p0p0p2p6_BE/lef/PLLTS5HSDESKEWA.lef"
set LEFS(MACRO,fracn_pll)                                                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lef/PLLTS5FFPLAFRACN.lef"
set LEFS(MACRO,cdns_custom_decap)                                          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lef/cdns_ddr_custom_decap_unit_cells.lef"
set LEFS(MACRO,noise_gen)                                                  "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_noisegen_v_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhv_2Yy2R_r100.20251030/lef/cdns_ddr_noisegen_v.antenna.lef"
set LEFS(MACRO,sram)                                                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhocp_120a/LEF/ts1n05mblvta16384x39m16qwbzhocp.lef"
set LEFS(MACRO,gpio)                                                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/lef/mt/16m/16M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_6Y_VHVHVH_2YY2R/lef/tphn05_12gpio_16lm.lef"
set LEFS(MACRO,bump)                                                       "/process/tsmcN5/data/stdcell/n5v/TSMC/tpbn05v_cu_round_bump_100a/lef/fc/fc_bot/APRDL/lef/tpbn05v_cu_round_bump.lef"
set LEFS(MACRO,tcd)                                                        "/process/tsmcN5/data/stdcell/n5/TSMC/N5_DTCD_library_kit_v1d3.1/lef/N5_DTCD_M12/N5_DTCD_v1d2.lef"
set LEFS(MACRO,esd)                                                        "/process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12lup_120a/lef/mt/16m/16M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_6Y_VHVHVH_2YY2R/lef/tpmn05_12lup_16lm.lef /process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12esd_120b/lef/mt/16m/16M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_6Y_VHVHVH_2YY2R/lef/tpmn05_12esd_16lm.lef"
set LEFS(DESIGN,CDN_204H_cdn_hs_phy_adrctl_slice)                          "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlef/CDN_204H_cdn_hs_phy_adrctl_slice.lef"
set LEFS(DESIGN,CDN_204H_cdn_hs_phy_data_slice)                            "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlef/CDN_204H_cdn_hs_phy_data_slice.lef"
set LEFS(DESIGN,cdn_hs_phy_top)                                            "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlef/cdn_hs_phy_top.lef"
set LEFS(DESIGN,cadence_mc_controller)                                     "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/prlef/cadence_mc_controller.lef"
set LEFS(DESIGN,databahn_data_pat_gen)                                     "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlef/databahn_data_pat_gen.lef"

##1:CDLS FILES:
set CDLS(STD)                                                              "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spice/tcbn05_bwph210l6p51cnod_base_elvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spice/tcbn05_bwph210l6p51cnod_base_lvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spice/tcbn05_bwph210l6p51cnod_base_lvtll.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spice/tcbn05_bwph210l6p51cnod_base_svt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spice/tcbn05_bwph210l6p51cnod_base_ulvt.spi /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spice/tcbn05_bwph210l6p51cnod_base_ulvtll.spi"
set CDLS(MACRO,ddr1000_decap)                                              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_custom_decap_cells_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v1p7.20251125/cdl/cdns_ddr1000_custom_decap_cells_h.cdl"
set CDLS(MACRO,cdns_ddr1000)                                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v2p17.20251126/cdl/ddr1000_80bit_h.cdl"
set CDLS(MACRO,cdns_dcc)                                                   "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhvh_2Yy2R_r300.20250625/cdl/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base.cdl"
set CDLS(MACRO,deskew_pll)                                                 "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5HSDESKEWA_2025_07_31_v1p0p0p2p6_BE/netlist/PLLTS5HSDESKEWA.cdl"
set CDLS(MACRO,fracn_pll)                                                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/netlist/PLLTS5FFPLAFRACN.cdl"
set CDLS(MACRO,cdns_custom_decap)                                          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/cdl/cdns_ddr_custom_decap_unit_cells.cdl"
set CDLS(MACRO,noise_gen)                                                  "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_noisegen_v_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhv_2Yy2R_r100.20251030/cdl/cdns_ddr_noisegen_v.cdl"
set CDLS(MACRO,sram)                                                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhocp_120a/SPICE/ts1n05mblvta16384x39m16qwbzhocp.spi"
set CDLS(MACRO,gpio)                                                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/spice/tphn05_12gpio.spi"
set CDLS(MACRO,esd)                                                        "/process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12lup_120a/spice/tpmn05_12lup.spi /process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12esd_120b/spice/tpmn05_12esd.spi"
set CDLS(DESIGN,CDN_204H_cdn_hs_phy_adrctl_slice)                          "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/latest/cdl/CDN_204H_cdn_hs_phy_adrctl_slice.cdl"
set CDLS(DESIGN,CDN_204H_cdn_hs_phy_data_slice)                            "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/latest/cdl/CDN_204H_cdn_hs_phy_data_slice.cdl"
set CDLS(DESIGN,cdn_hs_phy_top)                                            "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/latest/cdl/cdn_hs_phy_top.cdl"
set CDLS(DESIGN,cadence_mc_controller)                                     "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/latest/cdl/cadence_mc_controller.cdl"
set CDLS(DESIGN,databahn_data_pat_gen)                                     "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/latest/cdl/databahn_data_pat_gen.cdl"

##2:GDS FILES:
set GDS(STD)                                                               "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/gds/tcbn05_bwph210l6p51cnod_base_elvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/gds/tcbn05_bwph210l6p51cnod_base_lvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/gds/tcbn05_bwph210l6p51cnod_base_lvtll.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/gds/tcbn05_bwph210l6p51cnod_base_svt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/gds/tcbn05_bwph210l6p51cnod_base_ulvt.gds /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/gds/tcbn05_bwph210l6p51cnod_base_ulvtll.gds"
set GDS(MACRO,ddr1000_decap)                                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_custom_decap_cells_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v1p7.20251125/gds/cdns_ddr1000_custom_decap_cells_h.gds.gz"
set GDS(MACRO,cdns_ddr1000)                                                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v2p17.20251126/gds/ddr1000_80bit_h.gds.gz"
set GDS(MACRO,cdns_dcc)                                                    "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhvh_2Yy2R_r300.20250625/gds/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base.gds"
set GDS(MACRO,deskew_pll)                                                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5HSDESKEWA_2025_07_31_v1p0p0p2p6_BE/gds/PLLTS5HSDESKEWA.gds"
set GDS(MACRO,fracn_pll)                                                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/gds/PLLTS5FFPLAFRACN.gds"
set GDS(MACRO,cdns_custom_decap)                                           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/gds/cdns_ddr_custom_decap_unit_cells.gds"
set GDS(MACRO,noise_gen)                                                   "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_noisegen_v_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhv_2Yy2R_r100.20251030/gds/cdns_ddr_noisegen_v.gds.gz"
set GDS(MACRO,sram)                                                        "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhocp_120a/GDSII/ts1n05mblvta16384x39m16qwbzhocp.gds"
set GDS(MACRO,gpio)                                                        "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/gds/mt/16m/16M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_6Y_VHVHVH_2YY2R/tphn05_12gpio.gds"
set GDS(MACRO,bump)                                                        "/process/tsmcN5/data/stdcell/n5v/TSMC/tpbn05v_cu_round_bump_100a/gds/fc/fc_bot/APRDL/tpbn05v_cu_round_bump.gds"
set GDS(MACRO,tcd)                                                         "/process/tsmcN5/data/stdcell/n5/TSMC/N5_DTCD_library_kit_v1d3.1/gds/N5P_DTCD_full_stack_general_v0d5_190612.gds"
set GDS(MACRO,esd)                                                         "/process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12lup_120a/gds/mt/16m/16M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_6Y_VHVHVH_2YY2R/tpmn05_12lup.gds /process/tsmcN5/data/stdcell/n5/TSMC/tpmn05_12esd_120b/gds/mt/16m/16M_1X_H_1XB_V_1XE_H_1YA_V_1YB_H_6Y_VHVHVH_2YY2R/tpmn05_12esd.gds"
set GDS(DESIGN,CDN_204H_cdn_hs_phy_adrctl_slice)                           "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/latest/gds/CDN_204H_cdn_hs_phy_adrctl_slice.nomerged.gds.gz"
set GDS(DESIGN,CDN_204H_cdn_hs_phy_data_slice)                             "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/latest/gds/CDN_204H_cdn_hs_phy_data_slice.nomerged.gds.gz"
set GDS(DESIGN,cdn_hs_phy_top)                                             "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/latest/gds/cdn_hs_phy_top.uniquify.gds.gz"
set GDS(DESIGN,cadence_mc_controller)                                      "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/latest/gds/cadence_mc_controller.nomerged.gds.gz"
set GDS(DESIGN,databahn_data_pat_gen)                                      "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/latest/gds/databahn_data_pat_gen.nomerged.gds.gz"

##3:LIB FILES:

###STD LIBs###
set LIB_STD(ssgnp_0p675v_125c_cworst_CCworst_T)                            "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz"
set LIB_STD(ssgnp_0p675v_m40c_cworst_CCworst_T)                            "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_hm_lvf_p_ccs.lib.gz"
set LIB_STD(ffgnp_0p825v_125c_cbest_CCbest_T)                              "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz"
set LIB_STD(ffgnp_0p825v_m40c_cbest_CCbest_T)                              "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_hm_lvf_p_ccs.lib.gz"
set LIB_STD(tt_0p75v_85c_typical)                                          "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_85c_typical_hm_lvf_p_ccs.lib.gz"
set LIB_STD(tt_0p75v_25c_typical)                                          "/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz \
                                                                            /process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/lvf/ccs/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_25c_typical_hm_lvf_p_ccs.lib.gz"
###MACRO LIBs###
set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,ddr1000_decap)            "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_custom_decap_cells_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v1p7.20251125/lib/cdns_ddr_custom_decap_cells_ddr5_ss_0p675v_1p060v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,ddr1000_decap)            "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_custom_decap_cells_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v1p7.20251125/lib/cdns_ddr_custom_decap_cells_ddr5_ss_0p675v_1p060v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,ddr1000_decap)              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_custom_decap_cells_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v1p7.20251125/lib/cdns_ddr_custom_decap_cells_ddr5_ff_0p825v_1p170v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,ddr1000_decap)              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_custom_decap_cells_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v1p7.20251125/lib/cdns_ddr_custom_decap_cells_ddr5_ff_0p825v_1p170v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,ddr1000_decap)                          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_custom_decap_cells_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v1p7.20251125/lib/cdns_ddr_custom_decap_cells_ddr5_tt_0p750v_1p100v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,ddr1000_decap)                          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_custom_decap_cells_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v1p7.20251125/lib/cdns_ddr_custom_decap_cells_ddr5_tt_0p750v_1p100v_25c.lib"

set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,cdns_ddr1000)             "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v2p17.20251126/lib/cdns_ddr1000_h_ddr5_ss_0p675v_1p060v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,cdns_ddr1000)             "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v2p17.20251126/lib/cdns_ddr1000_h_ddr5_ss_0p675v_1p060v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,cdns_ddr1000)               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v2p17.20251126/lib/cdns_ddr1000_h_ddr5_ff_0p825v_1p170v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,cdns_ddr1000)               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v2p17.20251126/lib/cdns_ddr1000_h_ddr5_ff_0p825v_1p170v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,cdns_ddr1000)                           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v2p17.20251126/lib/cdns_ddr1000_h_ddr5_tt_0p750v_1p100v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,cdns_ddr1000)                           "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr1000_h_t5g_80b_DR_12p8G_v159d133h212_CuBUMP_16M6Y2Yy2R_r400_v2p17.20251126/lib/cdns_ddr1000_h_ddr5_tt_0p750v_1p100v_25c.lib"

set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,cdns_dcc)                 "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhvh_2Yy2R_r300.20250625/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ssgnp_cworst_CCworst_T_0p675v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,cdns_dcc)                 "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhvh_2Yy2R_r300.20250625/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ssgnp_cworst_CCworst_T_0p675v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,cdns_dcc)                   "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhvh_2Yy2R_r300.20250625/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ffgnp_cbest_CCbest_T_0p825v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,cdns_dcc)                   "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhvh_2Yy2R_r300.20250625/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_ffgnp_cbest_CCbest_T_0p825v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,cdns_dcc)                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhvh_2Yy2R_r300.20250625/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_tt_typical_0p75v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,cdns_dcc)                               "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhvh_2Yy2R_r300.20250625/lib/spectre_v1d2_2p5/lib_dfly/cdns_ddr_custom_dig_cells_tcbn05_bwph210l6p51cnod_base_tt_typical_0p75v_25c.lib"

set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,deskew_pll)               "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5HSDESKEWA_2025_07_31_v1p0p0p2p6_BE/lib/PLLTS5HSDESKEWA_SSGNP_0P675V_125C_cworst_CCworst_T.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,deskew_pll)               "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5HSDESKEWA_2025_07_31_v1p0p0p2p6_BE/lib/PLLTS5HSDESKEWA_SSGNP_0P675V_M40C_cworst_CCworst_T.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,deskew_pll)                 "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5HSDESKEWA_2025_07_31_v1p0p0p2p6_BE/lib/PLLTS5HSDESKEWA_FFGNP_0P825V_125C_cbest_CCbest_T.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,deskew_pll)                 "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5HSDESKEWA_2025_07_31_v1p0p0p2p6_BE/lib/PLLTS5HSDESKEWA_FFGNP_0P825V_125C_cbest_CCbest_T.lib"
set LIB_MACRO(tt_0p75v_85c_typical,deskew_pll)                             "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5HSDESKEWA_2025_07_31_v1p0p0p2p6_BE/lib/PLLTS5HSDESKEWA_TT_0P75V_85C_typical.lib"
set LIB_MACRO(tt_0p75v_25c_typical,deskew_pll)                             "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5HSDESKEWA_2025_07_31_v1p0p0p2p6_BE/lib/PLLTS5HSDESKEWA_TT_0P75V_25C_typical.lib"

set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,fracn_pll)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_SSGNP_0P675V_125C_Cworst_CCworst_T.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,fracn_pll)                "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_SSGNP_0P675V_M40C_Cworst_CCworst_T.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,fracn_pll)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,fracn_pll)                  "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_FFGNP_0P825V_125C_Cbest_CCbest_T.lib"
set LIB_MACRO(tt_0p75v_85c_typical,fracn_pll)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_TT_0P75V_85C_Typical.lib"
set LIB_MACRO(tt_0p75v_25c_typical,fracn_pll)                              "/process/tsmcN5/data/stdcell/n5gp/CDNS/PLLTS5FFPLAFRACN_2023_02_01_v1p3p0p2p6_BE/lib/PLLTS5FFPLAFRACN_TT_0P75V_25C_Typical.lib"

set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,cdns_custom_decap)        "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ss_0p675v_0p47v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,cdns_custom_decap)        "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ss_0p675v_0p47v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,cdns_custom_decap)          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ff_0p825v_0p57v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,cdns_custom_decap)          "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_ff_0p825v_0p57v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,cdns_custom_decap)                      "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_tt_0p75v_0p5v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,cdns_custom_decap)                      "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_custom_decap_unit_cells_t5g_1X1Xb1Xe1Ya1Yb5Y_r100_v1p0.20251030/lib/cdns_ddr_custom_decap_unit_cells_lpddr6_tt_0p75v_0p5v_25c.lib"

set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,noise_gen)                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_noisegen_v_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhv_2Yy2R_r100.20251030/lib/cdns_ddr_noisegen_v_ddr5_ss_0p675v_1p05v_125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,noise_gen)                "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_noisegen_v_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhv_2Yy2R_r100.20251030/lib/cdns_ddr_noisegen_v_ddr5_ss_0p675v_1p05v_m40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,noise_gen)                  "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_noisegen_v_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhv_2Yy2R_r100.20251030/lib/cdns_ddr_noisegen_v_ddr5_ff_0p825v_1p17v_125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,noise_gen)                  "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_noisegen_v_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhv_2Yy2R_r100.20251030/lib/cdns_ddr_noisegen_v_ddr5_ff_0p825v_1p17v_125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,noise_gen)                              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_noisegen_v_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhv_2Yy2R_r100.20251030/lib/cdns_ddr_noisegen_v_ddr5_tt_0p75v_1p1v_85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,noise_gen)                              "/process/tsmcN5/data/stdcell/n5/CDNS/cdns_ddr_noisegen_v_t5g_16M_1X_h_1Xb_v_1Xe_h_1Ya_v_1Yb_h_6Y_vhvhv_2Yy2R_r100.20251030/lib/cdns_ddr_noisegen_v_ddr5_tt_0p75v_1p1v_25c.lib"

set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,sram)                     "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhocp_120a/CCS/ts1n05mblvta16384x39m16qwbzhocp_ssgnp_0p675v_125c_cworst_ccworst_t.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,sram)                     "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhocp_120a/CCS/ts1n05mblvta16384x39m16qwbzhocp_ssgnp_0p675v_m40c_cworst_ccworst_t.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,sram)                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhocp_120a/CCS/ts1n05mblvta16384x39m16qwbzhocp_ffgnp_0p825v_125c_cbest_ccbest.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,sram)                       "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhocp_120a/CCS/ts1n05mblvta16384x39m16qwbzhocp_ffgnp_0p825v_125c_cbest_ccbest.lib"
set LIB_MACRO(tt_0p75v_85c_typical,sram)                                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhocp_120a/CCS/ts1n05mblvta16384x39m16qwbzhocp_tt_0p750v_85c_typical.lib"
set LIB_MACRO(tt_0p75v_25c_typical,sram)                                   "/process/tsmcN5/data/stdcell/n5gp/CDNS/ts1n05mblvta16384x39m16qwbzhocp_120a/CCS/ts1n05mblvta16384x39m16qwbzhocp_tt_0p750v_25c_typical.lib"

set LIB_MACRO(ssgnp_0p675v_125c_cworst_CCworst_T,gpio)                     "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiossgnp0p675v1p08v125c.lib"
set LIB_MACRO(ssgnp_0p675v_m40c_cworst_CCworst_T,gpio)                     "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiossgnp0p675v1p08vm40c.lib"
set LIB_MACRO(ffgnp_0p825v_125c_cbest_CCbest_T,gpio)                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpioffgnp0p825v1p32v125c.lib"
set LIB_MACRO(ffgnp_0p825v_m40c_cbest_CCbest_T,gpio)                       "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpioffgnp0p825v1p32v125c.lib"
set LIB_MACRO(tt_0p75v_85c_typical,gpio)                                   "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiott0p75v1p2v85c.lib"
set LIB_MACRO(tt_0p75v_25c_typical,gpio)                                   "/process/tsmcN5/data/stdcell/n5/TSMC/tphn05_12gpio_120b/nldm/tphn05_12gpiott0p75v1p2v25c.lib"





###Design LIBs###
###>>>CDN_204H_cdn_hs_phy_adrctl_slice<<<###
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,scan,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scan,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,scan,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scan,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,bypass,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.bypass.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,bypass,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.bypass.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,bypass,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.bypass.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,bypass,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.bypass.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,scan,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scan,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,scan,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scan,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,bypass,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.bypass.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,bypass,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.bypass.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,bypass,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.bypass.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,bypass,CDN_204H_cdn_hs_phy_adrctl_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_adrctl_slice/prlib/CDN_204H_cdn_hs_phy_adrctl_slice.bypass.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##

###>>>CDN_204H_cdn_hs_phy_data_slice<<<###
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,scan,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scan,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,scan,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scan,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,bypass,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.bypass.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,bypass,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.bypass.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,bypass,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.bypass.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,bypass,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.bypass.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,scan,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scan,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,scan,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scan,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,bypass,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.bypass.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,bypass,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.bypass.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,bypass,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.bypass.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,bypass,CDN_204H_cdn_hs_phy_data_slice) "/projects/TC73_DDR5_12800_N5P/output/CDN_204H_cdn_hs_phy_data_slice/prlib/CDN_204H_cdn_hs_phy_data_slice.bypass.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##

###>>>cdn_hs_phy_top<<<###
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cdn_hs_phy_top)     "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cdn_hs_phy_top)     "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cdn_hs_phy_top)       "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cdn_hs_phy_top)       "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,scan,cdn_hs_phy_top)     "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scan,cdn_hs_phy_top)     "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,scan,cdn_hs_phy_top)       "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scan,cdn_hs_phy_top)       "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,bypass,cdn_hs_phy_top)   "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.bypass.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,bypass,cdn_hs_phy_top)   "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.bypass.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,bypass,cdn_hs_phy_top)     "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.bypass.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,bypass,cdn_hs_phy_top)     "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.bypass.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cdn_hs_phy_top)    "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cdn_hs_phy_top)    "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cdn_hs_phy_top)      "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cdn_hs_phy_top)      "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,scan,cdn_hs_phy_top)    "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scan,cdn_hs_phy_top)    "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,scan,cdn_hs_phy_top)      "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scan,cdn_hs_phy_top)      "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,bypass,cdn_hs_phy_top)  "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.bypass.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,bypass,cdn_hs_phy_top)  "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.bypass.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,bypass,cdn_hs_phy_top)    "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.bypass.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,bypass,cdn_hs_phy_top)    "/projects/TC73_DDR5_12800_N5P/output/cdn_hs_phy_top/prlib/cdn_hs_phy_top.bypass.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##

###>>>cadence_mc_controller<<<###
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cadence_mc_controller) "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/prlib/cadence_mc_controller.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cadence_mc_controller) "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/prlib/cadence_mc_controller.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cadence_mc_controller) "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/prlib/cadence_mc_controller.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cadence_mc_controller) "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/prlib/cadence_mc_controller.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,cadence_mc_controller) "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/prlib/cadence_mc_controller.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,cadence_mc_controller) "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/prlib/cadence_mc_controller.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,cadence_mc_controller) "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/prlib/cadence_mc_controller.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,cadence_mc_controller) "/projects/TC73_DDR5_12800_N5P/output/cadence_mc_controller/prlib/cadence_mc_controller.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##

###>>>databahn_data_pat_gen<<<###
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_PRECTS(ssgnp_0p675v_125c_cworst_CCworst_T,scan,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ssgnp_0p675v_m40c_cworst_CCworst_T,scan,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.scanshift.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_125c_cbest_CCbest_T,scan,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.scanshift.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.ideal.lib"
set LIB_PRECTS(ffgnp_0p825v_m40c_cbest_CCbest_T,scan,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.scanshift.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.ideal.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ssgnp_0p675v_m40c_cworst_CCworst_T,func,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup.lib"
set LIB_POSTCTS(ffgnp_0p825v_125c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold.lib"
set LIB_POSTCTS(ffgnp_0p825v_m40c_cbest_CCbest_T,func,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.func.ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold.lib"
##
set LIB_POSTCTS(ssgnp_0p675v_125c_cworst_CCworst_T,scan,databahn_data_pat_gen) "/projects/TC73_DDR5_12800_N5P/output/databahn_data_pat_gen/prlib/databahn_data_pat_gen.scanshift.ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup.lib"
##

##4:OASIS FILES:
###RC CORNERS####
set MCMM(MMMC_RC_CORNERS) {}
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cworst_CCworst_T_125c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/cworst/Tech/cworst_CCworst_T/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcworst_CCworst_T_125c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/rcworst/Tech/rcworst_CCworst_T/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cworst_CCworst_T_m40c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/cworst/Tech/cworst_CCworst_T/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcworst_CCworst_T_m40c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/rcworst/Tech/rcworst_CCworst_T/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cbest_CCbest_125c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/cbest/Tech/cbest_CCbest/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cworst_CCworst_125c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/cworst/Tech/cworst_CCworst/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcbest_CCbest_125c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/rcbest/Tech/rcbest_CCbest/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcworst_CCworst_125c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/rcworst/Tech/rcworst_CCworst/qrcTechFile \
	125 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cbest_CCbest_m40c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/cbest/Tech/cbest_CCbest/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	cworst_CCworst_m40c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/cworst/Tech/cworst_CCworst/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcbest_CCbest_m40c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/rcbest/Tech/rcbest_CCbest/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	rcworst_CCworst_m40c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/rcworst/Tech/rcworst_CCworst/qrcTechFile \
	-40 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	typical_25c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/typical/Tech/typical/qrcTechFile \
	25 \
	]
	lappend MCMM(MMMC_RC_CORNERS) [list \
	typical_85c \
	/process/tsmcN5/data/g/QRC/16M1X1Xb1Xe1Ya1Yb6Y2Yy2R_SHDMIM_UT/fs_v1d2p4a/typical/Tech/typical/qrcTechFile \
	85 \
	]
###OCV TABLES####
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
###SOCV SETS####
set MCMM(MMMC_SOCV_SETS) {}
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_tt_0p75v_25c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_25c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list func_tt_0p75v_85c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_85c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scan_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scan_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scan_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scan_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scan_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scan_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scan_tt_0p75v_25c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_25c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list scan_tt_0p75v_85c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_85c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list bypass_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list bypass_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllffgnp_0p825v_125c_cbest_CCbest_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list bypass_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_125c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtllssgnp_0p675v_m40c_cworst_CCworst_T_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list bypass_tt_0p75v_25c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_25c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_25c_typical_sp.socv \
	]
lappend MCMM(MMMC_SOCV_SETS) [list bypass_tt_0p75v_85c_typical_setup \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_elvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_elvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_lvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_lvtlltt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_svt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvt_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvttt_0p75v_85c_typical_sp.socv \
	/process/tsmcN5/data/stdcell/n5/TSMC/tcbn05_bwph210l6p51cnod_base_ulvtll_120b/spm/socv/tcbn05_bwph210l6p51cnod_base_ulvtlltt_0p75v_85c_typical_sp.socv \
	]
###Delay Corners####

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner0) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner0) [list \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner1) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner1) [list \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner2) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner2) [list \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner3) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner3) [list \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner4) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner4) [list \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner5) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner5) [list \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner6) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner6) [list \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner7) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner7) [list \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold \
		func_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner8) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner8) [list \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner9) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner9) [list \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner10) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner10) [list \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner11) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner11) [list \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold \
		func_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner12) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner12) [list \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner13) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner13) [list \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold \
		func_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner14) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner14) [list \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner15) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner15) [list \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold \
		func_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner16) OCV_tt_0p75v_25c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner16) [list \
		func_tt_0p75v_25c_typical_typical_setup \
		func_tt_0p75v_25c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_ccs \
		tt_0p75v_25c_typical \
		typical_25c \
		1.0 \
		0.75 \
		25 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner17) OCV_tt_0p75v_85c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner17) [list \
		func_tt_0p75v_85c_typical_typical_setup \
		func_tt_0p75v_85c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_ccs \
		tt_0p75v_85c_typical \
		typical_85c \
		1.0 \
		0.75 \
		85 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner18) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner18) [list \
		scan_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup \
		scan_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner19) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner19) [list \
		scan_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		scan_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner20) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner20) [list \
		scan_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup \
		scan_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner21) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner21) [list \
		scan_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		scan_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner22) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner22) [list \
		scan_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold \
		scan_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner23) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner23) [list \
		scan_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold \
		scan_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner24) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner24) [list \
		scan_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold \
		scan_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner25) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner25) [list \
		scan_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold \
		scan_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner26) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner26) [list \
		scan_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold \
		scan_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner27) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner27) [list \
		scan_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold \
		scan_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner28) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner28) [list \
		scan_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold \
		scan_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner29) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner29) [list \
		scan_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold \
		scan_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner30) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner30) [list \
		scan_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold \
		scan_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner31) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner31) [list \
		scan_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold \
		scan_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner32) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner32) [list \
		scan_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold \
		scan_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner33) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner33) [list \
		scan_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold \
		scan_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner34) OCV_tt_0p75v_25c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner34) [list \
		scan_tt_0p75v_25c_typical_typical_setup \
		scan_tt_0p75v_25c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_ccs \
		tt_0p75v_25c_typical \
		typical_25c \
		1.0 \
		0.75 \
		25 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner35) OCV_tt_0p75v_85c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner35) [list \
		scan_tt_0p75v_85c_typical_typical_setup \
		scan_tt_0p75v_85c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_ccs \
		tt_0p75v_85c_typical \
		typical_85c \
		1.0 \
		0.75 \
		85 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner36) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner36) [list \
		bypass_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_T_setup \
		bypass_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner37) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner37) [list \
		bypass_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		bypass_ssgnp_0p675v_125c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_T_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner38) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner38) [list \
		bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_T_setup \
		bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner39) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner39) [list \
		bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_T_setup \
		bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_setup \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_T_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner40) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner40) [list \
		bypass_ffgnp_0p825v_125c_cbest_CCbest_T_cbest_CCbest_hold \
		bypass_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner41) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner41) [list \
		bypass_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold \
		bypass_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		cworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner42) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner42) [list \
		bypass_ffgnp_0p825v_125c_cbest_CCbest_T_rcbest_CCbest_hold \
		bypass_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcbest_CCbest_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner43) OCV_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner43) [list \
		bypass_ffgnp_0p825v_125c_cbest_CCbest_T_rcworst_CCworst_hold \
		bypass_ffgnp_0p825v_125c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_125c_cbest_CCbest_T \
		rcworst_CCworst_125c \
		1.0 \
		0.825 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner44) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner44) [list \
		bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_cbest_CCbest_hold \
		bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner45) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner45) [list \
		bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_cworst_CCworst_hold \
		bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		cworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner46) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner46) [list \
		bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_rcbest_CCbest_hold \
		bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcbest_CCbest_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner47) OCV_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner47) [list \
		bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_rcworst_CCworst_hold \
		bypass_ffgnp_0p825v_m40c_cbest_CCbest_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtffgnp_0p825v_125c_cbest_CCbest_T_ccs \
		ffgnp_0p825v_m40c_cbest_CCbest_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.825 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner48) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner48) [list \
		bypass_ssgnp_0p675v_125c_cworst_CCworst_T_cworst_CCworst_hold \
		bypass_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		cworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner49) OCV_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner49) [list \
		bypass_ssgnp_0p675v_125c_cworst_CCworst_T_rcworst_CCworst_hold \
		bypass_ssgnp_0p675v_125c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_125c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_125c_cworst_CCworst_T \
		rcworst_CCworst_125c \
		1.0 \
		0.675 \
		125 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner50) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner50) [list \
		bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_cworst_CCworst_hold \
		bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		cworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner51) OCV_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner51) [list \
		bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_rcworst_CCworst_hold \
		bypass_ssgnp_0p675v_m40c_cworst_CCworst_T_hold \
		tcbn05_bwph210l6p51cnod_base_svtssgnp_0p675v_m40c_cworst_CCworst_T_ccs \
		ssgnp_0p675v_m40c_cworst_CCworst_T \
		rcworst_CCworst_m40c \
		1.0 \
		0.675 \
		-40 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner52) OCV_tt_0p75v_25c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner52) [list \
		bypass_tt_0p75v_25c_typical_typical_setup \
		bypass_tt_0p75v_25c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_25c_typical_ccs \
		tt_0p75v_25c_typical \
		typical_25c \
		1.0 \
		0.75 \
		25 \
		]

	set MMMC_DELAY_CORNER_OCV(tmpDelayCorner53) OCV_tt_0p75v_85c_typical_typical_setup
	set MMMC_DELAY_CORNERS_LIST(tmpDelayCorner53) [list \
		bypass_tt_0p75v_85c_typical_typical_setup \
		bypass_tt_0p75v_85c_typical_setup \
		tcbn05_bwph210l6p51cnod_base_svttt_0p75v_85c_typical_ccs \
		tt_0p75v_85c_typical \
		typical_85c \
		1.0 \
		0.75 \
		85 \
		]
