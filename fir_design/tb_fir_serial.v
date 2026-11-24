// tb_fir_serial.v - feeds stim.mem through fir_serial for one coefficient set
// and writes each output sample (decimal) to the file named by +OUT=...
// Run: vvp sim +SET=<0..3> +OUT=out_set0.txt
`timescale 1ns/1ps
module tb_fir_serial;
    localparam integer NSAMP  = 1200;
    localparam integer PERIOD = 400;   // clocks between samples (real design: ~2083)

    reg clk = 0, rst = 1, in_valid = 0;
    reg signed [15:0] in_sample = 0;
    reg [1:0] set_sel = 0;
    wire out_valid, busy;
    wire signed [15:0] out_sample;

    reg [15:0] stim [0:NSAMP-1];
    integer set_arg, fd, n, outs;
    reg [8*64-1:0] out_name;

    fir_serial dut (.clk(clk), .rst(rst), .in_valid(in_valid), .in_sample(in_sample),
                    .set_sel(set_sel), .out_valid(out_valid), .out_sample(out_sample),
                    .busy(busy));

    always #5 clk = ~clk;   // 100 MHz

    always @(posedge clk) if (out_valid) begin
        $fdisplay(fd, "%0d", out_sample);
        outs = outs + 1;
    end

    initial begin
        if (!$value$plusargs("SET=%d", set_arg)) set_arg = 0;
        if (!$value$plusargs("OUT=%s", out_name)) out_name = "out.txt";
        $readmemh("stim.mem", stim);
        fd = $fopen(out_name, "w");
        outs = 0;
        set_sel = set_arg;
        repeat (4) @(posedge clk);
        rst = 0;
        for (n = 0; n < NSAMP; n = n + 1) begin
            @(posedge clk);
            in_sample <= stim[n];
            in_valid  <= 1'b1;
            @(posedge clk);
            in_valid  <= 1'b0;
            repeat (PERIOD - 2) @(posedge clk);
        end
        repeat (PERIOD) @(posedge clk);
        $fclose(fd);
        $display("set %0d: %0d outputs", set_arg, outs);
        $finish;
    end
endmodule
