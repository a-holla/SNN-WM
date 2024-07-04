from PyLTSpice import SpiceEditor, SimRunner, RawRead
import numpy as np


def lif_def():
    #Return circuit definition of LIF circuit block
    lif_str = """.subckt liftest_mod Vmem Out
C1 Vmem 0 0.5p
V1 VDD 0 1.8
R8 Vmem 0 33.33e6
V2 N008 0 90m
C2 VC2 0 50p
R2 N009 0 69k
A1 VC2 0 0 0 0 0 N010 0 SCHMITT Vhigh=1.8 Vt=100m Vh=60m Trise=1n Tfall=1n
V5 VSS 0 -1.8
XU1 Vmem N008 VDD VSS N007 TLV9032
M1 N003 N007 0 0 CMOSN w=180n
M2 VDD N007 N003 VDD CMOSP w=180n
V3 N002 0 0.2
M4 VDD N002 N005 VDD CMOSP w=900n
M5 N005 N003 Vmem VDD CMOSP w=540n
M8 VDD N004 N006 VDD CMOSP w=2700n
M7 0 N010 Vmem 0 CMOSN w=1080n m=1
V6 N004 0 0.1
M9 N006 N003 VC2 VDD CMOSP w=27000n
M3 VC2 N003 N009 0 CMOSN w=180n
XU2 N001 Vmem VDD VSS Out TLV9032
V4 N001 0 200m
.ic V(Vmem) = 0
.ic V(VC2) = 0
.include tsmc018.lib
.ends liftest_mod \n"""
    return lif_str

def tempotron_def():
    tempotron_str = """.subckt tempotroncircuit_new Vpre Vout Voutp
V1 VDD 0 1.8
V4 VS1 0 0.7
C1 VDD VC1 4p
V5 VS2 0 1.65
V6 VS3 0 1.6
V7 VSS 0 -1.8
V8 VS1p 0 -0.7
V9 VS3p 0 -1.6
V10 VS2p 0 -1.65
C2 VSS VC2 7p
M8 VSS VS3p VC2 VSS CMOSN
M7 VSS VC2 N004 N003 CMOSN l=130n w=200n
C3 N004 0 0.25p
R1 N004 0 6e6
R2 N006 Vout 1k
XU2 0 N006 VDD VSS Voutp level1 Avol=1Meg GBW=10Meg Vos=0 En=0 Enk=0 In=0 Ink=0 Rin=500Meg
R3 N006 Voutp 1k
V3 N005 N004 24.72µ
M1 N001 Vpre VDD VSS CMOSN w=540n
M2 VDD Vprep N001 VDD CMOSP w=540n
M3 N001 Vprep VS1 VSS CMOSN w=540n
M4 VS1 Vpre N001 VDD CMOSP w=540n
M6 VDD VS3 VC1 VDD CMOSP w=180n
M5 VDD VC1 N004 VDD CMOSP
M12 N002 Vpre VSS VSS CMOSN w=540n
M13 VSS Vprep N002 VDD CMOSP w=540n
M14 N002 Vprep VS1p VSS CMOSN w=540n
M15 VS1p Vpre N002 VDD CMOSP w=540n
M9 Vprep Vpre VSS VSS CMOSN w=180n
M10 VDD Vpre Vprep VDD CMOSP w=180n
M11 VC1 N001 VS2 VDD PMOS
M16 VC2 N002 VS2p VSS NMOS
XU1 N005 Vout VDD VSS Vout level1 Avol=1Meg GBW=10Meg Vos=0 En=0 Enk=0 In=0 Ink=0 Rin=500Meg
.ic V(VC1)=1.8
.include ibm130.lib
.ic V(VC2)=-1.8
.ends tempotroncircuit_new \n"""
    return tempotron_str

def cccs_def():
    cccs_str = """.subckt i_controlled_i_source In Out
V1 VDD 0 1.8
V2 VSS 0 -1.8
R2 In N003 750
XU1 0 In VDD VSS N003 level1 Avol=1Meg GBW=10Meg Vos=0 En=0 Enk=0 In=0 Ink=0 Rin=500Meg
XU2 Out N002 VDD VSS N001 level1 Avol=1Meg GBW=10Meg Vos=0 En=0 Enk=0 In=0 Ink=0 Rin=500Meg
R4 Out In 15e6
R5 N002 N003 15e6
R6 Out N001 15e6
R7 N001 N002 15e6
.ends i_controlled_i_source \n"""
    return cccs_str

def make_crossbar(weights, input_image, num_rows = 10, num_cols = 784):
    
    netlist_file=open(file="./retention_crossbar.net", mode="w")
    
    netlist_file.write("* Python Script Created Netlist File\n")
    
    netlist_file.write("* Global VDD node\n")
    vdd_val = "1.8"
    
    vdd_voltage_command=f"V1 VDD 0 {vdd_val}"
    netlist_file.write(f"{vdd_voltage_command}\n")
    
    netlist_file.write("* Backward Input Current Sources\n")
    t_exposure = "110u"
    t_observation = "330u"
    t_exposure_int = 110
    I_excitation_lt2 = "30n"
    current_pulse_string = f"PULSE({I_excitation_lt2} 0 {t_exposure} 1n 1n {t_observation})" #I1 I2 t_delay t_rise t_fall t_on
    offset_res_val = 332
        
    #Tempotron, Synaptic Resistors, I2I source, WM LIF neurons
    netlist_file.write("*WM LIF\n")
    
    for i in range(num_cols):
        netlist_file.write(f"XCCCS_SM_WM_{i} COL_WM_{i} BXL_WM_{i} i_controlled_i_source\n")
        netlist_file.write(f"XL_WM_{i} BXL_WM_{i} V_WM_{i} liftest_mod \n")
    
    
    #WM feedback path
    netlist_file.write("*WM Feedback\n")
    for i in range(num_cols):
        netlist_file.write(f"XT_WM_WM_{i} V_WM_{i} ROW_WM_FB_{i} ROW_WM_FB_{i}p tempotroncircuit_new\n")
        feedback_weight_resistance = 270
        netlist_file.write(f"R_WM_WM_{i}{i} ROW_WM_FB_{i} COL_WM_{i} {feedback_weight_resistance}\n") 
        netlist_file.write(f"R_WM_WM_{i}{i}p ROW_WM_FB_{i}p COL_WM_{i} {offset_res_val}\n") #Offset resistor
        
    #Current Input to Sensory Memory Neurons
    I_SM_input_max = 30 #nA
    input_image_norm = (input_image - input_image.min())/(input_image.max() - input_image.min())
    
    netlist_file.write("*SM Input\n")
    for i in range(num_cols):
        I_excitation_SM = float(input_image_norm[i]*I_SM_input_max)
        current_pulse_string = f"PULSE({I_excitation_SM}n 0 {t_exposure} 1n 1n {t_observation})" #I1 I2 t_delay t_rise t_fall t_on
        netlist_file.write(f"I_IN_SM_{i} VDD IN_SM_{i} {current_pulse_string}\n")
    
        
    #Sensory Memory Neurons + Tempotron + Synaptic Resistor
    netlist_file.write("*Sensory Memory\n")
    for i in range(num_cols):
        netlist_file.write(f"XL_SM_{i} IN_SM_{i} V_SM_{i} liftest_mod \n")
        netlist_file.write(f"XT_SM_WM_{i} V_SM_{i} ROW_SM_{i} ROW_SM_{i}p tempotroncircuit_new\n")
        sm_wm_weight = 600
        sm_wm_synaptic_resistance = 1/((sm_wm_weight/900 + 1)/332)
        netlist_file.write(f"R_SM_WM_{i}{i} ROW_SM_{i} COL_WM_{i} {sm_wm_synaptic_resistance}\n") 
        netlist_file.write(f"R_SM_WM_{i}{i}p ROW_SM_{i}p COL_WM_{i} {offset_res_val}\n") #Offset resistor
        
        
    #Block Definitions
    netlist_file.write("* block symbol definitions\n")
    netlist_file.write(lif_def())
    netlist_file.write("\n")
    netlist_file.write(tempotron_def())
    netlist_file.write("\n")
    netlist_file.write(cccs_def())
    netlist_file.write("\n\n")
    
    #CMOS definitions
    netlist_file.write(".model NMOS NMOS\n")
    netlist_file.write(".model PMOS PMOS\n")
    netlist_file.write(".lib C:\\Users\\amodh\\OneDrive\\Documents\\LTspiceXVII\\lib\\cmp\\standard.mos\n")

    #Simulation commands
    netlist_file.write(f".tran {4*t_exposure_int}u \n")
    
    #Add some external libraries
    netlist_file.write(".lib C:\\Users\\amodh\\OneDrive\\Desktop\\working_memory notes\\SPICEckts\\comparator\\tlv9032.lib\n")
    netlist_file.write(".lib LTC.lib\n")
    netlist_file.write(".lib UniversalOpAmp1.lib\n")
    netlist_file.write(".backanno\n")
    netlist_file.write(".end\n")
    
    
    netlist_file.close()
    
    print("Completed generating the netlist!")
    

num_rows = 1
num_cols = 196
row_len = 14
col_len = 14
weights = np.load('./weights/trained_lt1_lt2_weight_reduced.npy')
weights = weights.reshape((row_len, col_len, -1))
make_crossbar(None, weights[:, :, 0:1].reshape((num_cols, -1)), num_rows = None, num_cols = num_cols)


#FOR DEBUG PURPOSE
'''
num_rows = 1
num_cols = 2
weights = np.array([80, 400]).reshape((1, 2))
make_crossbar(weights, weights.reshape((2, 1)), num_rows = num_rows, num_cols = num_cols)
'''

    
    

