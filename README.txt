This archive contains the proof-of-concept implementation as well as all the 
input files to reproduce the experiments for the TACAS'15 paper 'Shield 
Synthesis: Runtime Enforcement for Reactive Systems'. Instructions for 
reproducing the experiments can be found below.


Installing the tool:
====================
So far, this tool has been tested on Linux systems only. In order to 
make it run, you need to:
 - Make sure you have Python installed
 - Download and install PyCUDD [1] 
 - Add the directory in which you installed PyCUDD to your 
   LD_LIBRARY_PATH and PYTHONPATH environment variables. On Bash-like
   shells you can do this by typing
   export PYTHONPATH=$PYTHONPATH:/path_to/pycudd2.0.2/pycudd
   export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/path_to/pycudd2.0.2/cudd-2.4.2/lib
   In order to avoid setting these variables each time, you can also add these
   two lines to the file ~/.bashrc.
 - If you would also like to model-check synthesized shiedls, you should
   install the model-checkers NuSMV [2] and/or VIS [3]. However, these tools
   are only called as external processes. You can still use the synthesis tool
   without these model checkers.
 - If you would also like to optimize shield-circuits in a post-processing step,
   you need to download and install ABC [4].
 
Running our synthesis tool:
===========================
 - Open a shell in the directory where you extracted this archive. 
 - Execute
    > python ./shield.py -h
   to get a list of command-line arguments.
 - If you only want to synthesize a shield from a safety specification, then
   executing
    > python ./shield.py path/to/spec_automaton.dfa
   should be enough. You can also list several .dfa-files, then the tool
   automatically computes the product automaton. For automatically composing 
   the shield with a design or model checkig it, refer to the help-text of the
   command line parameters (printed with option -h).
 - The safety specification automaton is defined with a very simple textual
   format. This format is described in the file docs/InputFormat.txt.
 - Example input files can be found in the directory 
   inputfiles/specs/automata/*
 - Not every option is available from command-line parameters. Some parameters
   are also defined as constants in the python files. E.g.,
    - MAX_DEVIATIONS in shield.py defines the maximum k that is tried
    - DEBUG in shield.py (and many other files) is a flag that allows you to
      get intermediate results and other debug output printed.

Reproducing the results from the paper:
=======================================

Traffic light controller:
-------------------------
- Execute
   > python ./shield.py -e verilog inputfiles/specs/automata/traffic/traffic_1_timebug.dfa
  to synthesize a shield for this example in Verilog format. The result will be
  written to the file output/traffic_1_timebug.v
- To optimize the shield further (regarding circuit size), execute the command
   > ./optimize_verilog_with_abc.sh ./output/traffic_1_timebug.v
  You should see output like:
  shield       : i/o =    3/    2  lat =    5  and =     41  lev =  7
  (which means: 5 latches, 41 AIG gates)
- To simulate the behavior of the shield together with a faulty version of the
  design from the VIS user manual, execute either:
   > veriwell ./simulation/traffic_1_timebug_sim.v
  or
   > iverilog ./simulation/traffic_1_timebug_sim.v
   > ./a.out
  depending on your favourite verilog simulator.
  You should get output like this:
    Time =   1, emergency=0, car=0, farmS=r, hwS=G, farmD=r, hwD=G 
    Time =  11, timer_state=short
    Time =  11, emergency=1, car=1, farmS=r, hwS=R, farmD=r, hwD=R 
    Time =  21, timer_state= long
    Time =  21, emergency=0, car=1, farmS=r, hwS=G, farmD=r, hwD=G 
    Time =  31, timer_state=start
    Time =  31, emergency=0, car=1, farmS=r, hwS=R, farmD=r, hwD=R 
    Time =  41, timer_state=short
    Time =  41, emergency=0, car=1, farmS=r, hwS=R, farmD=r, hwD=R 
    Time =  51, timer_state=start
    Time =  51, emergency=0, car=1, farmS=g, hwS=R, farmD=g, hwD=R 
    Time =  61, timer_state=short
    Time =  61, emergency=0, car=0, farmS=g, hwS=R, farmD=g, hwD=R 
    Time =  71, timer_state=start
    Time =  71, emergency=0, car=0, farmS=r, hwS=R, farmD=r, hwD=G 
    Time =  81, timer_state=short
    Time =  81, emergency=0, car=1, farmS=r, hwS=G, farmD=r, hwD=G 
    Time =  91, timer_state= long
    Time =  91, emergency=0, car=1, farmS=r, hwS=G, farmD=r, hwD=G 
    Time = 101, timer_state=start
    Time = 101, emergency=0, car=0, farmS=r, hwS=R, farmD=r, hwD=R 
    Time = 111, timer_state=short
    Time = 111, emergency=0, car=0, farmS=r, hwS=R, farmD=r, hwD=R 
    Time = 121, timer_state=start
    Time = 121, emergency=1, car=0, farmS=r, hwS=R, farmD=g, hwD=R 
    Time = 131, timer_state=start
    Time = 131, emergency=0, car=0, farmS=r, hwS=R, farmD=r, hwD=R 
    Time = 141, timer_state=short
    Time = 141, emergency=0, car=0, farmS=r, hwS=R, farmD=r, hwD=R 
  This is the simulation trace you can find in the paper.
- The graph summarizing the behavior of the final shield has been constructed
  as explained in the file 'traffic_solution_graph.txt'
- A spec for the properties 1 and 2 only (without property 3) can be
  found in the file 'inputfiles/specs/automata/traffic/prop1and2.dfa'.
  The synthesis result is in 'output/prop1and2.v'. This shield
  implementation contains a few latches, but none of them is used.
  Optimization with ABC gives:
  shield       : i/o =    3/    2  lat =    0  and =      3  lev =  2
  i.e., the shield is purely combinational, and has 3 AND gates.
  If we would allow AND gates with negated inputs, we would probably
  get a solution with only 2 AND gates.
- Simulating this shield implementation gives the following truth table:  
  phf    h'f'
  -----------
  0Gg -> G r
  0Gr -> G r
  0Rg -> R g
  0Rr -> R r
  1Gg -> R r
  1Gr -> R r
  1Rg -> R r
  1Rr -> R r

  
  
Guarantee 3 of the ARM AMBA AHB bus controller:
-----------------------------------------------
- Execute
   > python ./shield.py -e verilog inputfiles/specs/automata/amba02/amba_g3.dfa
  to synthesize a shield for this example in Verilog format. The result will be
  written to the file output/amba_g3.v
- To optimize the shield further (regarding circuit size), execute the command
   > ./optimize_verilog_with_abc.sh ./output/amba_g3.v
  You should see output like:
  shield       : i/o =    5/    2  lat =    4  and =     77  lev = 10
  (which means: 4 latches, 77 AIG gates)  
- To simulate the behavior of the shield together with a faulty version of the
  design (synthesized automatically from a faulty specification with the RATSY
  tool):
   > veriwell ./simulation/amba_g3_burst4bug.v
  or
   > iverilog ./simulation/amba_g3_burst4bug.v
   > ./a.out
  depending on your favourite verilog simulator.
  You should get output like this:
    Time =    1, B=0, s=0, R=1, shield_s=0
    Time =   11, B=0, s=0, R=1, shield_s=0
    Time =   21, B=0, s=0, R=1, shield_s=0
    Time =   31, B=1, s=1, R=0, shield_s=1
    Time =   41, B=1, s=0, R=1, shield_s=0
    Time =   51, B=1, s=0, R=1, shield_s=0
    Time =   61, B=1, s=0, R=1, shield_s=0
    Time =   71, B=1, s=1, R=1, shield_s=0
    Time =   81, B=1, s=0, R=1, shield_s=0
    Time =   91, B=1, s=0, R=1, shield_s=0
    Time =  101, B=1, s=0, R=1, shield_s=0
    Time =  111, B=1, s=0, R=1, shield_s=0
    Time =  121, B=1, s=0, R=1, shield_s=0
    Time =  131, B=1, s=0, R=1, shield_s=0
    Time =  141, B=1, s=0, R=1, shield_s=0
    Time =  151, B=1, s=1, R=1, shield_s=1
    Time =  161, B=1, s=0, R=1, shield_s=0
    Time =  171, B=1, s=0, R=1, shield_s=0
    Time =  181, B=1, s=0, R=1, shield_s=0
  This is the simulation trace you can find in the paper.

Specification patterns by Dwyer et al:
--------------------------------------
- Here, we executed our tool on the first 10 specification from
  http://patterns.projects.cis.ksu.edu/documentation/patterns/ltl.shtml
- The input files can be found in the directory:
    inputfiles/specs/automata/pattern_mappings/
- Execute
   > python ./shield.py -e verilog inputfiles/specs/automata/pattern_mappings/some.dfa
  to synthesize a shield for the respective property.
  If the dfa-name ends with a number, then this number indicates the 
  liveness-to-safety bound that has been used for transforming the property into
  a pure safety specification. See the comments in the dfa-file and the paper
  for a more detailed explanation.
  As usual, the resulting Verilog code will be written into the file 
  output/some.v
- Execute  
   > ./optimize_verilog_with_abc.sh ./output/some.v
  to optimize the resulting file with ABC.
- The results of our run can be found in the file pattern_results.txt.

Any questions? Do not hesistate to contact the authors of the paper.

Have fun!

[1] http://bears.ece.ucsb.edu/pycudd.html
[2] http://nusmv.fbk.eu/
[3] http://vlsi.colorado.edu/~vis/
[4] http://www.eecs.berkeley.edu/~alanmi/abc/