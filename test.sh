now="$(date +'%Y%m%d_%H%M%S')"
./kstab_test.sh > kstab_$now.txt 
now="$(date +'%Y%m%d_%H%M%S')"
./burst_test.sh > burst_$now.txt 
now="$(date +'%Y%m%d_%H%M%S')"
./burst_imp_test.sh > burst_imp_$now.txt 
