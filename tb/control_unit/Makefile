# defaults
SIM ?= verilator
TOPLEVEL_LANG ?= verilog
EXTRA_ARGS += --trace --trace-structs
WAVES = 1

VERILOG_SOURCES += $(PWD)/../../rtl/definitions_pkg.sv
VERILOG_SOURCES += $(PWD)/../../rtl/control_unit.sv

# The top-level module we want to test
TOPLEVEL = control_unit

# The Python test file
MODULE = test_control_unit

# Include cocotb's make rules
include $(shell cocotb-config --makefiles)/Makefile.sim