import argparse
import os
import random
import shutil
import subprocess
import xml.etree.ElementTree as ET

from Bio.Seq import Seq

# A = green, U = red, C = orange, G = blue
coding_sequence_palette = ['#7FB800', '#A63D40', '#F19A3E', '#008FCC']

# provided by https://supercolorpalette.com/
protein_sequence_palette = [
    '#7FB800',  # A
    '#A63D40',  # C
    '#F19A3E',  # D
    '#008FCC',  # E
    '#81701F',  # F
    '#264864',  # G
    '#16AC61',  # H
    '#702C96',  # I
    '#B49D1D',  # K
    '#4D1B1E',  # L
    '#2630C5',  # M
    '#A24395',  # N
    '#EA5906',  # P
    '#4B9AAA',  # Q
    '#E23318',  # R
    '#86C358',  # S
    '#DE2B73',  # T
    '#233E8B',  # V
    '#852A9D',  # W
    '#AF3254'  # Y
]

base = 'AUCG'
amino_acids = 'ACDEFGHIKLMNPQRSTVWY'
sequence_length = 7


def generate_coding_sequence():
    s = 'AUG'  # start codon
    for i in range(sequence_length - 1):
        while True:
            codon = ''.join(base[random.randint(0, 3)] for _ in range(3))
            # ignore starting and stop codons
            if Seq(codon).translate() != '*':
                break
        s += codon
    return s


def generate_card(participant_id, table, coding_sequence, protein_sequence):
    a = ET.Element('svg', version='1.1', width='3.5in', height='2in', viewBox='0 0 175 100')
    t = ET.SubElement(a, 'text', x='50%', y='50%', fill='black',
                      attrib={'text-anchor': 'middle', 'font-family': 'Courier Prime',
                              'font-size': '20'})
    t.text = 'Table #' + str(table + 1)

    # participant ID
    t = ET.SubElement(a, 'text', x='50%', y=str(100 / 2 + 20), fill='black',
                      attrib={'text-anchor': 'middle', 'font-family': 'Courier Prime',
                              'font-size': '10'})
    t.text = 'Your ID is #' + str(participant_id + 1)

    # protein sequence at top
    for i, aa in enumerate(protein_sequence):
        w = 175 / len(protein_sequence)
        offset = 0 + (i * w)
        ET.SubElement(a, 'rect', x=str(offset), y='0', width=str(w),
                      height=str(w), fill=protein_sequence_palette[amino_acids.index(aa)])
        t = ET.SubElement(a, 'text', x=str(offset + (w / 2)), y=str(w / 2 + 6.5), fill='white',
                          attrib={'text-anchor': 'middle', 'font-family': 'Courier Prime', 'font-size': '22'})
        t.text = aa

    # codon sequence at bottom
    for i, b in enumerate(coding_sequence):
        w = 175 / len(coding_sequence)
        offset = 0 + (i * w)
        ET.SubElement(a, 'rect', x=str(offset), y=str(100 - w), width=str(w),
                      height=str(w), fill=coding_sequence_palette[base.index(b)])
        t = ET.SubElement(a, 'text', x=str(offset + (w / 2)), y=str(100 - w / 2 + 2.5), fill='white',
                          attrib={'text-anchor': 'middle', 'font-family': 'Courier Prime', 'font-size': '8'})
        t.text = b
    return ET.ElementTree(a)


def generate_participant_master_list(participant_ids, table_ids, N):
    with open('seats.tsv', 'w') as f:
        f.write('participant_id\ttable_id\tpartner_1_id\tpartner_2_id\n')
        for i, (participant_id, table_id) in enumerate(zip(participant_ids, table_ids)):
            f.write(
                f'{participant_id + 1}\t{table_id + 1}\t{participant_ids[(i - 1) % N] + 1}\t{participant_ids[(i + 1) % N] + 1}\n')


def generate_cards(participant_ids, table_ids, coding_sequences, protein_sequences):
    if os.path.isdir('cards'):
        print('Removing existing cards/ directory...')
        shutil.rmtree('cards')
    os.mkdir('cards')
    for participant_id, table_id, coding_sequence, protein_sequence in zip(participant_ids, table_ids, coding_sequences,
                                                                           protein_sequences):
        tree = generate_card(participant_id, table_id, coding_sequence, protein_sequence)
        tree.write('cards/Participant #' + str(participant_id + 1) + '.svg')
        subprocess.run(
            ['rsvg-convert', '-f', 'pdf', '--output', 'cards/Participant #' + str(participant_id + 1) + '.pdf',
             'cards/Participant #' + str(participant_id + 1) + '.svg'])


def generate_printing_template(participants):
    root = ET.Element('svg', version='1.1', height='8.5in', width='11in')
    for i, participant in enumerate(participants):
        c = ET.parse('cards/' + 'Participant #' + str(participant + 1) + ".svg")
        r = c.getroot()
        r.attrib['x'] = str(i % 3 * 3.5 + 0.25) + 'in'
        r.attrib['y'] = str(i // 3 * 2 + 0.25) + 'in'
        root.append(r)
    # add some cutting guides
    # vertical
    for i in range(4):
        root.append(
            ET.Element('line', x1=str(0.25 + i * 3.5) + 'in', y1='0.25in', x2=str(0.25 + i * 3.5) + 'in',
                       y2='8.25in', stroke='black', attrib={'stroke-width': '.01'}))
    # horizontal
    for i in range(3):
        root.append(
            ET.Element('line', x1='0.25in', y1=str(0.25 + i * 2) + 'in', x2='10.75in',
                       y2=str(0.25 + i * 2) + 'in',
                       stroke='black', attrib={'stroke-width': '.01'}))
    return root


def generate_printing_templates(participant_ids):
    if os.path.isdir('templates'):
        print('Removing existing templates/ directory...')
        shutil.rmtree('templates')
    os.mkdir('templates')

    # generate printing templates...
    for template_id, offset in enumerate(range(0, len(participant_ids), 4 * 3)):
        root = generate_printing_template(participant_ids[offset:offset + (4 * 3)])
        tree = ET.ElementTree(root)
        tree.write('templates/Template #' + str(template_id + 1) + '.svg')
        subprocess.run(['rsvg-convert', '-f', 'pdf', '--output', 'templates/Template #' + str(template_id + 1) + '.pdf',
                        'templates/Template #' + str(template_id + 1) + '.svg'])


def generate_mishaps(participant_ids):
    if os.path.isdir('mishaps'):
        print('Removing existing mishaps/ directory...')
        shutil.rmtree('mishaps')
    os.mkdir('mishaps')
    # generate printing templates...
    for template_id, offset in enumerate(range(0, len(participant_ids), 4 * 3)):
        root = generate_printing_template(participant_ids[offset:offset + (4 * 3)])
        tree = ET.ElementTree(root)
        tree.write('mishaps/Template #' + str(template_id + 1) + '.svg')
        subprocess.run(['rsvg-convert', '-f', 'pdf', '--output', 'mishaps/Template #' + str(template_id + 1) + '.pdf',
                        'mishaps/Template #' + str(template_id + 1) + '.svg'])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tables', type=int, default=23, help='Number of tables')
    parser.add_argument('--table-capacity', type=int, default=10, help='Individual table capacity')
    parser.add_argument('--seed', type=int, default=124, help='Seed to use for the pseudo-random number generator')
    args = parser.parse_args()

    T = args.tables  # number of tables
    TC = args.table_capacity  # table capacity
    N = T * TC

    # if the model does not reach a solution, try a different seed!
    random.seed(args.seed)

    participant_ids = list(range(N))
    random.shuffle(participant_ids)

    coding_sequences = [generate_coding_sequence() for _ in range(N)]
    protein_sequences = [Seq(coding_sequences[i - 1]).translate() for i in range(len(coding_sequences))]

    tables = [[] for _ in range(T)]
    table_ids = []
    # assign participant to destination tables
    for i, participant_id in enumerate(participant_ids):
        while True:
            table_id = random.randint(0, T - 1)
            if len(tables[table_id]) < TC:
                tables[table_id].append(participant_id)
                table_ids.append(table_id)
                break

    generate_participant_master_list(participant_ids, table_ids, N)
    generate_cards(participant_ids, table_ids, coding_sequences, protein_sequences)
    generate_printing_templates(participant_ids)
    generate_mishaps([52])


if __name__ == '__main__':
    main()
