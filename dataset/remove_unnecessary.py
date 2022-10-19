import os
import glob
import lizard

# we only care about the c++ solutions
os.system('find -name "samples" | xargs -I{} rm -r {}')
os.system('find -name "solutions_python" | xargs -I{} rm -r {}')

# remove files that only have one function
files = glob.glob('codeforces/*/solutions_c++/*.txt')
p = lizard.analyze_files(files)
for solution in p:
    if len(solution.function_list) < 2:
        os.unlink(solution.filename)
    else:
        os.replace(solution.filename, solution.filename[:-4] + '.cpp')
