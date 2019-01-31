set -x
gcc -std=c99 -D_MP_INTERNAL -DNDEBUG -D_EXTERNAL_RELEASE -D_USE_THREAD_LOCAL   -fvisibility=hidden -c -mfpmath=sse -msse -msse2 -fopenmp -O3 -D_LINUX_ -fPIC -D_LINUX_  -o tmp.o  -I/home/meng/z3/src/api $1
g++ -o $2  tmp.o  libz3.so -lpthread  -fopenmp -lrt
