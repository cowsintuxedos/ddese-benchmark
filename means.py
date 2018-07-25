import numpy as np
total_cpu = []
total_fpga = []
odd = True          # used to parse each pair of lines as one pair
tests = 0
total_tests = 1000  # total number of tests ran

# parse output
with open('test_output.txt') as f:
    # skip the first 9 lines of output file
    for _ in range(9):
        next(f)

    # then iterate through the file
    for line in f:
        if tests < total_tests:
            # parse each pair of lines
            last = float(line.split(',')[-1])
            if odd:
                total_cpu.append(last)
            else:
                total_fpga.append(last)
                tests += 1
            odd = not odd

# calculate/output usetime averages and standard deviations
avg_cpu = np.mean(total_cpu)
std_cpu = np.std(total_cpu)
avg_fpga = np.mean(total_fpga)
std_fpga = np.std(total_fpga)

# output detailed info
print('Average CPU runtime  : ' + '%.3f'%(avg_cpu) + ' +- ' + '%.3f'%(std_cpu))
print('Average FPGA runtime : ' + '%.3f'%(avg_fpga) + ' +- ' + '%.3f'%(std_fpga))
print('Average speedup: ' + '%.3f'%(avg_cpu/avg_fpga) + 'x\n')

# output only the speedup
#print('%.3f'%(avg_cpu/avg_fpga))