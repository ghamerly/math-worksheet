#!/usr/bin/env python3

# generate a math worksheet, and associated answer sheet, in PDF

import argparse
import random
import subprocess
import time
import tabulate

tabulate.PRESERVE_WHITESPACE = True

# Things to fix:
#   - adaptive width for larger numbers (and possibly negative numbers; not sure
#       they work either)
#   - problems like "0 * ? = 0" do not have unique solutions

def make_problem(args):
    '''Generate a random problem using source values in the range [0, max_value]'''
    a = b = c = None

    # if we disallow negatives, then keep trying until we get something in range
    # (could loop infinitely...)
    while a is None or min(a, b, c) < 0 and not args.allow_negatives:
        a = random.randint(0, args.max_value)
        b = random.randint(0, args.max_value)
        options = []
        if args.addition: options.append(('+', lambda a, b: a + b))
        if args.subtraction: options.append(('-', lambda a, b: a - b))
        if args.multiplication: options.append(('*', lambda a, b: a * b))
        op, f = random.choice(options)
        c = f(a, b)

    v = [a, b, c]
    answer = '{v[0]:2} {op} {v[1]:2} = {v[2]:3}'.format(**locals())
    # choose one of the three at random to go missing
    options = [0, 1, 2] if args.algebra else [2]
    v[random.choice(options)] = '__'
    question = '{v[0]:2} {op} {v[1]:2} = {v[2]:3}'.format(**locals())

    return question, answer

def make_output(args, title, filename, entries):
    num_cols = args.page_width // len(entries[0])
    output = ['']
    for i in range(0, len(entries), num_cols):
        output.append(entries[i:i+num_cols])
    output = tabulate.tabulate(output, stralign='right', tablefmt='plain')
    # get extra spacing between rows
    output = output.replace('\n', '\n\n\n')

    if args.terminal_only:
        print('-----', title, filename)
        print(output)
    else:
        ps2pdf = subprocess.Popen(['ps2pdf', '-', filename], stdin=subprocess.PIPE)
        enscript = subprocess.Popen(['enscript', '-o', '-', '--media=Letter', '--title', title, '--columns=1', '--portrait'], stdin=subprocess.PIPE, stdout=ps2pdf.stdin)
        enscript.communicate(output.encode('utf-8'))
        enscript.wait()
        ps2pdf.communicate()
        ps2pdf.wait()

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--max-value', type=int, default=10, help='maximum value given in the problem')
    p.add_argument('--num-problems', type=int, default=50, help='number of problems')
    p.add_argument('--page-width', type=int, default=80, help='number of characters on the page')

    p.add_argument('--no-addition', dest='addition', action='store_false', default=True)
    p.add_argument('--no-multiplication', dest='multiplication', action='store_false', default=True)
    p.add_argument('--no-subtraction', dest='subtraction', action='store_false', default=True)
    p.add_argument('--no-algebra', dest='algebra', action='store_false', default=True)
    p.add_argument('--allow-negatives', action='store_true', default=False)
    p.add_argument('--seed', type=int, default=int(time.time() * 10) % 100000, help='random number seed (default is based on time.time())')
    p.add_argument('--terminal-only', action='store_true', default=False, help='do not make PDFs; output directly to terminal (for testing)')
    args = p.parse_args()

    random.seed(args.seed)


    problems, answers = [], []
    for i in range(args.num_problems):
        problem, answer = make_problem(args)
        problems.append(problem)
        answers.append(answer)
    
    COLUMN_WIDTH = max(map(len, problems + answers)) + 5 # extra whitespace between columns
    QUESTION_FORMAT = '{{0:{COLUMN_WIDTH:d}s}}'.format(**locals()) # => '{0:<width>d}'
    problems = [QUESTION_FORMAT.format(p) for p in problems]
    answers  = [QUESTION_FORMAT.format(a) for a in answers]

    make_output(args, 'Math worksheet (seed: {})'.format(args.seed), 'worksheet.pdf', problems)
    make_output(args, 'Math worksheet answers (seed: {})'.format(args.seed), 'worksheet_answers.pdf', answers)

