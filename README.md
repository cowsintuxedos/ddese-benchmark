# DeePhi DDESE Benchmark
For use with the DeePhi Descartes AMI on AWS.
https://aws.amazon.com/marketplace/pp/B079N2J42R?qid=1532541099673

Usage:  
SSH into your DeePhi DDESE instance.  
sudo bash  
source /opt/Xilinx/SDx/2017.1.rte/setup.sh  
cd ASR_Accelerator/deepspeech2  
source activate test_py3  
git clone https://github.com/aws/aws-fpga/  
source aws-fpga/sdk_setup.sh  
python aws_test.py --fpga_config deephi/config/fpga_cnnblstm_0.15.json --audio_path data/long_audio/wav/long_audio3.wav --single_test --multi_loop_format |& tee test_output.txt && python means.py | tee -a means_output.txt  

--audio_path argument is path to the audio file, with an upper limit of 3 second duration.  
test_output.txt contains the results of the tests; remove the --multi_loop_format argument for verbose detail.  
means_output.txt contains the means of the results.  


Summary: 
Recreated numbers, i.e. average speedup on long audio files (>2 seconds) ~8X; average power usage = 18 watts, max power usage measured = 25 watts. See output data.

The DeePhi AMI includes test audio files located in data/short_audio/wav/, data/middle_audio/wav/, and data/long_audio/wav/. Used these in tests below.
Should also take into consideration CPU usage when writing/parsing the outputs.

Steps taken:
1.	Logged outputs from aws_test.py and modified the numbers of tests it ran
a.	By default, aws_test.py runs 1000 tests on one file using the single-test argument
2.	Wrote means.py to parse outputs from aws_test.py to find average use times
3.	Calculated avg. speedup by dividing average CPU use time by average FPGA use time
4.	Ran 25 tests per file and averaged the use times; avg. speedup = 7.629X
5.	Ran 100 tests per file and averaged the use times; avg. speedup = 8.106X
6.	Ran 10000 tests on a single file and measured power usage; avg. = 18w, max = 25w
Contents:
1.	FPGA power consumption 		(1)
2.	Command format/notes 		(2)
3.	Example test outputs 			(3)
4.	means.py code 			(4)
5.	Output data 				(5-7)
6.	Extra					(8-)

1.	FPGA power consumption:  fpga-describe-local-image -S 0 -M
Average      : 18 watts
Max measured : 25 watts
Last measured is almost always 18 watts, but sometimes jumps between 18 and 25; the average intermittently changes to 19 watts for a short period, perhaps denoting a cluster of power spikes.
** Cloned the aws-fpga git repo located at https://github.com/aws/aws-fpga into /deepspeech2 for the power metrics because the version of aws-fpga on this AMI is deprecated.
2.	Command format: (uses aws_test.py - runs deepspeech2 multiple times on each audio file and outputs the average cpu and fpga runtimes for each file)
python aws_test.py --fpga_config deephi/config/fpga_cnnblstm_0.15.json --audio_path data/long_audio/wav/long_audio3.wav --single_test --multi_loop_format |& tee test_output.txt && python means.py | tee -a means_output.txt


Explanations:
python aws_test.py --fpga_config deephi/config/fpga_cnnblstm_0.15.json --audio_path data/long_audio/wav/long_audio3.wav --single_test
Runs the test itself on a single audio file, long_audio3.wav; default number of runs is 1000.
** The --fpga_config argument is required to display both cpu and cpu+fpga use times.

--multi_loop_format
Outputs the results of test in comma-delimited format, which is parsed by means.py; see example test output section for more detail. Remove from command for detailed outputs.
** Seems to only work with the --single_test argument from above.

|& tee test_output.txt
Outputs the results of all tests for one file to test_output.txt; overwrites test_output.txt with new test results when it reaches new file, after calling means.py.
Also outputs to console.

&& python means.py
Parses test_output.txt, and finds the average use times for CPU and FPGA; code for means.py located below.

| tee -a means_output.txt
Appends the average use times to means_out.txt.
Also outputs to console.
3.	Example test output:

Normal output from running aws_test.py with --fpga_config and --single_test arguments:
===1256th test===
CNN use time     :  0.037392377853393555 seconds
LSTM use time    :  0.44629526138305664 seconds
FC use time      :  0.00014209747314453125 seconds
SoftMax use time :  9.369850158691406e-05 seconds
decode use time  :  0.00014472007751464844 seconds
Forward use time :  0.48421573638916016 seconds
[CPU] IT'LL BE NO DISAPPOINTMENT TO ME
[CPU] Decoded 2.18 seconds of audio in 0.518734 seconds

FPGA use time    :  0.04261279106140137 seconds
FC use time      :  0.0009109973907470703 seconds
SoftMax use time :  0.00010657310485839844 seconds
decode use time  :  0.00013756752014160156 seconds
Forward use time :  0.043863534927368164 seconds
[FPGA] IT'LL BE NO DISAPPOINTMENT TO ME
[FPGA] Decoded 2.18 seconds of audio in 0.078382 seconds         

Shortened output when adding the --multi_loop_format argument:
1256,0.037392377853393555,0.44629526138305664,0.00014209747314453125,9.369850158691406e-05,0.00014472007751464844,0.48421573638916016,0.518734,1.487
0.04261279106140137,0.0009109973907470703,0.00010657310485839844,0.00013756752014160156,0.043863534927368164,0.078382,0.166
** This is the same as above, just without the formatting, and with the totals appended as the last value; much easier to parse. First line is CPU values, second line is FPGA values.
** --multi_loop_format seems to only work with the --single_test argument.
 
4.	means.py: (used to calculate average CPU and FPGA runtime)
import numpy as np
total_cpu = []
total_fpga = []
odd = True          # used to parse each pair of lines as one pair; true = CPU, false = FPGA
tests = 0
total_tests = 1000  # total number of tests ran

# parse output
with open('test_output.txt') as f:
    # skip the first 9 lines of output file
    for _ in range(9):
        next(f)

    # then iterate through the file; use short output format
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
print('%.3f'%(avg_cpu/avg_fpga))

 
5.	Data: 
25 tests per file:
Average speedup for short audio files (<1 s): 3.983x
Average speedup for middle audio files (1-2 s): 5.674x
Average speedup for long audio files (>2 s): 7.629x
100 tests per file:
Average speedup for short audio files (<1 s): 4.043x
Average speedup for middle audio files (1-2 s): 6.324x
Average speedup for long audio files (>2 s): 8.106x

Outputs for 25 tests per file:
** Each set of 3 outputs below, i.e. CPU use time, FPGA use time, and speedup, corresponds to the decode tests of one file in the directory listed.
Short audio directory: data/short_audio/wav/ (5 files)
Average CPU runtime	: 0.164 +- 0.002 seconds
Average FPGA runtime	: 0.043 +- 0.001 seconds
Average speedup: 3.835x

Average CPU runtime	: 0.205 +- 0.043 seconds
Average FPGA runtime	: 0.045 +- 0.001 seconds
Average speedup: 4.593x

Average CPU runtime 	: 0.169 +- 0.013 seconds
Average FPGA runtime 	: 0.046 +- 0.001 seconds
Average speedup: 3.678x

Average CPU runtime  	: 0.190 +- 0.037 seconds
Average FPGA runtime 	: 0.045 +- 0.001 seconds
Average speedup: 4.256x

Average CPU runtime  	: 0.168 +- 0.001 seconds
Average FPGA runtime 	: 0.047 +- 0.001 seconds
Average speedup: 3.555x
Average speedup for short audio files: 3.983x

Middle: data/middle_audio/wav/ (20 files)
Average CPU runtime  : 0.375 +- 0.001 seconds
Average FPGA runtime : 0.070 +- 0.001 seconds
Average speedup: 5.342x

Average CPU runtime  : 0.592 +- 0.088 seconds
Average FPGA runtime : 0.077 +- 0.001 seconds
Average speedup: 7.690x

Average CPU runtime  : 0.393 +- 0.001 seconds
Average FPGA runtime : 0.075 +- 0.001 seconds
Average speedup: 5.249x

Average CPU runtime  : 0.548 +- 0.001 seconds
Average FPGA runtime : 0.213 +- 0.001 seconds
Average speedup: 2.578x

Average CPU runtime  : 0.391 +- 0.001 seconds
Average FPGA runtime : 0.074 +- 0.001 seconds
Average speedup: 5.296x

Average CPU runtime  : 0.735 +- 0.095 seconds
Average FPGA runtime : 0.204 +- 0.001 seconds
Average speedup: 3.602x

Average CPU runtime  : 0.599 +- 0.088 seconds
Average FPGA runtime : 0.076 +- 0.001 seconds
Average speedup: 7.865x

Average CPU runtime  : 0.412 +- 0.001 seconds
Average FPGA runtime : 0.076 +- 0.001 seconds
Average speedup: 5.396x

Average CPU runtime  : 0.739 +- 0.045 seconds
Average FPGA runtime : 0.196 +- 0.000 seconds
Average speedup: 3.764x

Average CPU runtime  : 0.636 +- 0.059 seconds
Average FPGA runtime : 0.078 +- 0.000 seconds
Average speedup: 8.170x

Average CPU runtime  : 0.564 +- 0.094 seconds
Average FPGA runtime : 0.074 +- 0.001 seconds
Average speedup: 7.623x

Average CPU runtime  : 0.487 +- 0.001 seconds
Average FPGA runtime : 0.179 +- 0.001 seconds
Average speedup: 2.726x

Average CPU runtime  : 0.394 +- 0.001 seconds
Average FPGA runtime : 0.074 +- 0.001 seconds
Average speedup: 5.293x

Average CPU runtime  : 0.469 +- 0.102 seconds
Average FPGA runtime : 0.077 +- 0.001 seconds
Average speedup: 6.081x

Average CPU runtime  : 0.622 +- 0.075 seconds
Average FPGA runtime : 0.078 +- 0.000 seconds
Average speedup: 7.935x

Average CPU runtime  : 0.405 +- 0.001 seconds
Average FPGA runtime : 0.077 +- 0.001 seconds
Average speedup: 5.277x

Average CPU runtime  : 0.410 +- 0.062 seconds
Average FPGA runtime : 0.074 +- 0.001 seconds
Average speedup: 5.527x

Average CPU runtime  : 0.551 +- 0.039 seconds
Average FPGA runtime : 0.078 +- 0.001 seconds
Average speedup: 7.107x

Average CPU runtime  : 0.395 +- 0.001 seconds
Average FPGA runtime : 0.075 +- 0.001 seconds
Average speedup: 5.278x
Average speedup for middle audio files: 5.674x

Long: data/long_audio/wav/ (5 files)
Average CPU runtime  : 1.575 +- 0.105 seconds
Average FPGA runtime : 0.293 +- 0.001 seconds
Average speedup: 5.384x

Average CPU runtime  : 1.375 +- 0.157 seconds
Average FPGA runtime : 0.143 +- 0.000 seconds
Average speedup: 9.645x

Average CPU runtime  : 1.180 +- 0.120 seconds
Average FPGA runtime : 0.141 +- 0.001 seconds
Average speedup: 8.355x

Average CPU runtime  : 1.074 +- 0.231 seconds
Average FPGA runtime : 0.141 +- 0.001 seconds
Average speedup: 7.598x

Average CPU runtime  : 1.007 +- 0.205 seconds
Average FPGA runtime : 0.141 +- 0.001 seconds
Average speedup: 7.165x
Average speedup for long audio files: 7.629x 


Setup commands:
sudo bash
source /opt/Xilinx/SDx/2017.1.rte/setup.sh
cd ASR_Accelerator/deepspeech2
source activate test_py3
