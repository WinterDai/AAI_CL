source $env(WB_ROOT)/kits/setup/Yaml/setup_vars.tcl 
source $env(WB_ROOT)/kits/setup/setup_common.tcl

###Below is incremental setting in addtion to the setup_common.tcl setting.
namespace eval innovus {}
namespace eval qrc {}
namespace eval voltus {
    ##For DFPHY or GDDRPHY, AMS_PG_DEF (eg. IO def or RDL def) may be provided by AMS team and need to read to EMIR flow,
    ##Below setting is for reference.please change that based on real name accordingly.
    switch -regexp -- $env(WB_DESIGN) {
         cdns_lp5x_x32_ns_phy_top {set  AMS_PG_DEF AMS_PG_DEF_NAME;}
    }
    ##PHY_TYPE (options: HSPHY/HPPHY/DFPHY/GDDRPHY) to control the diemodel generation flow
    set PHY_TYPE "HPPHY"
}
namespace eval tempus {}
namespace eval ddr {}
namespace eval pvs {
    switch -regexp -- $env(WB_DESIGN) {
        cdn_hs_phy_top                {set CPU 48;  set EXEC_CMD "pegasus -c $env(WB_ROOT)/kits/setup/resource.drc.cfg"}
        cdn_hs_phy_data_slice         {set CPU 32;  set EXEC_CMD "pegasus " }
        default                       {set CPU 16;  set EXEC_CMD "pegasus " }
    }
}
namespace eval fv {
    set VSTUBS       {}
    set VSTUBSLVF    {}
    set VSTUBSLVF   [lrange [lindex $innovus::MMMC_LIB_SETS 0] 1 end]
   
    ## If design have functional ECO, then ignore scan chain when LEC
    switch -regexp -- $env(WB_DESIGN) {
 	cdn_hs_phy_data_slice        {set IGNORE_SCAN NO;}
 	cdn_hs_phy_top               {set IGNORE_SCAN NO;}
 	default		             {set IGNORE_SCAN NO;}
    }
 
    foreach  lib $VSTUBSLVF  {
       if {[regexp cdn_hs_phy_data_slice $lib]} {regsub  /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/output/CDN_102H_cdn_hs_phy_data_slice_EW/prlib/CDN_102H_cdn_hs_phy_data_slice_EW.func.*.lib $lib "/projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/setup/CDN_102H_cdn_hs_phy_data_slice_EW.func.ffg_s250_v0880_m40c_xcbccbt_cbest_CCbest.LEC_VDDGONE_HACK.ideal.lib" lib }
       lappend VSTUBS $lib
    }
}

##valus and libcompiler is for ETMQA flow
namespace eval valus {
  set MODULE_CMD       "module unload ssv ; module load ssv/211/21.15.000"
  set EXEC_CMD 	       "valus"
}

namespace eval libcompiler {
  set MODULE_CMD       "module unload synopsys ; module load synopsys/lc_Q-2019.12-SP2"
  set EXEC_CMD 	       "lc_shell"
}

#######################################################################################
###      SignOff Part settings which are not included in the common_setup.tcl ###########
#######################################################################################

namespace eval signoff {

    set DESIGN     $env(WB_DESIGN)
    set QUEUE      "ddr -P PD"
 
    # Assemle Delay Element for signoff  (Delay Element Package Path)
    set DELAY_ELEMENT_DIR   /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/output
 
    ## IPTAG (Please double check the information in pre2post excel table or check with PM)
    set IPTAG_PROD          /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/iptag/phy_iptag.EW.prod
    set IPTAG_VERSION       R110

    ##Please follow the standard prefix naming rule "cdn_ddr|gddr|hbm_<foundry&node>_<metal stack>_<block_name>_". 
    ##The <foundry&node> and <metal_stack> follow the naming convention in IPTAG

    set UNIQ_PREFIX	   cdn_ddr_T7G_15M1X1Xa1Ya5Y2Yy2Yx2R_cadence_phy_ew_cdn_hs_phy_top_
    
    ## PerBit Macro Data Dir
    set SIGNOFF_PERBIT_DIR  /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/output 

    ## data delivery/release dir
    set RELEASE_DIR         /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/output
    
    # whether include 0c spef/view or not!
    set QRC_INCLUDE_0C 0 

    # Constraint for EMIR analysis
    # In case, the data rate is different for ND and OD, need to assign the proper constraint to the EMIR signoff corners.
    
    switch -regexp -- $env(WB_DESIGN) {
            cdn_hs_phy_top	{set DESIGN4SDC                  [regsub "cadence_phy_ew_" $env(WB_DESIGN) ""]}
            default		{set DESIGN4SDC                  [regsub "CDN_102H_" [regsub "_EW|_NS" $env(WB_DESIGN) ""] ""]}
    }
    
    set SDC_FUNC ""
    set SDC_ROOT "/projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/input/latest/sta_signoff_0p75v/constraints/phy/"

    switch -regexp -- $env(WB_DESIGN) {
         cdn_hs_phy_top			 {set  SDC_FUNC ${SDC_ROOT}/user_setup_top.ets ; lappend SDC_FUNC ${SDC_ROOT}/${DESIGN4SDC}.con.ets}
         default			 {set  SDC_FUNC ${SDC_ROOT}/user_setup.ets     ; lappend SDC_FUNC ${SDC_ROOT}/${DESIGN4SDC}.con.ets} 
    }
    
    set SDC_FUNC_OD ""
    set SDC_ROOT_OD "/projects/brcm_freya_N7G_16bit_NSEW_phy/EW/input/latest/sta_signoff_0p8v/constraints/phy/"

    switch -regexp -- $env(WB_DESIGN) {
         cdn_hs_phy_top			 {set  SDC_FUNC_OD ${SDC_ROOT_OD}/user_setup_top.ets ; lappend SDC_FUNC_OD ${SDC_ROOT_OD}/${DESIGN4SDC}.con.ets}
         default			 {set  SDC_FUNC_OD ${SDC_ROOT_OD}/user_setup.ets     ; lappend SDC_FUNC_OD ${SDC_ROOT_OD}/${DESIGN4SDC}.con.ets} 
    }

    ##caseBycase ##SHE(Self-Heating Effect) analysis for project based on TSMC standard cell library if customer requires.
    ##caseBycase ##How to generate the SHE_ALPHA_PARAM and SHE_BETA_PARAM?
    ##caseBycase ##Take Murano as example
    ##caseBycase ##/process/tsmcN4/data/gp/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/v1d0p1a/vfi/param.sh
    ##caseBycase ##SHE_ALPHA_PARAM :"{{layer1 alpha_overlapping alpha_connecting} {layer2 alpha_overlapping alpha_connecting}...}"
    ##caseBycase ##SHE_BETA_PARAM: "{beta_c1 beta_c2 beta_c3}"
    ##caseBycase ##For TRF file: 
    ##caseBycase ##Cat all foundry standard cell trf file together 
    ##caseBycase ##/process/tsmcN4/data/stdcell/n4gp/TSMC/MISC_n4gp/docs/N4P_H210_v1d0_TRF/trf/*/*.report
    ##caseBycase set SHE_ALPHA_PARAM "{{poly 0.83 0.83} {MD_STI_CPP85 0.83 0.83} {MD_OD_CPP85 0.83 0.83} {VDR 0.83 0.83} {MD_STI_IO 0.83 0.83} {MD_OD_IO 0.83 0.83} {MP 0.83 0.83} {MD_OD 0.83 0.83} {MD_OD_SRM 0.83 0.83} {MD_STI 0.83 0.83} {MD_STI_SRM 0.83 0.83} {M0 0.73 0.83} {M1 0.65 0.83} {M2 0.55 0.83} {M3 0.46 0.83} {M4 0.39 0.83} {M5 0.32 0.83} {M6 0.25 0.83} {M7 0.25 0.83} {M8 0.25 0.83} {M9 0.25 0.83} {M10 0.25 0.83} {M11 0.25 0.83} {M12 0.25 0.83} {M13 0.25 0.83} {M14 0.25 0.83} {M15 0.25 0.83} {AP 0.25 0.83}}"
    ##caseBycase set SHE_BETA_PARAM "{0.0043 -0.0014 0.8318}"
    ##caseBycase set SHE_TRF        /projects/Murano_N4P_80bits_6400_phy/common_scripts/FLOW/she.trf 
    ##caseBycase set SHE_TECH_FILE  /process/tsmcN4/data/gp/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/v1d0p1a/rcworst/Tech/rcworst_CCworst_T/qrcTechFile 

    ##caseBycase ##SEB(Statistical ElectroMigration Budgeting)/FIT(Failures in Time) analysis for project based on TSMC standard cell library if customer requires.
    ##caseBycase ##need to check whether FIT_SEB_TABLE is available
    ##caseBycase set FIT_SEB_LIFETIME 10
    ##caseBycase set FIT_SEB_TABLE /process/tsmcN4/data/gp/QRC/15M1X1Xb1Xe1Ya1Yb5Y2Yy2Z_SHDMIM_UT/seb_ircx_v1d0p1a/SEB_CLN4P_1P15M+UT-ALRDL_1X1XB1XE1YA1YB5Y2YY2Z_SHDMiM.ircx 
  
    # EM signoff view matched from setup_init.yaml#####
    # EM signoff corners: ML+rcworst/TC85
    # signal RC version use cworst, PG RC use rcworst (in tech PGV)
    set EM_analysis_views_CON ""
       lappend EM_analysis_views_CON [list func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold $SDC_FUNC]
       #lappend EM_analysis_views_CON [list func_func_ffg_s250_v0880_125c_xcbccbt_cworst_CCworst_hold $SDC_FUNC_OD]
  
    # IR Drop signoff view matched from setup_init.yaml#####
    # IR Drop signoff corners: Static: ML+rcworst/WC+rcworst/TC85; Dynamic: TC85
    # signal RC version use cworst, PG RC use rcworst (in tech PGV)
    set DYNAMIC_TRIGGER_FILE ""
    set PA_static_views_CON ""
    	lappend PA_static_views_CON [list func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold $SDC_FUNC]
  	lappend PA_static_views_CON [list func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup $SDC_FUNC]
    set PA_dynamic_views_CON ""
    	lappend PA_dynamic_views_CON [list func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold $SDC_FUNC]
   	lappend PA_dynamic_views_CON [list func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup $SDC_FUNC]

    ##VDDR/VDDR6 DL based PA static views 
    set DS_VDDR_PA_static_views_CON ""
        lappend DS_VDDR_PA_static_views_CON [list func_func_ffgnp_0p825v_125c_cbest_CCbest_T_cworst_CCworst_hold $SDC_FUNC]
    set VDDR_DL_based_toggle_setting "/projects/workbench/versions/reference/delayline_toggle_based_on_code/set_activity_for_VDDR_DE_based_on_code.tcl"

    # low power setting
    set phy_top_UPF ""
    set phy_top_powerup_rail "VDDG" 

    # Diemodel generate view matched from setup_init.yaml#####
    # Diemodel generation views: VCD based ML corner read/write die model 
    # FIRM PHY: Don't provide the VCD based die model 
    set Die_vectorbased_views_CON ""
    	lappend Die_vectorbased_views_CON [list func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold_read $SDC_FUNC]
    	lappend Die_vectorbased_views_CON [list func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold_write $SDC_FUNC]

    ##VCD inputs
    set VCD_SCOPE "memcd_test/asic/cadence_phy_ew_ddr_subsystem/cdn_hs_phy_top"
    set VCD_FILE "/projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/input/power_latest/for_power_est/power_read_write_bst.vcd"

    ##Diemodel parameter: "view VCD_FILE VCD_SCOPE VCD_start VCD_end"
    ##Can take 50ns simulation window in the VCD window for simulation for HSPHY/HPPHY/GDDRPHY.
    ##For Dragonfly PHY, the simulation window will be more than 50ps with different modes, please use the actual window.
    ##Event based diemodel generation doesn't need trigger file setting.
    set VCD_DIEMODEL_PARA ""
    lappend VCD_DIEMODEL_PARA [list func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold_read     $VCD_FILE $VCD_SCOPE 541300ns 541350ns]
    lappend VCD_DIEMODEL_PARA [list func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold_write    $VCD_FILE $VCD_SCOPE 511000ns 511050ns]
  

    ## For DDR PHY & ACS/ADR/MCB/DS/ACM/LPS
    ## Die model generation
    set DIE_PG_LIST ""
    switch -regexp -- $env(WB_DESIGN) {
         cdn_hs_phy_top			 {set  DIE_PG_LIST "VDD VDDQ VDDQX VDDQ_CK VDDPLL_MCB VDDPLL_TOP VDDPLL_DS0 VDDPLL_DS1"}
         default			 {set  DIE_PG_LIST "VDD"} 
    }   
    
    ## set voltage for EMIR and Diemodel generation
    set PG_VOLTAGE_SETS_DEFAULT ""
    lappend  PG_VOLTAGE_SETS_DEFAULT  [list  VDD	  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup 0.67]
    lappend  PG_VOLTAGE_SETS_DEFAULT  [list  VDD	  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold    0.83]

    set PG_VOLTAGE_SETS_SPECIAL1 ""
    lappend  PG_VOLTAGE_SETS_SPECIAL1  [list  VDD	  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup 0.67]
    lappend  PG_VOLTAGE_SETS_SPECIAL1  [list  VDDR	  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup 0.580]
    lappend  PG_VOLTAGE_SETS_SPECIAL1  [list  VDD	  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold    0.83]
    lappend  PG_VOLTAGE_SETS_SPECIAL1  [list  VDDR	  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold    0.719]
 
    set PG_VOLTAGE_SETS_SPECIAL2 ""
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDD	  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup   0.67]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDQ	  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup   0.47]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDQ_CK     func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup   0.47]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDQX	  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup   1.01]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDPLL_TOP  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup   0.67]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDPLL_MCB  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup   0.67]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDPLL_DS0  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup   0.67]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDPLL_DS1  func_func_ssg_s250_v0670_125c_xcwccwt_cworst_CCworst_T_setup   0.67]

    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDD	  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold      0.83]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDQ	  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold      0.57]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDQ_CK     func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold      0.57]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDQX	  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold      1.12]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDPLL_TOP  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold      0.83]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDPLL_MCB  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold      0.83]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDPLL_DS0  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold      0.83]
    lappend  PG_VOLTAGE_SETS_SPECIAL2  [list  VDDPLL_DS1  func_func_ffg_s250_v0830_125c_xcbccbt_cworst_CCworst_hold      0.83]

    set PG_VOLTAGE_SETS ""
    ##annotate the regulator VDD current(VDDR_regulator_VDD_current default 45mA; VDDR6_regulator_VDD_current default 20mA)
    ## If low power design,add UPF and POWERUP_RAIL to the block setting like below
    ## phy_top  {set  PG_VOLTAGE_SETS $PG_VOLTAGE_SETS_SPECIAL2 ; set UPF $phy_top_UPF; set POWERUP_RAIL $phy_top_powerup_rail; }

    switch -regexp -- $env(WB_DESIGN) {
         cdn_hs_phy_data_slice 	         {set  PG_VOLTAGE_SETS $PG_VOLTAGE_SETS_SPECIAL1 ; set VDDR_regulator_VDD_current 0.040 ; set VDDR_DL_based_toggle_setting $VDDR_DL_based_toggle_setting;}
         cdn_hs_phy_top			 {set  PG_VOLTAGE_SETS $PG_VOLTAGE_SETS_SPECIAL2 ; set VDDR_regulator_VDD_current 0.040 ;}
         default			 {set  PG_VOLTAGE_SETS $PG_VOLTAGE_SETS_DEFAULT ;} 
    }   

    # DRC/LVS/ANT ruledeck (Pegasus version)
    # If MIMCAP is inserted, we need to set ANTMIMRULE to enable ANT MIM Pegasus run. 

     set LVS             /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck/DFM_LVS_RC_PEGASUS_N7_1p15M_1X1Xa1Ya5Y2Yy2Yx2R_ALRDL.1.2a.freya

     set BLOCK_DRC       /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck/PLN7FF_15M_1X1Xa1Ya5Y2Yy2Yx2R_001.13_1a.encrypt.freya
     set PHY_DRC         /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck/PLN7FF_15M_1X1Xa1Ya5Y2Yy2Yx2R_001.13_1a.encrypt.freya.phy
 
     set PHY_DRC_FEOL    /projects/brcm_freya_N7G_16bit_NSEW_phy/EW/libs/ruledeck/PLN7FF_15M_1X1Xa1Ya5Y2Yy2Yx2R_001.13_1a.encrypt.freya.phy.FEOL
     set PHY_DRC_BEOL    /projects/brcm_freya_N7G_16bit_NSEW_phy/EW/libs/ruledeck/PLN7FF_15M_1X1Xa1Ya5Y2Yy2Yx2R_001.13_1a.encrypt.freya.phy.BEOL
   
     set BLOCK_BEOL      /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck/Dummy_BEOL_Pegasus_7nm_001.13a.freya.otherslice
     set DS_BEOL         /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck/Dummy_BEOL_Pegasus_7nm_001.13a.freya.dataslice
     set PHY_BEOL        /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck/Dummy_BEOL_Pegasus_7nm_001.13a.freya.phy.EW
    
     set BLOCK_FEOL      /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck/Dummy_FEOL_Pegasus_7nm_001.13a.freya.slices
     set PHY_FEOL        /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck/Dummy_FEOL_Pegasus_7nm_001.13a.freya.phy.EW
    
     set ANTRULE	 /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck/PLN7FF_15M_1X1Xa1Ya5Y2Yy2Yx2R_001_ANT.13_1a.encrypt.freya
     #set ANTMIMRULE	 

     set BUMPRULE        /projects/brcm_freya_N7G_16bit_NSEW_phy/EW/libs/ruledeck/PN7_CU_BUMP_ON_PAD_15M_1X1Xa1Ya5Y2Yy2Yx2R_004.07a.freya

     # BEOL/FEOL/DRC/LVS/ANT ruledeck (Calibre version,for TSMCN7, no FEOL/BUMP calibre version)
     # If MIMCAP is inserted, we need to set PHY_CALIBRE_ANTMIM_DIR to enable ANT MIM Calibre run.
     # and add "set CALIBRE_ANTMIM_DIR $PHY_CALIBRE_ANTMIM_DIR" in cadence_phy_ew_cdn_hs_phy_top switch 
     # For BRCM projects, "set CALIBRE_ARC_DIR $PHY_CALIBRE_ARC_DIR" in cadence_phy_ew_cdn_hs_phy_top switch 

     #set PHY_Calibre_FEOL_Dir 
     set PHY_CALIBRE_BEOL_DIR /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck_calibre/M2_3stars_FILL_Dummy_BEOL_TN07CLDR002C3_V10_1A 
     set PHY_CALIBRE_DRC_DIR  /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck_calibre/M2_3stars_DRC_TN07CLDR001C1_1_3_3A 
     set PHY_CALIBRE_ANT_DIR  /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck_calibre/M2_3stars_DRC_ANT_TN07CLDR001C1_1_3_3A
     #set PHY_CALIBRE_ANTMIM_DIR  
     #set PHY_CALIBRE_ARC_DIR  
     set PHY_CALIBRE_LVS_DIR  /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/libs/ruledeck_calibre/M2_3stars_LVS_TN07CLLS001Y1_1_2A_15M_1X1Xa1Ya5Y2Yy2Yx2R_ALRDL
     #set PHY_CALIBRE_BUMP_DIR 

     switch -regexp -- $env(WB_DESIGN) {
            cdn_hs_phy_data_slice	   {set DRCRULE $BLOCK_DRC; set LVSRULE $LVS ; set BEOLRULE $DS_BEOL    ; set FEOLRULE $BLOCK_FEOL ;}
            cdn_hs_phy_dqs_bit		   {set DRCRULE $BLOCK_DRC; set LVSRULE $LVS ; set BEOLRULE $DS_BEOL    ; set FEOLRULE $BLOCK_FEOL ;}
            cdn_hs_phy_dq_bit		   {set DRCRULE $BLOCK_DRC; set LVSRULE $LVS ; set BEOLRULE $DS_BEOL    ; set FEOLRULE $BLOCK_FEOL ;}
            cadence_phy_ew_cdn_hs_phy_top  {set DRCRULE $PHY_DRC;   set DRCRULEBEOL $PHY_DRC_BEOL; set DRCRULEFEOL $PHY_DRC_FEOL; set LVSRULE $LVS ; set BEOLRULE $PHY_BEOL   ; set CALIBRE_BEOL_DIR $PHY_CALIBRE_BEOL_DIR; set FEOLRULE $PHY_FEOL; set CALIBRE_DRC_DIR $PHY_CALIBRE_DRC_DIR; set CALIBRE_ANT_DIR $PHY_CALIBRE_ANT_DIR; set CALIBRE_LVS_DIR $PHY_CALIBRE_LVS_DIR;}
            default			   {set DRCRULE $BLOCK_DRC; set LVSRULE $LVS ; set BEOLRULE $BLOCK_BEOL ; set FEOLRULE $BLOCK_FEOL ;}
     } 

   #LEC
   switch -regexp -- $env(WB_DESIGN) {
   	cdn_hs_phy_top			{set SYN_NETLIST /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/input/latest/eco_netlists/cadence_phy_ew_cdn_hs_phy_top.v.eco}
   	cdn_hs_phy_acm_slice		{set SYN_NETLIST /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/input/latest/netlists/CDN_102H_cdn_hs_phy_acm_slice_EW.vg}
   	cdn_hs_phy_adrctl_slice		{set SYN_NETLIST /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/input/latest/netlists/CDN_102H_cdn_hs_phy_adrctl_slice_EW.vg}
   	cdn_hs_phy_data_slice		{set SYN_NETLIST /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/input/latest/netlists/CDN_102H_cdn_hs_phy_data_slice_EW.vg}
   	default				{set SYN_NETLIST /projects/brcm_freya_N7G_16bit_NSEW_phy_5500/EW/input/latest/netlists/$env(WB_DESIGN).vg}
   }

   # PG TCL
   switch -regexp -- $env(WB_DESIGN) {
        cdn_hs_phy_data_slice         {set CONNECT_PG_TCL "your filename";}
        default                       {}
   }
}
