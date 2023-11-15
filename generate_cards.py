import xml.etree.ElementTree as ET
import random
import os
import shutil
import subprocess

# if the model does not reach a solution, try a different seed!
random.seed(134)

N = 110 # number of participants
T = 10  # number of tables
K = 7   # sequence length

# table capacity
TS = [12 for _ in range(T)]
TS[4] = 5

# limit the number of initial participants sharing the same table after shuffling
MOP  = 2

assert N % 2 == 0, "There must be an even number of participants"
assert N <= sum(TS), "There's not enough tables to seat everyone"
assert all(t <= 12 for t in TS), "Table must have at"

base = 'ATCG'
complement = 'TAGC'

background = ['#E5ECE9', '#5D737E', '#0D3B66']

# green, red, orange, blue, background, font
palette = ['#7FB800', '#A63D40', '#F19A3E', '#008FCC']

initial_tables = [[] for _ in range(T)]
tables = [[] for _ in range(T)]

def generate_card(participant_id, initial_table, table, sequence):
    a = ET.Element('svg', version='1.1', width='3.5in', height='2in', viewBox='0 0 175 100')
    t = ET.Element('text', x='0', y='8', fill='black', attrib={'font-size': '8', 'font-family': 'Dancing Script'})
    t = ET.Element('text', x='50%', y='50%', fill='black',
                   attrib={'text-anchor': 'middle', 'font-family': 'Dancing Script',
                           'font-size': '18'})
    t.text = 'Table #' + str(initial_table + 1) + ' → ' + '#' + str(table + 1)
    a.append(t)
    for i in range(K):
        offset = 0 + (i * 25)
        r = ET.Element('rect', x=str(offset), y='75', width='25',
                            height='25', fill=palette[base.index(sequence[i])])
        t = ET.Element('text', x=str(offset + 12.5), y='91', fill='white',
                       attrib={'text-anchor': 'middle', 'font-family': 'Courier Prime'})
        t.text = sequence[i]
        a.append(r)
        a.append(t)
    return ET.ElementTree(a)

if os.path.isdir('cards'):
    print('Removing existing cards/ directory...')
    shutil.rmtree('cards')

with open('seats.tsv', 'w') as f:
    f.write('participant_id\tinitial_table_id\ttable_id\tsequence\n')
    for n in range(0, N, 2):
        seq = ''.join([base[random.randint(0, 3)] for b in range(K)])

        initial_table = random.randint(0, T - 1)
        while len(initial_tables[initial_table]) >= TS[initial_table]:
            print(f'Table {initial_table+1} is full, reassigning participant {n+1}...')
            initial_table = random.randint(0, T - 1)
        initial_tables[initial_table].append(n)

        # ensure that he moves!
        table = random.randint(0, T - 1)
        while table == initial_table or len(tables[table]) >= TS[table] or sum(c in tables[table] for c in initial_tables[initial_table]) >= MOP:
            if len(tables[table]) >= TS[table]:
                print(f'Table {table+1} is full, reassigning participant {n+1}...')
            if table == initial_table:
                print(f'Sorry mate, you have to move!')
            table = random.randint(0, T - 1)
        tables[table].append(n)

        tree = generate_card(n, initial_table, table, seq)
        os.makedirs('cards/Table #'+str(initial_table+1), exist_ok=True)
        tree.write('cards/Table #'+str(initial_table+1)+'/Participant #'+str(n+1)+'.svg')
        f.write(f'{n+1}\t{initial_table+1}\t{table+1}\t{seq}\n')

        n += 1

        # make sure that two participants are not sitting at the same table
        # initially
        not_this_initial_table = initial_table
        initial_table = random.randint(0, T - 1)
        while len(initial_tables[initial_table]) >= TS[initial_table] or initial_table == not_this_initial_table:
            if len(initial_tables[initial_table]) >= TS[initial_table]:
                print(f'Table {initial_table+1} is full, reassigning participant {n+1}...')
            if initial_table == not_this_initial_table:
                print(f'Complement of {n+1} is already sitting at this table, reassigning...')
            initial_table = random.randint(0, T - 1)
        initial_tables[initial_table].append(n)

        # nor once moving
        not_this_table = table
        table = random.randint(0, T - 1)
        while table == initial_table or len(tables[table]) >= TS[table] or table == not_this_table or sum(c in tables[table] for c in initial_tables[initial_table]) >= MOP:
            if len(tables[table]) > TS[table]:
                print(f'Table {table+1} is full, reassigning participant {n+1}...')
            if table == not_this_table:
                print(f'Complement of {n+1} is already sitting at this table, reassigning...')
            table = random.randint(0, T - 1)
        tables[table].append(n)

        assert initial_table != not_this_initial_table
        assert table != not_this_table

        seq = ''.join([complement[base.index(s)] for s in reversed(seq)])
        tree = generate_card(n, initial_table, table, seq)
        os.makedirs('cards/Table #'+str(initial_table+1), exist_ok=True)
        tree.write('cards/Table #'+str(initial_table+1)+'/Participant #'+str(n+1)+'.svg')
        f.write(f'{n+1}\t{initial_table+1}\t{table+1}\t{seq}\n')

from glob import glob

# generate printing templates...
for table in range(T):
    root = ET.Element('svg', version='1.1', height='8.5in', width='11in')
    for i, participant in enumerate(glob('cards/Table #' + str(table+1) + '/*.svg')):
        c = ET.parse(participant)
        r = c.getroot()
        r.attrib['x'] = str(i % 3 * 3.5 + 0.25) + 'in'
        r.attrib['y'] = str(i // 3 * 2 + 0.25) + 'in'
        root.append(r)
    # add some cutting guides
    root.append(ET.Element('line', x1='3.75in', y1='0.25in', x2='3.75in', y2='8.25in', stroke='black'))
    root.append(ET.Element('line', x1='7.25in', y1='0.25in', x2='7.25in', y2='8.25in', stroke='black'))
    tree = ET.ElementTree(root)
    os.makedirs('templates', exist_ok=True)
    tree.write('templates/Table #'+str(table+1)+'.svg')
    subprocess.run(['rsvg-convert', '-f', 'pdf', '--output', 'templates/Table #'+str(table+1)+'.pdf',
                    'templates/Table #'+str(table+1)+'.svg'])
