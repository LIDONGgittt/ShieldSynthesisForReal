echo "Toyota Benchmarks:\n"
echo "================================================\n"
python shield.py -a realgo inputfiles/toyota/toyota_r26.dfa inputfiles/toyota/toyota_r27.dfa 
python shield.py -a realgo inputfiles/toyota/toyota_r32.dfa inputfiles/toyota/toyota_r33.dfa 
python shield.py -a realgo inputfiles/toyota/toyota_r26.dfa inputfiles/toyota/toyota_r27.dfa inputfiles/toyota/toyota_r32.dfa inputfiles/toyota/toyota_r33.dfa inputfiles/toyota/toyota_r34.dfa


echo "Auto drive Benchmarks:\n"
echo "================================================\n"
python shield.py -a realgo inputfiles/varman/autodrive1.dfa
python shield.py -a realgo inputfiles/varman/autodrive2.dfa
python shield.py -a realgo inputfiles/varman/autodrive1.dfa inputfiles/varman/autodrive2.dfa

echo "ACC Benchmarks:\n"
echo "================================================\n"

python shield.py -a realgo inputfiles/acc/acc1.dfa inputfiles/acc/acc3.dfa inputfiles/acc/acc4.dfa
python shield.py -a realgo inputfiles/acc/acc2.dfa inputfiles/acc/acc3.dfa inputfiles/acc/acc4.dfa
python shield.py -a realgo inputfiles/acc/acc1.dfa inputfiles/acc/acc2.dfa inputfiles/acc/acc3.dfa inputfiles/acc/acc4.dfa

echo "Drone Benchmarks:\n"
echo "================================================\n"
python shield.py -a realgo inputfiles/drone/goal.dfa inputfiles/drone/obs.dfa

echo "Settling Benchmarks:\n"
echo "================================================\n"
python shield.py -a realgo inputfiles/settling/c1.dfa inputfiles/settling/c2.dfa inputfiles/settling/c3.dfa inputfiles/settling/c4.dfa

echo "T1D Benchmarks:\n"
echo "================================================\n"
python shield.py -a realgo inputfiles/diabete.dfa

echo "water tank Benchmarks:\n"
echo "================================================\n"
python shield.py -a realgo inputfiles/waterTank_1.dfa inputfiles/waterTank_2.dfa                           