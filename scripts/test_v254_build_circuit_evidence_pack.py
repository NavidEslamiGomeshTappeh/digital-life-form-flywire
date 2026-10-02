import csv, gzip, json, subprocess, sys
from pathlib import Path

def write_gz(path, text):
    with gzip.open(path, 'wt', encoding='utf-8', newline='') as f:
        f.write(text)

def test_builder_exact_fixture(tmp_path):
    connections = tmp_path / 'connections.csv.gz'
    synapses = tmp_path / 'synapse_coordinates.csv.gz'
    reference = tmp_path / 'V230.csv'
    out = tmp_path / 'pack'
    root = 'R1'
    other = 'R9'

    write_gz(connections,
        'pre_root_id,post_root_id,neuropil,syn_count,nt_type\\n'
        f'{other},{root},ME_R,2,GLUT\\n'
        f'{other},{root},ME_R,3,GLUT\\n'
        'R2,R3,ME_R,9,GLUT\\n')

    write_gz(synapses,
        'pre_root_id,post_root_id,x,y,z\\n'
        f'{other},{root},10,20,30\\n'
        ',,11,21,31\\n'
        'R2,R3,12,22,32\\n')

    reference.write_text(
        'pre_root_id,post_root_id,x,y,z\\n'
        f'{other},{root},10,20,30\\n'
        f'{other},{root},11,21,31\\n',
        encoding='utf-8')

    script = Path(__file__).resolve().parents[1] / 'scripts' / 'v254_build_circuit_evidence_pack.py'
    subprocess.run([
        sys.executable, str(script), '--connections', str(connections), '--synapses', str(synapses),
        '--reference-v230', str(reference), '--output', str(out), '--root', root
    ], check=True)

    manifest = json.loads((out / 'MANIFEST.json').read_text(encoding='utf-8'))
    assert manifest['status'] == 'PASS'
    assert manifest['selected_directed_pairs'] == 1
    assert manifest['selected_synapse_rows'] == 2
    assert manifest['regression']['pair_counts_exact'] is True
    assert manifest['regression']['individual_synapse_set_exact'] is True

def test_builder_rejects_bad_header(tmp_path):
    connections = tmp_path / 'connections.csv.gz'
    synapses = tmp_path / 'synapse_coordinates.csv.gz'
    write_gz(connections, 'bad,header\\n1,2\\n')
    write_gz(synapses, 'pre_root_id,post_root_id,x,y,z\\nR1,R2,1,2,3\\n')
    out = tmp_path / 'pack'
    script = Path(__file__).resolve().parents[1] / 'v254_build_circuit_evidence_pack.py'
    p = subprocess.run([
        sys.executable, str(script), '--connections', str(connections), '--synapses', str(synapses),
        '--output', str(out), '--root', 'R1'
    ], text=True, capture_output=True)
    assert p.returncode != 0
