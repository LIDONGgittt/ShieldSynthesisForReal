echo "AMBA Benchmarks:\n"
echo "================================================\n"
python shield.py -f inputfiles/amba/amba_g1.dfa inputfiles/amba/amba_g2.dfa inputfiles/amba/amba_g3.dfa
python shield.py -f inputfiles/amba/amba_g1.dfa inputfiles/amba/amba_g2.dfa inputfiles/amba/amba_g4.dfa
python shield.py -f inputfiles/amba/amba_g1.dfa inputfiles/amba/amba_g3.dfa inputfiles/amba/amba_g4.dfa
python shield.py -f inputfiles/amba/amba_g1.dfa inputfiles/amba/amba_g2.dfa inputfiles/amba/amba_g3.dfa inputfiles/amba/amba_g5.dfa
python shield.py -f inputfiles/amba/amba_g1.dfa inputfiles/amba/amba_g2.dfa inputfiles/amba/amba_g4.dfa inputfiles/amba/amba_g5.dfa
python shield.py -f inputfiles/amba/amba_g4.dfa inputfiles/amba/amba_g5.dfa inputfiles/amba/amba_g6.dfa
python shield.py -f inputfiles/amba/amba_g5.dfa inputfiles/amba/amba_g6.dfa inputfiles/amba/amba_g10.dfa
python shield.py -f inputfiles/amba/amba_g5.dfa inputfiles/amba/amba_g6.dfa inputfiles/amba/amba_g9_eventually4.dfa inputfiles/amba/amba_g10.dfa
python shield.py -f inputfiles/amba/amba_g5.dfa inputfiles/amba/amba_g6.dfa inputfiles/amba/amba_g9_eventually8.dfa inputfiles/amba/amba_g10.dfa
python shield.py -f inputfiles/amba/amba_g5.dfa inputfiles/amba/amba_g6.dfa inputfiles/amba/amba_g9_eventually16.dfa inputfiles/amba/amba_g10.dfa
python shield.py -f inputfiles/amba/amba_g5.dfa inputfiles/amba/amba_g6.dfa inputfiles/amba/amba_g9_eventually64.dfa inputfiles/amba/amba_g10.dfa
python shield.py -f inputfiles/amba/amba_g8_1.dfa inputfiles/amba/amba_g8_2.dfa inputfiles/amba/amba_g9_eventually4.dfa inputfiles/amba/amba_g10.dfa
python shield.py -f inputfiles/amba/amba_g8_1.dfa inputfiles/amba/amba_g8_2.dfa inputfiles/amba/amba_g9_eventually8.dfa inputfiles/amba/amba_g10.dfa
python shield.py -f inputfiles/amba/amba_g8_1.dfa inputfiles/amba/amba_g8_2.dfa inputfiles/amba/amba_g9_eventually16.dfa inputfiles/amba/amba_g10.dfa
python shield.py -f inputfiles/amba/amba_g8_1.dfa inputfiles/amba/amba_g8_2.dfa inputfiles/amba/amba_g9_eventually64.dfa inputfiles/amba/amba_g10.dfa


echo "Other Benchmarks:\n"
echo "================================================\n"
python shield.py -f inputfiles/traf/pro1.dfa inputfiles/traf/pro2.dfa inputfiles/traf/pro3.dfa
python shield.py -f inputfiles/auto/req1_1.dfa inputfiles/auto/req1_2.dfa inputfiles/auto/req2.dfa inputfiles/auto/req3.dfa inputfiles/auto/req4.dfa 
python shield.py -f inputfiles/toyota/toyota_r26.dfa inputfiles/toyota/toyota_r27.dfa inputfiles/toyota/toyota_r32.dfa inputfiles/toyota/toyota_r33.dfa inputfiles/toyota/toyota_r34.dfa
 
echo "LTL Benchmarks:\n"
echo "================================================\n"
python shield.py -f inputfiles/ltl/absence1_globally.dfa
python shield.py -f inputfiles/ltl/absence2_beforeR.dfa
python shield.py -f inputfiles/ltl/absence3_afterQ.dfa
python shield.py -f inputfiles/ltl/absence4_betweenQandR.dfa
python shield.py -f inputfiles/ltl/absence5_afterQuntilR.dfa
python shield.py -f inputfiles/ltl/existance2_beforeR.dfa
python shield.py -f inputfiles/ltl/existance3_afterQ0.dfa
python shield.py -f inputfiles/ltl/existance4_betweenQandR.dfa
python shield.py -f inputfiles/ltl/existance1_eventually0.dfa
python shield.py -f inputfiles/ltl/existance1_eventually4.dfa
python shield.py -f inputfiles/ltl/existance1_eventually16.dfa
python shield.py -f inputfiles/ltl/existance1_eventually64.dfa
python shield.py -f inputfiles/ltl/existance1_eventually256.dfa
python shield.py -f inputfiles/ltl/existance1_eventually512.dfa
python shield.py -f inputfiles/ltl/existance3_afterQ0.dfa
python shield.py -f inputfiles/ltl/existance3_afterQ4.dfa
python shield.py -f inputfiles/ltl/existance3_afterQ16.dfa
python shield.py -f inputfiles/ltl/existance3_afterQ64.dfa
python shield.py -f inputfiles/ltl/existance3_afterQ256.dfa
python shield.py -f inputfiles/ltl/existance3_afterQ512.dfa
python shield.py -f inputfiles/ltl/existance5_afterQuntilR2.dfa
python shield.py -f inputfiles/ltl/existance5_afterQuntilR4.dfa
python shield.py -f inputfiles/ltl/existance5_afterQuntilR8.dfa
python shield.py -f inputfiles/ltl/existance5_afterQuntilR10.dfa
python shield.py -f inputfiles/ltl/existance5_afterQuntilR12.dfa
#python shield.py -f inputfiles/ltl/existance5_afterQuntilR14.dfa


