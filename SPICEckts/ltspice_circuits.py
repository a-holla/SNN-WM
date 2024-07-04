from PyLTSpice import SpiceEditor, SimRunner, RawRead
import numpy as np
from time import time
import pandas as pd
import networkx as nx
from auxiliary.graph_gen import *
import os
import shutil

def ring_oscillator_def():
    # returns the multiline subcircuit definition of the ring oscillator
    definition=""".subckt ring_oscillator_9_stage V_dd V_in Inv_1 V_out
M73 Inv_1 V_in V_dd V_dd PMOS
M74 Inv_1 V_in 0 0 NMOS
M75 N001 Inv_1 V_dd V_dd PMOS
M76 N001 Inv_1 0 0 NMOS
M77 N002 N001 V_dd V_dd PMOS
M78 N002 N001 0 0 NMOS
M79 N003 N002 V_dd V_dd PMOS
M80 N003 N002 0 0 NMOS
M81 N004 N003 V_dd V_dd PMOS
M82 N004 N003 0 0 NMOS
M83 N005 N004 V_dd V_dd PMOS
M84 N005 N004 0 0 NMOS
M85 N006 N005 V_dd V_dd PMOS
M86 N006 N005 0 0 NMOS
M87 N007 N006 V_dd V_dd PMOS
M88 N007 N006 0 0 NMOS
M89 V_out N007 V_dd V_dd PMOS
M90 V_out N007 0 0 NMOS
.include p18_cmos_models_tt.inc
.ends ring_oscillator_9_stage\n"""

    return definition

def graph_maxcut_circuit_gen(graph: nx.Graph, coupling_resistors: np.ndarray,shil_dc_value:int,shil_resistor_value: int, shil_noise_fraction:np.ndarray, problem_name: str,start_time="0",stop_time="10u",record_start_time="0",step_size_time="0.1n"):
    
    num_nodes=len(list(graph.nodes))
    netlist_file=open(file=f"{problem_name}.net", mode="w")
    netlist_file.write("* Python Script Created Netlist File\n")

    # oscillator voltage supply
    vdd_positive_node="V_dd"
    vdd_negative_node="0"
    vdd_expression="5"  #vdd voltage behavior, integer means that particular DC value, expression for AC/noise
    vdd_name="V_dd_supply"
    vdd_voltage_command=f"{vdd_name} {vdd_positive_node} {vdd_negative_node} {vdd_expression}"
    netlist_file.write(f"{vdd_voltage_command}\n")

    # oscillator SHIL supply, oscillators insertion and SHIL resistor connection
    netlist_file.write("\n")

    shil_freq="35e6"
    '''
    Version 1.0: Individual SHIL source for each oscillator.
    Version 2.0: Common SHIL for each oscillator.
    '''
    nf=shil_noise_fraction[0]
    shil_voltage_positive_node=f"V_shil"
    shil_voltage_negative_node="0"
    shil_voltage_name=f"BSHIL"
    shil_voltage_expression=f"V={shil_dc_value}*(sin(2*pi*({shil_freq})*time)+{nf}*(white({shil_freq}/time)))"
    shil_voltage_command=f"{shil_voltage_name} {shil_voltage_positive_node} {shil_voltage_negative_node} {shil_voltage_expression}"
    netlist_file.write(f"{shil_voltage_command}\n")

    for v in range(num_nodes):
        oscillator_name=f"XX{v}"
        oscillator_vdd_node=vdd_positive_node
        oscillator_input_node=f"V_out_{v}" #shorted to output node, can include a feature to add a resistor in between
        oscillator_inverter_node=f"V_invert_{v}" #output from the first inverter, used for negative coupling
        oscillator_output_node=f"V_out_{v}"
        oscillator_reference="ring_oscillator_9_stage" #oscillator subcircuit reference
        oscillator_command=f"{oscillator_name} {oscillator_vdd_node} {oscillator_input_node} {oscillator_inverter_node} {oscillator_output_node} {oscillator_reference}"
        netlist_file.write(f"{oscillator_command}\n")

        
        shil_resistor_positive_node=shil_voltage_positive_node #output of shil voltage
        shil_resistor_negative_node=oscillator_input_node #output of oscillator j
        shil_resistor_name=f"R_il_{v}"
        shil_resistor_command=f"{shil_resistor_name} {shil_resistor_positive_node} {shil_resistor_negative_node} {shil_resistor_value}"
        netlist_file.write(f"{shil_resistor_command}\n")
        netlist_file.write("\n")

        
    # oscillator coupling
    # ij definition: input: i output: j
    netlist_file.write("\n")
    for i in range(num_nodes):
        for j in range(num_nodes):
            if coupling_resistors[i][j]==0:
                continue
            resistor_value=round(coupling_resistors[i][j])
            resistor_positive_node=f"V_out_{i}" #input of oscillator i
            resistor_negative_node=f"V_invert_{j}" #output of oscillator j
            resistor_name=f"R_c_{i}_{j}"
            resistor_command=f"{resistor_name} {resistor_positive_node} {resistor_negative_node} {resistor_value}"
            netlist_file.write(f"{resistor_command}\n")
    
    # subcircuits
    netlist_file.write("\n")
    netlist_file.write("* block symbol definitions\n")
    netlist_file.write(ring_oscillator_def())
    

    # model statements, NMOS and PMOS. Change the directory of models according to your LTSPice path
    netlist_file.write("\n")
    netlist_file.write(".model NMOS NMOS\n")
    netlist_file.write(".model PMOS PMOS\n")
    netlist_file.write(".lib C:\\Users\\sanya\\AppData\\Local\\LTspice\\lib\\cmp\\standard.mos\n")

    # analysis statements. I primarily use transient analysis
    netlist_file.write("\n")
    
    transient_command=f".tran {start_time} {stop_time} {record_start_time} {step_size_time} uic"
    netlist_file.write(f"{transient_command}\n")

    # ending the writing
    netlist_file.write(".backanno\n")
    netlist_file.write(".end\n")
    netlist_file.close()
 
def no_shil_maxcut_circuit(graph: nx.Graph, coupling_resistors: np.ndarray, problem_name: str,start_time="0",stop_time="10u",record_start_time="0",step_size_time="0.1n"):
    
    num_nodes=len(list(graph.nodes))
    netlist_file=open(file=f"{problem_name}.net", mode="w")
    netlist_file.write("* Python Script Created Netlist File\n")

    # oscillator voltage supply
    vdd_positive_node="V_dd"
    vdd_negative_node="0"
    vdd_expression="5"  #vdd voltage behavior, integer means that particular DC value, expression for AC/noise
    vdd_name="V_dd_supply"
    vdd_voltage_command=f"{vdd_name} {vdd_positive_node} {vdd_negative_node} {vdd_expression}"
    netlist_file.write(f"{vdd_voltage_command}\n")

    # Oscillators insertion
    netlist_file.write("\n")
    
    for v in range(num_nodes):
        oscillator_name=f"XX{v}"
        oscillator_vdd_node=vdd_positive_node
        oscillator_input_node=f"V_out_{v}" #shorted to output node, can include a feature to add a resistor in between
        oscillator_inverter_node=f"V_invert_{v}" #output from the first inverter, used for negative coupling
        oscillator_output_node=f"V_out_{v}"
        oscillator_reference="ring_oscillator_9_stage" #oscillator subcircuit reference
        oscillator_command=f"{oscillator_name} {oscillator_vdd_node} {oscillator_input_node} {oscillator_inverter_node} {oscillator_output_node} {oscillator_reference}"
        netlist_file.write(f"{oscillator_command}\n")
        
    # oscillator coupling
    # ij definition: input: i output: j
    netlist_file.write("\n")
    for i in range(num_nodes):
        for j in range(num_nodes):
            if coupling_resistors[i][j]==0:
                continue
            resistor_value=round(coupling_resistors[i][j])
            resistor_positive_node=f"V_out_{i}" #input of oscillator i
            resistor_negative_node=f"V_invert_{j}" #output of oscillator j
            resistor_name=f"R_c_{i}_{j}"
            resistor_command=f"{resistor_name} {resistor_positive_node} {resistor_negative_node} {resistor_value}"
            netlist_file.write(f"{resistor_command}\n")
    
    # subcircuits
    netlist_file.write("\n")
    netlist_file.write("* block symbol definitions\n")
    netlist_file.write(ring_oscillator_def())
    

    # model statements, NMOS and PMOS. Change the directory of models according to your LTSPice path
    netlist_file.write("\n")
    netlist_file.write(".model NMOS NMOS\n")
    netlist_file.write(".model PMOS PMOS\n")
    netlist_file.write(".lib C:\\Users\\sanya\\AppData\\Local\\LTspice\\lib\\cmp\\standard.mos\n")

    # analysis statements. I primarily use transient analysis
    netlist_file.write("\n")
    
    transient_command=f".tran {start_time} {stop_time} {record_start_time} {step_size_time} uic"
    netlist_file.write(f"{transient_command}\n")

    # ending the writing
    netlist_file.write(".backanno\n")
    netlist_file.write(".end\n")
    netlist_file.close()


def custom_anneal_maxcut_circuit(graph: nx.Graph, coupling_resistors: np.ndarray,shil_function: callable,shil_params: dict,shil_resistor_value: int, problem_name: str,start_time="0",stop_time="10u",record_start_time="0",step_size_time="0.1n"):
    
    num_nodes=len(list(graph.nodes))
    netlist_file=open(file=f"{problem_name}.net", mode="w")
    netlist_file.write("* Python Script Created Netlist File\n")

    # oscillator voltage supply
    vdd_positive_node="V_dd"
    vdd_negative_node="0"
    vdd_expression="5"  #vdd voltage behavior, integer means that particular DC value, expression for AC/noise
    vdd_name="V_dd_supply"
    vdd_voltage_command=f"{vdd_name} {vdd_positive_node} {vdd_negative_node} {vdd_expression}"
    netlist_file.write(f"{vdd_voltage_command}\n")

    # oscillator SHIL supply, oscillators insertion and SHIL resistor connection
    netlist_file.write("\n")

    shil_freq="35e6"
    '''
    Version 1.0: Individual SHIL source for each oscillator.
    Version 2.0: Common SHIL for each oscillator.
    '''

    shil_voltage_positive_node=f"V_shil"
    shil_voltage_negative_node="0"
    shil_voltage_name=f"BSHIL"

    kwargs=shil_params
    shil_voltage_expression=shil_function(**kwargs)
    shil_voltage_command=f"{shil_voltage_name} {shil_voltage_positive_node} {shil_voltage_negative_node} {shil_voltage_expression}"
    netlist_file.write(f"{shil_voltage_command}\n")

    for v in range(num_nodes):
        oscillator_name=f"XX{v}"
        oscillator_vdd_node=vdd_positive_node
        oscillator_input_node=f"V_out_{v}" #shorted to output node, can include a feature to add a resistor in between
        oscillator_inverter_node=f"V_invert_{v}" #output from the first inverter, used for negative coupling
        oscillator_output_node=f"V_out_{v}"
        oscillator_reference="ring_oscillator_9_stage" #oscillator subcircuit reference
        oscillator_command=f"{oscillator_name} {oscillator_vdd_node} {oscillator_input_node} {oscillator_inverter_node} {oscillator_output_node} {oscillator_reference}"
        netlist_file.write(f"{oscillator_command}\n")

        
        shil_resistor_positive_node=shil_voltage_positive_node #output of shil voltage
        shil_resistor_negative_node=oscillator_input_node #output of oscillator j
        shil_resistor_name=f"R_il_{v}"
        shil_resistor_command=f"{shil_resistor_name} {shil_resistor_positive_node} {shil_resistor_negative_node} {shil_resistor_value}"
        netlist_file.write(f"{shil_resistor_command}\n")
        netlist_file.write("\n")

        
    # oscillator coupling
    # ij definition: input: i output: j
    netlist_file.write("\n")
    for i in range(num_nodes):
        for j in range(num_nodes):
            if coupling_resistors[i][j]==0:
                continue
            resistor_value=round(coupling_resistors[i][j])
            resistor_positive_node=f"V_out_{i}" #input of oscillator i
            resistor_negative_node=f"V_invert_{j}" #output of oscillator j
            resistor_name=f"R_c_{i}_{j}"
            resistor_command=f"{resistor_name} {resistor_positive_node} {resistor_negative_node} {resistor_value}"
            netlist_file.write(f"{resistor_command}\n")
    
    # subcircuits
    netlist_file.write("\n")
    netlist_file.write("* block symbol definitions\n")
    netlist_file.write(ring_oscillator_def())
    

    # model statements, NMOS and PMOS. Change the directory of models according to your LTSPice path
    netlist_file.write("\n")
    netlist_file.write(".model NMOS NMOS\n")
    netlist_file.write(".model PMOS PMOS\n")
    netlist_file.write(".lib C:\\Users\\sanya\\AppData\\Local\\LTspice\\lib\\cmp\\standard.mos\n")

    # analysis statements. I primarily use transient analysis
    netlist_file.write("\n")
    
    transient_command=f".tran {start_time} {stop_time} {record_start_time} {step_size_time} uic"
    netlist_file.write(f"{transient_command}\n")

    # ending the writing
    netlist_file.write(".backanno\n")
    netlist_file.write(".end\n")
    netlist_file.close()

def linear_increase_anneal_shil(shil_freq:int, time:str,noise_frac: float, dc_val_end: float, dc_val_start=0.0):
    '''
    Annealing the SHIL voltage, as that is easier to modulate in practise than modulating the SHIL coupling element (resistor or any other element)

    This is an amplitude anneal where amplitude is varied, hence the Voltage is the form:
    V= A(t)*(periodic function + noise)

    In this case the periodic function is second harmonic sinusoidal.

    Current supported time frames: microsecond, milliseconds
    '''
    time_factor=0
    if time[-1]=="u":
        time_factor=1e6/int(time[:-1]) #converting microsecond to seconds
    elif time[-1]=="m":
        time_factor=1e3/int(time[:-1]) #converting millisecond to seconds
    shil_voltage_expression=f"V=({dc_val_start}+({dc_val_end}-{dc_val_start})*{time_factor}*time)*(sin(2*pi*({shil_freq})*time)+{noise_frac}*(white({shil_freq}/time)))"
    return shil_voltage_expression

def linear_decrease_anneal_shil(shil_freq:int, time:str,noise_frac: float, dc_val_end: float, dc_val_start=0.0):
    '''
    Annealing the SHIL voltage, as that is easier to modulate in practise than modulating the SHIL coupling element (resistor or any other element)

    This is an amplitude anneal where amplitude is varied, hence the Voltage is the form:
    V= A(t)*(periodic function + noise)

    In this case the periodic function is second harmonic sinusoidal.

    Current supported time frames: microsecond, milliseconds
    '''
    time_factor=0
    if time[-1]=="u":
        time_factor=1e6/int(time[:-1]) #converting microsecond to seconds
    elif time[-1]=="m":
        time_factor=1e3/int(time[:-1]) #converting millisecond to seconds
    shil_voltage_expression=f"V=({dc_val_end}+({dc_val_start}-{dc_val_end})*{time_factor}*time)*(sin(2*pi*({shil_freq})*time)+{noise_frac}*(white({shil_freq}/time)))"
    return shil_voltage_expression

def capacitive_coupling_maxcut_circuit(graph: nx.Graph, coupling_caps: np.ndarray, problem_name: str,start_time="0",stop_time="10u",record_start_time="0",step_size_time="0.1n"):
    num_nodes=len(list(graph.nodes))
    netlist_file=open(file=f"{problem_name}.net", mode="w")
    netlist_file.write("* Python Script Created Netlist File\n")

    # oscillator voltage supply
    vdd_positive_node="V_dd"
    vdd_negative_node="0"
    vdd_expression="5"  #vdd voltage behavior, integer means that particular DC value, expression for AC/noise
    vdd_name="V_dd_supply"
    vdd_voltage_command=f"{vdd_name} {vdd_positive_node} {vdd_negative_node} {vdd_expression}"
    netlist_file.write(f"{vdd_voltage_command}\n")

    # Oscillators insertion
    netlist_file.write("\n")
    
    for v in range(num_nodes):
        oscillator_name=f"XX{v}"
        oscillator_vdd_node=vdd_positive_node
        oscillator_input_node=f"V_out_{v}" #shorted to output node, can include a feature to add a resistor in between
        oscillator_inverter_node=f"V_invert_{v}" #output from the first inverter, used for negative coupling
        oscillator_output_node=f"V_out_{v}"
        oscillator_reference="ring_oscillator_9_stage" #oscillator subcircuit reference
        oscillator_command=f"{oscillator_name} {oscillator_vdd_node} {oscillator_input_node} {oscillator_inverter_node} {oscillator_output_node} {oscillator_reference}"
        netlist_file.write(f"{oscillator_command}\n")
        
    # oscillator coupling
    # ij definition: input: i output: j
    netlist_file.write("\n")
    for i in range(num_nodes):
        for j in range(num_nodes):
            if coupling_caps[i][j]==0:
                continue
            capacitor_value=round(coupling_caps[i][j])
            capacitor_positive_node=f"V_out_{i}" #input of oscillator i
            capacitor_negative_node=f"V_invert_{j}" #output of oscillator j
            capacitor_name=f"C_{i}_{j}"
            capacitor_command=f"{capacitor_name} {capacitor_positive_node} {capacitor_negative_node} {capacitor_value}p"
            netlist_file.write(f"{capacitor_command}\n")
    
    # subcircuits
    netlist_file.write("\n")
    netlist_file.write("* block symbol definitions\n")
    netlist_file.write(ring_oscillator_def())
    

    # model statements, NMOS and PMOS. Change the directory of models according to your LTSPice path
    netlist_file.write("\n")
    netlist_file.write(".model NMOS NMOS\n")
    netlist_file.write(".model PMOS PMOS\n")
    netlist_file.write(".lib C:\\Users\\sanya\\AppData\\Local\\LTspice\\lib\\cmp\\standard.mos\n")

    # analysis statements. I primarily use transient analysis
    netlist_file.write("\n")
    
    transient_command=f".tran {start_time} {stop_time} {record_start_time} {step_size_time} uic"
    netlist_file.write(f"{transient_command}\n")

    # ending the writing
    netlist_file.write(".backanno\n")
    netlist_file.write(".end\n")
    netlist_file.close()