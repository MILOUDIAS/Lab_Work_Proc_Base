# defaults
SIM ?= verilator
TOPLEVEL_LANG ?= verilog
EXTRA_ARGS += --trace --trace-structs
WAVES = 1

VERILOG_SOURCES += $(PWD)/../../rtl/definitions_pkg.sv
VERILOG_SOURCES += $(PWD)/../../rtl/ram.sv

# The top-level module we want to test
TOPLEVEL = ram

# The Python test file
MODULE = test_ram

# Include cocotb's make rules
include $(shell cocotb-config --makefiles)/Makefile.sim