#ifndef CALC_H
#define CALC_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

double calculate(double op1, double op2, const char* operation, int* status);
void print_usage();

#endif
