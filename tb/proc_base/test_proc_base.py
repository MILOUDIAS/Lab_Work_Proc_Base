# test_proc_base.py
#
# Cocotb testbench for the top-level proc_base CPU module.
#
# This testbench loads a simple program into the CPU's internal RAM,
# executes it, and verifies the final result stored back in RAM.

import cocotb
from cocotb.triggers import RisingEdge, Timer
from cocotb.clock import Clock

# --- Constants from definitions_pkg ---
# Opcodes
OP_ADD = 1
OP_LDA = 2
OP_STA = 3
OP_NON_IRM = 7

# --- Assembler Helper ---
def assemble(mnemonic, operand=0, i_bit=0):
    """A simple assembler to convert mnemonics to 16-bit machine code."""
    if mnemonic == "LDA":
        # Opcode=2 (010), I=i_bit. Format: I | 010 | Addr
        return (i_bit << 15) | (OP_LDA << 12) | operand
    if mnemonic == "ADD":
        # Opcode=1 (001), I=i_bit. Format: I | 001 | Addr
        return (i_bit << 15) | (OP_ADD << 12) | operand
    if mnemonic == "STA":
        # Opcode=3 (011), I=i_bit. Format: I | 011 | Addr
        return (i_bit << 15) | (OP_STA << 12) | operand
    if mnemonic == "HLT":
        # Opcode=7 (111), I=0, d_bits[0]=1. Hex: 7001
        return (OP_NON_IRM << 12) | 1
    return 0 # Invalid instruction becomes a NOP

class ProcessorHarness:
    """A helper class to manage interactions with the proc_base DUT."""

    def __init__(self, dut, clk):
        self.dut = dut
        self.clk = clk
        # Initialize all inputs
        self.dut.s_in.value = 0
        self.dut.inpr_data.value = 0
        self.dut.fgi_in.value = 0
        self.dut.fgo_in.value = 0

    async def reset(self):
        """Perform the reset sequence."""
        self.dut.reset_n.value = 0
        await RisingEdge(self.clk)
        await RisingEdge(self.clk)
        self.dut.reset_n.value = 1
        await RisingEdge(self.clk)
        self.dut._log.info("Processor reset.")

    async def start(self):
        """Press the 'start' button to begin execution."""
        self.dut.s_in.value = 1
        await RisingEdge(self.clk)
        self.dut.s_in.value = 0
        self.dut._log.info("Processor started.")

    async def load_program(self, program, base_addr=0):
        """
        Loads a program into the internal RAM using hierarchical paths.
        The program is a list of (address, data) tuples.
        """
        self.dut._log.info(f"Loading program into RAM at base address 0x{base_addr:X}...")
        for i, instruction in enumerate(program):
            # Accessing memory inside the DUT: dut -> main_ram (instance) -> mem (storage array)
            addr = base_addr + i
            self.dut.main_ram.mem[addr].value = instruction
            self.dut._log.info(f"  RAM[0x{addr:03X}] = 0x{instruction:04X}")

    async def read_ram(self, address):
        """Reads a value directly from the internal RAM for verification."""
        return self.dut.main_ram.mem[address].value


# =============================================================================
# Test Case
# =============================================================================

@cocotb.test()
async def test_run_simple_program(dut):
    """
    Test the full processor by running a simple program:
    1. LDA 0x100  (Load value_a into AC)
    2. ADD 0x101  (Add value_b to AC)
    3. STA 0x102  (Store result in memory)
    4. HLT       (Halt)
    """
    # --- Setup ---
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())
    harness = ProcessorHarness(dut, dut.clk)

    # --- Program and Data Definition ---
    prog_base_addr = 0x010
    data_addr_a    = 0x100
    data_addr_b    = 0x101
    result_addr    = 0x102
    
    value_a = 150
    value_b = 250
    expected_result = value_a + value_b

    # Assemble the program
    program_code = [
        assemble("LDA", data_addr_a),
        assemble("ADD", data_addr_b),
        assemble("STA", result_addr),
        assemble("HLT")
    ]
    
    # --- Test Execution ---
    await harness.reset()

    # Load program and initial data into RAM
    await harness.load_program(program_code, prog_base_addr)
    dut.main_ram.mem[data_addr_a].value = value_a
    dut.main_ram.mem[data_addr_b].value = value_b
    dut._log.info(f"RAM[0x{data_addr_a:X}] = {value_a}")
    dut._log.info(f"RAM[0x{data_addr_b:X}] = {value_b}")

    # Set the Program Counter to the start of our program.
    # We do this by forcing the internal pc_reg.
    dut.pc_reg.value = prog_base_addr
    dut._log.info(f"Manually setting PC to start at 0x{prog_base_addr:X}")
    
    await harness.start()

    # Wait for the program to execute.
    # Each instruction takes ~8 cycles (4 for fetch, 4 for execute).
    # 4 instructions * 8 cycles/instr = 32 cycles. We'll wait for 40 to be safe.
    dut._log.info("Waiting 40 cycles for program execution...")
    for _ in range(40):
        await RisingEdge(dut.clk)
        
    dut._log.info("Program execution finished. Verifying results.")

    # --- Verification ---
    # 1. Read the result from memory
    final_result = await harness.read_ram(result_addr)
    dut._log.info(f"Value at result address 0x{result_addr:X} is {final_result.integer}")
    
    assert final_result.integer == expected_result, \
        f"Program result incorrect! Expected {expected_result}, got {final_result.integer}"

    # 2. Check if the processor has halted
    # We can check the internal state of the 's_ff' in the control unit.
    s_ff_halted = dut.ctrl.s_ff.value
    assert s_ff_halted == 0, "Processor did not halt after HLT instruction."
    
    dut._log.info("Program result is correct and processor has halted.")
    dut._log.info("Top-level test PASSED.")
