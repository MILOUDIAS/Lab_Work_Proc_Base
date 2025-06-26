# Makefile for running cocotb tests on the ALU

# defaults
SIM ?= verilator
TOPLEVEL_LANG ?= verilog
EXTRA_ARGS += --trace --trace-structs
WAVES = 1

VERILOG_SOURCES += $(PWD)/../../rtl/definitions_pkg.sv
VERILOG_SOURCES += $(PWD)/../../rtl/ram.sv
VERILOG_SOURCES += $(PWD)/../../rtl/control_unit.sv
VERILOG_SOURCES += $(PWD)/../../rtl/alu.sv
VERILOG_SOURCES += $(PWD)/../../rtl/proc_base.sv

# The top-level module we want to test
TOPLEVEL = proc_base

# The Python test file
MODULE = test_proc_base

# Include cocotb's make rules
include $(shell cocotb-config --makefiles)/Makefile.sim