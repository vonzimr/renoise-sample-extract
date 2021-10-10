from typing import IO, List, Tuple
import click
from pydub import AudioSegment
from pathlib import Path
from zipfile import ZipFile, Path as ZipPath
import os
from os.path import splitext
import re

XRNI_SAMPLE_PATH = 'SampleData/'

def get_sample_data(sample: IO[bytes]):
    full_path = sample.name
    stem, ext = splitext(full_path)
    name = stem.replace(XRNI_SAMPLE_PATH, '')
    ext = ext.replace('.', '')
    return {'path': full_path, 'name': name, 'ext': ext, 'sample': sample}


def get_audio_from_xrns(xrni):
    zip = ZipFile(xrni)
    return [get_sample_data(zip.open(sample)) for sample in zip.namelist() if XRNI_SAMPLE_PATH in sample]


def create_export_folder(out='export'):
    out_dir = Path(out)
    if not out_dir.exists():
        os.mkdir(out_dir)
    return out_dir


@click.command()
@click.argument('file_or_path', required=True)
@click.option('--out', help='output folder', default='export')
@click.option('--mono',  is_flag=True, default=False)
@click.option('--bit-depth',  type=click.Choice(['8', '16', '24']), default='16')
def convert(file_or_path, out, mono, bit_depth):
    export_folder = create_export_folder(out)
    file_or_path = Path(file_or_path)

    def convert_instrument(xrni: Path):
        click.echo(f"Reading XRNI {xrni.name}...")
        sample_data = get_audio_from_xrns(xrni)

        if(len(sample_data) == 0):
            click.echo(f"No Samples Found for {xrni.stem}")
            return

        save_destination = export_folder.joinpath(xrni.stem)

        if not save_destination.exists():
            os.mkdir(save_destination)



        click.echo(f'Found {len(sample_data)} samples')

        for data in sample_data:
            click.echo(f"Converting {data['name']}...")
            audio = AudioSegment.from_file(data['sample'], format=data['ext'])
            audio = audio.set_channels(1 if mono else audio.channels)
            audio = audio.set_sample_width(int(int(bit_depth) / 8))
            audio.export(export_folder.joinpath(
                f"{xrni.stem}/{data['name']}.wav"), format='wav')
            click.echo(f'Done.')


    def convert_folder(search_path: Path):
        xrni_files = search_path.glob('**/*.xrni')
        for file in xrni_files:
            convert_instrument(file)

    if file_or_path.is_dir():
        return convert_folder(file_or_path)

    convert_instrument(file_or_path)


if __name__ == '__main__':
    convert()
