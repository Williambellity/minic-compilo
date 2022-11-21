#!/bin/bash
echo "Star *"
echo "------------------"
python3 compilo.py star
nasm -f elf64 star.asm
gcc -no-pie -fno-pie star.o -o star
echo "               "
echo "Result :"
./star
echo "               "
echo "               "
echo "               "

echo "Address &"
echo "------------------"
python3 compilo.py address
nasm -f elf64 address.asm
gcc -no-pie -fno-pie address.o -o address
echo "               "
echo "Result :"
./address
echo "               "
echo "               "
echo "               "

echo "starAddress *&"
echo "------------------"
python3 compilo.py starAddress
nasm -f elf64 starAddress.asm
gcc -no-pie -fno-pie starAddress.o -o starAddress
echo "               "
echo "Result :"
./starAddress
echo "               "
echo "               "
echo "               "

