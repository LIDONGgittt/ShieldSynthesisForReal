This archive contains the proof-of-concept implementation as well as all the 
input files to reproduce the experiments for the paper 

**Synthesizing 
Runtime Enforcer of Safety Specification under Burst Error [ [PDF](https://bitbucket.org/mengwu/shield-synthesis/src/3fd1604121c3/docs/?at=master) ]**. 

Instructions for reproducing the experiments can be found below. 
It is based on the tool developped by R. Bloem[1] in TACAS 15'

Installing the tool:
====================
So far, this tool has been tested on Linux systems only. In order to 
make it run, you need to:

 - Make sure you have Python installed
 - Download and install [PyCUDD][2] 
 - Add the directory in which you installed PyCUDD to your 
   LD_LIBRARY_PATH and PYTHONPATH environment variables. 
   On Bash-like shells you can do this by typing
   
   > `export PYTHONPATH=$PYTHONPATH:/path_to/pycudd2.0.2/pycudd`

   > `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/path_to/pycudd2.0.2/cudd-2.4.2/lib`
   
   In order to avoid setting these variables each time, you can also add these
   two lines to the file ~/.bashrc.
 
Running our synthesis tool:
===========================
 - Open a shell in the directory where you extracted this archive. 
 - If you only want to synthesize a shield from a safety specification, then
   executing

   > `> python ./shield.py path/to/spec_automaton.dfa`
   
   should be enough. You can also list several .dfa-files, then the tool
   automatically computes the product automaton. You can also add the option -f 
   to simplify the winning region computation by using implication:
   > `> python ./shield.py path/to/spec_automaton.dfa -f`

 - The safety specification automaton is defined with a very simple textual
   format. This format is described in the file docs/InputFormat.txt.

 - Example input files can be found in the directory 
   inputfiles/*

 - To run the old too by R. Bloem[1], use option -a ksalgo:

   > `> python ./shield.py path/to/spec_automaton.dfa -a ksalgo`

 - More usage of the tool, executing
 
   > `> python ./shield.py -h`
   
   to get a list of command-line arguments and more help messages.
 
Reproducing the results from the paper:
=======================================

  
Guarantee 1 2 and 3 of the ARM AMBA AHB bus controller:
-----------------------------------------------
- Execute 

  > `>python ./shield.py inputfiles/amba/amba_g1.dfa inputfiles/amba/amba_g2.dfa inputfiles/amba/amba_g3.dfa`
   
  to synthesize a shield for this example. The result will be written to the file output/amba_g1_amba_g2_amba_g3.v. An example output should be like:
  
```
************************************************
* Setup for Shield Synthesis:
** Output File in Verilog Format
** Used Synthesis Algorithm: Burst Error Algorithm
** Use standard algorithm to compute winning region
** Used specification automaton input files:
*** inputfiles/amba/amba_g1.dfa
*** inputfiles/amba/amba_g2.dfa
*** inputfiles/amba/amba_g3.dfa
************************************************

******************************************
*** ET Automaton Construction time: 0.05
*** ET Automaton Size: 22/260
*** Final Spec Automaton:
***     num states: 12
***     num edges: 131
***     num inputs: 4
***     num outputs: 2
*** Total execution time: 0.11
*** Num wining states: 22/528
******************************************
```
Specification patterns by Dwyer et al:
--------------------------------------
- Here, we executed our tool on the first 10 specification from

  [http://patterns.projects.cis.ksu.edu/documentation/patterns/ltl.shtml]()

- The input files can be found in the directory:
    inputfiles/ltl/

- Execute

  > `> python ./shield.py inputfiles/ltl/some.dfa [-f]`
  
   
  to synthesize a shield for the respective property.
  If the dfa-name ends with a number, then this number indicates the 
  liveness-to-safety bound that has been used for transforming the property into
  a pure safety specification. See the comments in the dfa-file and the paper
  for a more detailed explanation.
  As usual, the resulting Verilog code will be written into the file 
  output/some.v

Any questions? Do not hesistate to contact the authors of the paper.

Have fun!

[1] R. Bloem, B. K¨onighofer, R. K¨onighofer, and C. Wang. Shield synthesis: Runtime enforcement
for reactive systems. In International Conference on Tools and Algorithms for Construction
and Analysis of Systems. Springer, 2015.

[2]: http://bears.ece.ucsb.edu/pycudd.html
