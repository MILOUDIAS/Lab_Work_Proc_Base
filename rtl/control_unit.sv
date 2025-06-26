
//=============================================================================
// Control Unit Module
//=============================================================================
// This is the brain of the CPU. It generates all control signals (F1-F49)
// based on the current instruction and the processor's state.
module control_unit (
    input  logic        clk,
    input  logic        reset_n,

    // Inputs from Instruction Register (IR)
    input  logic [2:0]  op_code,      // IR[14:12]
    input  logic        i_bit,        // IR[15]
    input  logic [11:0] d_bits,       // IR[11:0]

    // Status Flag Inputs
    input  logic        ac_is_zero,
    input  logic        ac_is_neg,
    input  logic        e_is_zero,
    input  logic        fgi,
    input  logic        fgo,
    input  logic        mdr_is_zero,
    input  logic        s_in,         // Start/Stop button

    // Outputs: Control Signals F1-F49
    output logic [49:1] control_word
);
    import definitions_pkg::*;

    // --- State Variables ---
    logic [1:0]  cycle;         // Current FSM cycle (C0, C1, C2)
    logic [3:0]  t_step_cnt;    // Timing counter for T0-T3
    logic [2:0]  q;             // Decoded opcode (q0-q7)

    // --- Internal Signals ---
    logic        is_irm, is_irr, is_ies;
    logic [3:0]  t; // One-hot timing signals T0-T3

    // State flip-flops F and R, and timing counter
    logic f_ff, r_ff; // F and R flip-flops to determine the cycle
    logic s_ff;       // Start/Stop flip-flop

    assign cycle = {f_ff, r_ff};
    assign q = op_code;

    // Generate timing signals T0, T1, T2, T3
    assign t[0] = (t_step_cnt == 4'd0);
    assign t[1] = (t_step_cnt == 4'd1);
    assign t[2] = (t_step_cnt == 4'd2);
    assign t[3] = (t_step_cnt == 4'd3);

    // Instruction type decoding
    assign is_irm = (q != OP_NON_IRM);
    assign is_irr = (q == OP_NON_IRM) && (i_bit == 1'b0);
    assign is_ies = (q == OP_NON_IRM) && (i_bit == 1'b1);

    // --- Sequential Logic for State and Timing ---
    always_ff @(posedge clk or negedge reset_n) begin
        if (!reset_n) begin
            t_step_cnt <= 4'd0;
            f_ff <= 1'b0;
            r_ff <= 1'b0;
            s_ff <= 1'b0;
        end else begin
            // S flip-flop logic (start/stop)
            if (s_in) s_ff <= 1'b1; // Manual start
            else if (is_irr && d_bits[0] && cycle == CYCLE_EXECUTE && t[0]) s_ff <= 1'b0; // HLT instruction

            if (s_ff) begin // Processor is running
                // Timing counter: resets every 4 clocks
                if (t_step_cnt == 4'd3) begin
                    t_step_cnt <= 4'd0;
                end else begin
                    t_step_cnt <= t_step_cnt + 1;
                end

                // FSM cycle transitions (at T3)
                if (t[3]) begin
                    case (cycle)
                        CYCLE_FETCH: begin
                            if (is_irm && i_bit) begin // IRM Indirect
                                f_ff <= 1'b0;
                                r_ff <= 1'b1; // -> Indirect Cycle
                            end else begin
                                f_ff <= 1'b1;
                                r_ff <= 1'b0; // -> Execute Cycle
                            end
                        end
                        CYCLE_INDIRECT: begin
                            f_ff <= 1'b1;
                            r_ff <= 1'b0; // -> Execute Cycle
                        end
                        CYCLE_EXECUTE: begin
                            f_ff <= 1'b0;
                            r_ff <= 1'b0; // -> Fetch Cycle
                        end
                        default: begin // Should not happen
                            f_ff <= 1'b0;
                            r_ff <= 1'b0;
                        end
                    endcase
                end
            end else begin // Processor is halted
                t_step_cnt <= 4'd0;
            end
        end
    end

    // --- Combinational Logic to Generate Control Word ---
    logic [49:1] f_signals;
    always_comb begin
        f_signals = '0; // Default all signals to inactive

        if(s_ff) begin // Processor must be running
            // --- Cycle: FETCH ---
            if (cycle == CYCLE_FETCH) begin
                if (t[0]) f_signals[1]  = 1; // F1: MAR <- PC
                if (t[1]) f_signals[2]  = 1; // F2: MDR <- M(MAR), PC++
                if (t[2]) f_signals[3]  = 1; // F3: IR <- MDR
                if (t[3]) begin
                    if (is_irm && i_bit) f_signals[4] = 1; // F4: R <- 1 (Go to Indirect)
                    else                 f_signals[5] = 1; // F5: F <- 1 (Go to Execute)
                end
            end

            // --- Cycle: INDIRECT ---
            if (cycle == CYCLE_INDIRECT) begin
                if (t[0]) f_signals[6] = 1; // F6: MAR <- IR[ADR]
                if (t[1]) f_signals[7] = 1; // F7: MDR <- M(MAR)
                // t2 is NOP
                if (t[3]) f_signals[9] = 1; // F9: F <- 1, R <- 0 (Go to Execute)
            end

            // --- Cycle: EXECUTE ---
            if (cycle == CYCLE_EXECUTE) begin
                // F13: F <- 0 (Return to Fetch) is common for all IRM at t3
                if (is_irm) begin
                     if (t[3]) f_signals[13] = 1;
                end

                // IRM Instructions
                case (q)
                    OP_AND: begin
                        if (t[0]) f_signals[10] = 1; // MAR <- MDR[ADR]
                        if (t[1]) f_signals[11] = 1; // MDR <- M(MAR)
                        if (t[2]) f_signals[12] = 1; // AC <- AC AND MDR
                    end
                    OP_ADD: begin
                        if (t[0]) f_signals[14] = 1; // MAR <- MDR[ADR]
                        if (t[1]) f_signals[15] = 1; // MDR <- M(MAR)
                        if (t[2]) f_signals[16] = 1; // AC <- AC + MDR
                    end
                    OP_LDA: begin
                        if (t[0]) f_signals[17] = 1; // MAR <- MDR[ADR]
                        if (t[1]) f_signals[18] = 1; // MDR <- M(MAR)
                        if (t[2]) f_signals[19] = 1; // AC <- MDR
                    end
                    OP_STA: begin
                        if (t[0]) f_signals[20] = 1; // MAR <- MDR[ADR]
                        if (t[1]) f_signals[21] = 1; // MDR <- AC
                        if (t[2]) f_signals[22] = 1; // M(MAR) <- MDR
                    end
                    OP_BIN: begin
                        if (t[0]) f_signals[23] = 1; // PC <- MDR[ADR]
                    end
                    OP_BSA: begin
                        if (t[0]) f_signals[24] = 1; // MAR<-MDR[A], MDR[A]<-PC, PC<-MDR[A]
                        if (t[1]) f_signals[25] = 1; // M(MAR) <- MDR
                        if (t[2]) f_signals[26] = 1; // PC++
                    end
                    OP_ISZ: begin
                        if (t[0]) f_signals[27] = 1; // MAR <- MDR[ADR]
                        if (t[1]) f_signals[28] = 1; // MDR <- M(MAR)
                        if (t[2]) f_signals[29] = 1; // MDR <- MDR + 1
                        if (t[3]) f_signals[30] = 1; // M(MAR)<-MDR, if(MDR==0) PC++
                    end
                    OP_NON_IRM: begin
                        if(t[0]) begin // All IRR/IES are single-cycle at T0
                            if(is_irr) begin // IRR instructions
                                if (d_bits[11]) f_signals[31] = 1; // CLA
                                if (d_bits[10]) f_signals[32] = 1; // CLE
                                if (d_bits[9])  f_signals[33] = 1; // CMA
                                if (d_bits[8])  f_signals[34] = 1; // CME
                                if (d_bits[7])  f_signals[35] = 1; // CIR
                                if (d_bits[6])  f_signals[36] = 1; // CIL
                                if (d_bits[5])  f_signals[37] = 1; // INC
                                if (d_bits[4] && !ac_is_neg)  f_signals[38] = 1; // SPA
                                if (d_bits[3] && ac_is_neg)   f_signals[39] = 1; // SNA
                                if (d_bits[2] && ac_is_zero)  f_signals[40] = 1; // SZA
                                if (d_bits[1] && e_is_zero)   f_signals[41] = 1; // SZE
                                if (d_bits[0])                f_signals[42] = 1; // HLT
                            end
                            else if(is_ies) begin // IES instructions
                                if (d_bits[11]) f_signals[43] = 1; // INP
                                if (d_bits[10]) f_signals[44] = 1; // OUT
                                if (d_bits[9] && fgi)   f_signals[45] = 1; // SFI
                                if (d_bits[8] && fgo)   f_signals[46] = 1; // SFO
                                // LDI is special
                                if (d_bits[7]) begin
                                    // It uses the EXECUTE cycle differently
                                    // F47-F49 are for LDI
                                    // Simplified logic: treat as multi-step within one cycle
                                end
                            end
                        end
                        // LDI is a 2-word instruction. Full implementation is complex.
                        // Here we use F47-49 as defined in the table.
                        if (is_ies && d_bits[7]) begin // LDI
                           if (t[0]) f_signals[47] = 1; // MAR <- PC
                           if (t[1]) f_signals[48] = 1; // MDR <- M(MAR), PC++
                           if (t[2]) f_signals[49] = 1; // AC <- MDR
                        end
                    end
                endcase
            end
        end
    end

    assign control_word = f_signals;

endmodule : control_unit
