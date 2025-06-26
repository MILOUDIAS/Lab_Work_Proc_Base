//=============================================================================
// 5. Top-level Processor Module (Proc_base)
//=============================================================================
// This module connects all the individual components together structurally.
module proc_base(
    input  logic clk,
    input  logic reset_n,
    input  logic s_in, // Start button
    // I/O Ports
    input  logic [7:0] inpr_data,
    output logic [7:0] outr_data,
    input  logic       fgi_in, // Input flag
    input  logic       fgo_in  // Output flag
);

    import definitions_pkg::*;

    // --- Control Signals ---
    logic [49:1] F; // Control word from Control Unit

    // --- Register Declarations ---
    logic [ADDR_WIDTH-1:0] pc_reg;
    logic [ADDR_WIDTH-1:0] mar_reg;
    logic [DATA_WIDTH-1:0] mdr_reg;
    logic [DATA_WIDTH-1:0] ir_reg;
    logic [DATA_WIDTH-1:0] ac_reg;
    logic                  e_reg;
    logic [IO_WIDTH-1:0]   outr_reg;
    logic                  fgi_ff, fgo_ff;

    // --- Data Path Wires ---
    logic [DATA_WIDTH-1:0] ram_data_out;
    logic [DATA_WIDTH-1:0] alu_result;
    logic                  alu_carry_out;
    logic [DATA_WIDTH-1:0] ac_mux_out;
    logic [ADDR_WIDTH-1:0] mar_mux_out;
    logic [DATA_WIDTH-1:0] mdr_mux_out;

    // --- Status Flags ---
    logic ac_is_zero, ac_is_neg, e_is_zero, mdr_is_zero;

    assign ac_is_zero = (ac_reg == 0);
    assign ac_is_neg  = ac_reg[DATA_WIDTH-1];
    assign e_is_zero  = (e_reg == 0);
    assign mdr_is_zero = (mdr_reg == 0);
    assign outr_data = outr_reg;


    //=================================================
    // Sub-module Instantiations
    //=================================================

    // --- Control Unit ---
    control_unit ctrl (
        .clk(clk),
        .reset_n(reset_n),
        .op_code(ir_reg[14:12]),
        .i_bit(ir_reg[15]),
        .d_bits(ir_reg[11:0]),
        .ac_is_zero(ac_is_zero),
        .ac_is_neg(ac_is_neg),
        .e_is_zero(e_is_zero),
        .fgi(fgi_ff),
        .fgo(fgo_ff),
        .mdr_is_zero(mdr_is_zero),
        .s_in(s_in),
        .control_word(F)
    );

    // --- RAM ---
    ram main_ram (
        .clk(clk),
        .addr(mar_reg),
        .data_in(mdr_reg),
        .wr_en(F[22] | F[25] | F[30]), // Controlled by STA, BSA, ISZ
        .rd_en(F[2] | F[7] | F[11] | F[15] | F[18] | F[28] | F[48]), // Controlled by Fetch, Indirect, IRM loads, LDI
        .data_out(ram_data_out)
    );

    // --- ALU ---
    alu main_alu (
        .a(ac_reg),
        .b(mdr_reg),
        .alu_op(
            (F[12]) ? ALU_AND :
            (F[16]) ? ALU_ADD :
            (F[19]) ? ALU_TRANSFER :
            (F[31]) ? ALU_CLA :
            (F[33]) ? ALU_CMA :
            (F[37]) ? ALU_INC :
            ALU_TRANSFER // Default
        ),
        .result(alu_result),
        .carry_out(alu_carry_out)
    );


    //=================================================
    // Data Path Logic (Registers and Muxes)
    //=================================================

    // --- Program Counter (PC) ---
    always_ff @(posedge clk) begin
        if (F[23] | F[24]) pc_reg <= mdr_reg[ADDR_WIDTH-1:0]; // BIN, BSA
        else if (F[2] | F[26] | F[30] & mdr_is_zero | F[38] | F[39] | F[40] | F[41] | F[45] | F[46] | F[48])
            pc_reg <= pc_reg + 1; // Increment
    end

    // --- Memory Address Register (MAR) ---
    // Source Mux for MAR
    always_comb begin
        // S1 S0 | Source
        //  0  0 | MDR
        //  0  1 | PC
        //  1  0 | IR
        //  1  1 | --
        case ({F[6], F[1]}) // S0=F6, S1=F1 (pg 26)
            2'b01: mar_mux_out = pc_reg;
            2'b10: mar_mux_out = ir_reg[ADDR_WIDTH-1:0];
            default: mar_mux_out = mdr_reg[ADDR_WIDTH-1:0];
        endcase
    end
    always_ff @(posedge clk) begin
        // Load MAR is the OR of all functions that write to it
        if (F[1] | F[6] | F[10] | F[14] | F[17] | F[20] | F[24] | F[27] | F[47]) begin
            mar_reg <= mar_mux_out;
        end
    end

    // --- Memory Data Register (MDR) ---
    // Source Mux for MDR
    always_comb begin
        if (F[21]) mdr_mux_out = ac_reg;        // STA: MDR <- AC
        else if (F[24]) mdr_mux_out = {4'b0, pc_reg}; // BSA: MDR <- PC
        else mdr_mux_out = ram_data_out;      // Default: MDR <- RAM
    end
    always_ff @(posedge clk) begin
        if (F[2] | F[7] | F[11] | F[15] | F[18] | F[21] | F[24] | F[28] | F[48]) begin
            mdr_reg <= mdr_mux_out;
        end else if (F[29]) begin // ISZ
            mdr_reg <= mdr_reg + 1;
        end
    end

    // --- Instruction Register (IR) ---
    always_ff @(posedge clk) begin
        if (F[3]) ir_reg <= mdr_reg; // Load IR
    end

    // --- Accumulator (AC) and E flag ---
    // Source Mux for AC
    assign ac_mux_out = F[43] ? {ac_reg[15:8], inpr_data} : alu_result;

    always_ff @(posedge clk) begin
        // Load AC
        if (F[12] | F[16] | F[19] | F[31] | F[33] | F[37] | F[43] | F[49]) begin
            ac_reg <= ac_mux_out;
        end
        // CIR/CIL logic
        else if (F[35]) ac_reg <= {e_reg, ac_reg[15:1]}; // CIR
        else if (F[36]) ac_reg <= {ac_reg[14:0], e_reg}; // CIL

        // E flag logic
        if (F[32]) e_reg <= 1'b0; // CLE
        else if (F[34]) e_reg <= ~e_reg; // CME
        else if (F[16] | F[37]) e_reg <= alu_carry_out; // ADD, INC
    end

    // --- I/O Registers and Flags ---
    always_ff @(posedge clk) begin
        // OUTR
        if (F[44]) outr_reg <= ac_reg[IO_WIDTH-1:0];

        // FGI Flag
        if (fgi_in) fgi_ff <= 1'b1; // Set by peripheral
        else if (F[43]) fgi_ff <= 1'b0; // Cleared by INP

        // FGO Flag
        if (F[44]) fgo_ff <= 1'b1; // Set by OUT
        else if (fgo_in) fgo_ff <= 1'b0; // Cleared by peripheral
    end

endmodule : proc_base