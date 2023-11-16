import argparse
import os
import random
import shutil
import subprocess
import xml.etree.ElementTree as ET
from glob import glob

parser = argparse.ArgumentParser()
parser.add_argument('--tables', type=int, default=24, help='Number of tables')
parser.add_argument('--table-capacity', type=int, default=10, help='Individual table capacity')
parser.add_argument('--maximum-known-participants', type=int, default=1, help='Maximum number of participants from the initial table')
parser.add_argument('--seed', type=int, default=124, help='Seed to use for the pseudo-random number generator')
args = parser.parse_args()

T = args.tables  # number of tables
TC = args.table_capacity # table capacity
# limit the number of initial participants sharing the same table after shuffling
MKP  = args.maximum_known_participants

K = 7   # sequence length

# maximum number of attempts for reassigning a participant
MAX_ATTEMPTS = 100

# if the model does not reach a solution, try a different seed!
random.seed(args.seed)

assert T * TC % 2 == 0, "There must be an even number of seats"
assert TC <= 12, "The table capacity must be at most 12"

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
    for n in range(0, T * TC):
        if n % 2 == 0:
            seq = ''.join([base[random.randint(0, len(base) - 1)] for b in range(K)])
            not_this_initial_table = None
            not_this_table = None
        else:
            # from the previous iteration
            seq = ''.join([complement[base.index(s)] for s in reversed(seq)])
            # make sure that two matching participants are not sitting at the same table
            # initially
            not_this_initial_table = initial_table
            # nor once moving
            not_this_table = table

        # select the initial table
        attempts = 0
        initial_table = random.randint(0, T - 1)
        while len(initial_tables[initial_table]) >= TC or initial_table == not_this_initial_table:
            assert attempts <= MAX_ATTEMPTS, f"There's been 10 attempts to assign participant #{n+1}, giving up! You may try another seed or allow more common participants."
            if len(initial_tables[initial_table]) >= TC:
                print(f'Table #{initial_table+1} is full, reassigning participant #{n+1}...')
            if initial_table == not_this_initial_table:
                print(f'Complement of participant #{n+1} is already sitting at this table, reassigning...')
            initial_table = random.randint(0, T - 1)
            attempts += 1
        initial_tables[initial_table].append(n)

        # select the destination table
        attempts = 0
        table = random.randint(0, T - 1)
        while table == initial_table or len(tables[table]) >= TC or table == not_this_table or sum(c in tables[table] for c in initial_tables[initial_table]) >= MKP:
            assert attempts <= MAX_ATTEMPTS, f"There's been 10 attempts to assign participant #{n+1}, giving up! You may try another seed or allow more common participants."
            if len(tables[table]) > TC:
                print(f'Table {table+1} is full, reassigning participant {n+1}...')
            if table == not_this_table:
                print(f'Complement of participant #{n+1} is already sitting at this table, reassigning...')
            if sum(c in tables[table] for c in initial_tables[initial_table]) >= MKP:
                print(f'Table #{table+1} already has {MKP} participants from table #{initial_table+1}, reassigning participant #{n+1}...')
            table = random.randint(0, T - 1)
            attempts += 1
        common_partners = ['#'+str(c+1) for c in initial_tables[initial_table] if c in tables[table]]
        if common_partners:
            print(f'Participant #{n+1} will be sitting with {len(common_partners)} known participant(s) from its initial table: ' + ', '.join(common_partners))
        tables[table].append(n)

        assert initial_table != not_this_initial_table
        assert table != not_this_table

        tree = generate_card(n, initial_table, table, seq)
        os.makedirs('cards/Table #'+str(initial_table+1), exist_ok=True)
        tree.write('cards/Table #'+str(initial_table+1)+'/Participant #'+str(n+1)+'.svg')
        f.write(f'{n+1}\t{initial_table+1}\t{table+1}\t{seq}\n')

if os.path.isdir('templates'):
    print('Removing existing templates/ directory...')
    shutil.rmtree('templates')

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
