# test_ram.py
#
# Cocotb testbench for the SystemVerilog RAM module from the "Processeur de Base" project.
#
# This testbench verifies:
# - Synchronous write functionality.
# - Asynchronous read functionality.
# - Correct data storage and retrieval at various addresses.
# - Behavior of read enable (rd_en) signal.

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock
import random

# --- Constants derived from the DUT parameters ---
# These can be read directly from the DUT in cocotb if needed,
# but defining them here is clear for this testbench.
ADDR_WIDTH = 12
DATA_WIDTH = 16
MAX_ADDR = (1 << ADDR_WIDTH) - 1
MAX_DATA = (1 << DATA_WIDTH) - 1

async def reset_dut(dut, clk):
    """Helper coroutine to initialize DUT inputs."""
    dut.addr.value = 0
    dut.data_in.value = 0
    dut.wr_en.value = 0
    dut.rd_en.value = 0
    await RisingEdge(clk)
    dut._log.info("DUT inputs initialized.")


@cocotb.test()
async def test_randomized_access(dut):
    """Write to multiple random addresses and verify by reading back."""
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    
    await reset_dut(dut, dut.clk)
    
    # Golden model: A Python dictionary to store our expected memory content
    golden_memory = {}
    num_tests = 50
    
    dut._log.info(f"Starting randomized test with {num_tests} writes.")

    # --- Random Write Phase ---
    for i in range(num_tests):
        # Generate random address and data
        rand_addr = random.randint(0, MAX_ADDR)
        rand_data = random.randint(0, MAX_DATA)

        # Store in our golden model
        golden_memory[rand_addr] = rand_data
        
        # Drive the DUT to write
        dut.addr.value = rand_addr
        dut.data_in.value = rand_data
        dut.wr_en.value = 1
        
        await RisingEdge(dut.clk)
    
    # De-assert write enable after the loop
    dut.wr_en.value = 0
    await RisingEdge(dut.clk)

    dut._log.info("Random write phase complete. Starting read verification.")

    # --- Read Verification Phase ---
    # Read back every address we wrote to and check against the golden model
    for addr, expected_data in golden_memory.items():
        dut.addr.value = addr
        dut.rd_en.value = 1
        
        await Timer(1, units='ns') # Wait for async read
        
        read_data = dut.data_out.value
        
        dut._log.info(f"Verifying addr {addr}: Expected 0x{expected_data:X}, Got 0x{read_data.integer:X}")
        assert read_data == expected_data, \
            f"Mismatch at address {addr}! Expected 0x{expected_data:X}, got 0x{read_data.integer:X}"

    dut.rd_en.value = 0
    await Timer(1, units='ns')
    
    dut._log.info("Randomized access test PASSED.")
