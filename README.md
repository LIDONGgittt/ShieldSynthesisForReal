This archive contains the proof-of-concept implementation as well as all the 
input files to reproduce the experiments for the paper 

**Synthesizing 
Shield Synthesis for Real: Enforcing Safety in Cyber-Physical Systems(FMCAD 2019) [ [PDF](./docs/WuWDW19.pdf) ]**. 

Instructions for reproducing the experiments can be found below. 
It is based on the tool developped by R. Bloem[^1] in TACAS 15'

Installing the tool:
====================
So far, this tool has been tested on Linux systems only. In order to 
make it run, you need to:

 - Make sure you have Python installed
 - Download and install [PyCUDD](http://bears.ece.ucsb.edu/pycudd.html) 
 - Add the directory in which you installed PyCUDD to your 
   LD_LIBRARY_PATH and PYTHONPATH environment variables. 
   On Bash-like shells you can do this by typing
   
   >> `export PYTHONPATH=$PYTHONPATH:/path_to/pycudd2.0.2/pycudd`

   >> `export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/path_to/pycudd2.0.2/cudd-2.4.2/lib`
   
   In order to avoid setting these variables each time, you can also add these
   two lines to the file ~/.bashrc.
 
Running our synthesis tool:
===========================
 - Open a shell in the directory where you extracted this archive. 
 - If you only want to synthesize a shield from a safety specification, then
   executing

   >> `> python ./shield.py -a realgo path/to/spec_automaton.dfa`
   
   should be enough. You can also list several .dfa-files, then the tool
   automatically computes the product automaton. 

 - The safety specification automaton is defined with a very simple textual
   format. This format is described in the file docs/InputFormat.txt.

 - Example input files can be found in the directory inputfiles/*

 - Some template files for generating shield using c language are also presented in inputfiles/, changes to them are not recommended.

 - To run the old tool by R. Bloem[^1], use option -a ksalgo, or run the previous NFM2016 tool[^2] use option -a bealgo

 - More usage of the tool, executing
 
   >> `> python ./shield.py -h`
   
   to get a list of command-line arguments and more help messages.
 
Reproducing the results from the paper:
=======================================
simply use our script `> ./real_test.sh` 

TBD: the input data and runtime evaluation for synthesized shield program is under preparation!
  

Any questions? Do not hesistate to contact the authors of the paper.

Have fun!


[^1]: R. Bloem, B. K¨onighofer, R. K¨onighofer, and C. Wang. Shield synthesis: Runtime enforcement
for reactive systems. In International Conference on Tools and Algorithms for Construction
and Analysis of Systems. Springer, 2015.

[^2]: Wu M, Zeng H, Wang C. Synthesizing runtime enforcer of safety properties under burst error[C]//NASA Formal Methods Symposium. Springer, Cham, 2016: 65-81. 
