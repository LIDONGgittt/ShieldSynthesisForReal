/* Written by Tom Shiple, 25 October 1995 */

/* Symbolic variables */
//typedef enum {YES, NO} boolean;
//typedef enum {START, SHORT, LONG} timer_state;
//typedef enum {GREEN, YELLOW, RED} color;
// my verilog simulator does not like typedefs
`define YES 1
`define NO 0
`define START 0 
`define SHORT 1
`define LONG  2
`define GREEN    2'b00
`define TRAN_RED 2'b01
`define RED      2'b11

`timescale 1ns / 100ps

module design (clk, 
            car_present,
            emergeny,
            farm_light,
            hwy_light);
  input clk;
  input car_present;
  input emergeny;
  output farm_light;
  output hwy_light;

  wire start_timer, short_timer, long_timer;
  wire enable_farm, farm_start_timer, enable_hwy, hwy_start_timer;
  wire raw_farm_light;
  wire raw_hwy_light;

  assign start_timer = farm_start_timer || hwy_start_timer;
  assign farm_light = emergeny ? 1 : raw_farm_light;
  assign hwy_light = emergeny ? 1 : raw_hwy_light;

  timer timer(clk, 
              start_timer, 
              short_timer, 
              long_timer);
  farm_control farm_control(clk, 
                            car_present, 
                            enable_farm, 
                            short_timer,
                            long_timer,
                            raw_farm_light, 
                            farm_start_timer, 
                            enable_hwy);
  hwy_control hwy_control (clk, 
                          car_present, 
                          enable_hwy,  
                          short_timer,
                          long_timer,
                          raw_hwy_light, 
                          hwy_start_timer, 
                          enable_farm);
endmodule

module timer(clk, 
             start, 
             short, 
             long);
  input clk;
  input start;
  output short;
  output long;

  wire rand_choice;
  wire start, short, long;
  reg [1:0] state;

  initial state = `START;
  assign rand_choice = 1;//$ND(0,1);

  /* short could as well be assigned to be just (state == SHORT) */
  assign short = ((state == `SHORT) || (state == `LONG));
  assign long  = (state == `LONG);

  always @(posedge clk) 
    begin
      if (start) 
        state = `START;
      else 
          begin
          case (state)
          `START: 
                  if (rand_choice == 1) state = `SHORT;
          `SHORT: 
                  if (rand_choice == 1) state = `LONG;
                  /* if LONG, remains LONG until start signal received */
          endcase
          end
  end
endmodule

module farm_control(clk, 
                    car_present, 
                    enable_farm, 
                    short_timer, 
                    long_timer,
                    farm_light, 
                    farm_start_timer, 
                    enable_hwy);
  input clk;
  input car_present;
  input enable_farm;
  input short_timer;
  input long_timer;
  output farm_light;
  output farm_start_timer;
  output enable_hwy;

  wire car_present;
  wire short_timer, long_timer;
  wire farm_start_timer;
  wire enable_hwy;
  wire enable_farm;
  reg [1:0] farm_state;

  initial farm_state = `RED;
  assign farm_start_timer = (((farm_state == `GREEN) && ((car_present == `NO) || long_timer)) 
                            || (farm_state == `RED) && enable_farm);
  assign enable_hwy = ((farm_state == `TRAN_RED) && short_timer);
  assign farm_light = farm_state[0:0];

  always @(posedge clk) begin
      case (farm_state)
      `GREEN:
              if ((car_present == `NO) || long_timer) farm_state = `TRAN_RED;
      `TRAN_RED:
              if (short_timer) farm_state = `RED;
      `RED:
              if (enable_farm) farm_state = `GREEN;
      endcase
  end
endmodule

module hwy_control(clk, 
                   car_present, 
                   enable_hwy, 
                   short_timer, 
                   long_timer,
                   hwy_light, 
                   hwy_start_timer, 
                   enable_farm);
  input clk;
  input car_present;
  input enable_hwy;
  input short_timer;
  input long_timer;
  output hwy_light;
  output hwy_start_timer;
  output enable_farm;

  wire car_present;
  wire short_timer, long_timer;
  wire hwy_start_timer;
  wire enable_farm;
  wire enable_hwy;
  reg [1:0] hwy_state;

  initial hwy_state = `GREEN;
  assign hwy_start_timer = (((hwy_state == `GREEN) && ((car_present  == `YES) && long_timer))
                           || (hwy_state == `RED) && enable_hwy);
  assign enable_farm = ((hwy_state == `TRAN_RED) && short_timer);
  assign hwy_light = hwy_state[0:0];

  always @(posedge clk) begin
      case (hwy_state)
      `GREEN:
              if ((car_present == `YES) && long_timer) hwy_state = `TRAN_RED;
      `TRAN_RED:
              if (short_timer) hwy_state = `RED;
      `RED:
              if (enable_hwy) hwy_state = `GREEN;
      endcase
  end
endmodule
