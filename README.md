# Lab Work Proc Base Repository

This repository contains the lab work for a Basic custom processor for my lab work, written in SystemVerilog. All simulations and verification are performed using open-source EDA tools.

## 1. Setup & Environment: `IIC-OSIC-TOOLS`

To ensure a consistent and reproducible environment, all the necessary tools for this lab have been pre-installed in the **[`IIC-OSIC-TOOLS`](https://github.com/iic-jku/IIC-OSIC-TOOLS)** environment. There is no need to install any software on your local machine.

Please launch the `IIC-OSIC-TOOLS` container or virtual machine to access all required dependencies.

## 2. Running Simulations with Cocotb

The simulations are based on `cocotb`, a coroutine-based cosimulation library for VHDL/Verilog/SystemVerilog. The testbenches are written in Python.

### How to Run a Simulation

#### Way one

All simulation targets are managed using a `Makefile`. To run a specific testbench, navigate to the relevant lab directory and use the `make` command.

**Example:**

Let's assume you are in a directory containing a `Makefile` and a cocotb test file.

1.  **Launch the simulation:**
    Open a terminal within the `IIC-OSIC-TOOLS` environment, navigate to the project directory, go the 'tb' directory, and got to sub directory you want to test:

    ```bash
    cd tb/alu
    make
    ```

    This command compiles the HDL source files and executes the Python testbench using the Verilator simulator.

2.  **Simulation Output:**
    The `make` command will generate output files, including a waveform dump file (typically with a `.vcd` extension), such as `dump.vcd`.

#### Way Two

go the 'tb' sub directory, and execute the command:

    ```bash
    make clean      # to clean previous simulations
    make alu_test   # to test the alu
    make proc_base_test   # to test the top level core
    ```

## 3. Viewing Waveforms with GTKWave

After a simulation is complete, you can analyze the resulting waveforms using `GTKWave`.

### How to View a Dump File

1.  **Launch GTKWave:**
    From the same terminal, launch `GTKWave` and provide the path to the dump file, first go to the disered sub directory in the 'tb' folder, and run:

    ```bash
    gtkwave dump.vcd
    ```

2.  **Analyze Waveforms:**
    GTKWave will open, allowing you to drag and drop signals into the waveform viewer to analyze the circuit's behavior during the simulation.

## 4. My simulations results

### ALU simulation:

##### the results of verilator using cocotb:

![`alu cocotb`](simulations/alu_cocotb.png)

##### the results of waveforms:

![`alu cocotb`](simulations/alu_dump_vcd.png)

### Control Unit simulation:

##### the results of verilator using cocotb:

![`alu cocotb`](simulations/control_unit_cocotb.png)

##### the results of waveforms:

![`alu cocotb`](simulations/control_unit_dump_vcd.png)

### ram simulation:

##### the results of verilator using cocotb:

![`alu cocotb`](simulations/ram_cocotb.png)

##### the results of waveforms:

![`alu cocotb`](simulations/ram_dump_vcd.png)

### Top level proc base simulation:

##### the results of verilator using cocotb:

![`alu cocotb`](simulations/proc_base_cocotb.png)

##### the results of waveforms:

![`alu cocotb`](simulations/proc_base_dump_vcd.png)
