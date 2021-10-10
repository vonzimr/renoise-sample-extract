from typing import IO, List, Tuple
import click
from pydub import AudioSegment, exceptions
from pathlib import Path
from zipfile import ZipFile, Path as ZipPath
import os
from os.path import splitext
import re
import sys

import pydub

XRNI_SAMPLE_PATH = 'SampleData/'
name_extract = re.compile("Sample[0-9]+ \(?([^\(\)]*)")


def get_sample_data(sample: IO[bytes]):
    full_path = sample.name
    stem, ext = splitext(full_path)
    try:
        name = name_extract.search(stem).group(1)
    except AttributeError:
        sys.exit(f"Could not extract name from {full_path}")
    else:
        ext = ext.replace('.', '')
        return {'path': full_path, 'name': name, 'ext': ext, 'sample': sample}


def get_audio_from_xrns(xrni):
    zip = ZipFile(xrni)

    def is_sample(path):
        return XRNI_SAMPLE_PATH in path and path.replace(XRNI_SAMPLE_PATH, '') != ''

    return [get_sample_data(zip.open(sample)) for sample in zip.namelist() if is_sample(sample)]


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
        sample_data = get_audio_from_xrns(xrni)

        if(len(sample_data) == 0):
            click.echo(f"No Samples Found for {xrni.stem}")
            return

        save_destination = export_folder.joinpath(xrni.stem)

        if not save_destination.exists():
            os.mkdir(save_destination)

        for data in sample_data:
            try:
                audio = AudioSegment.from_file(
                    data['sample'], format=data['ext'])
            except exceptions.PydubException:
                click.clear()
                click.echo(
                    f"encountered an error decoding {data['name']}", err=True)
            else:
                audio = audio.set_channels(1 if mono else audio.channels)
                audio = audio.set_sample_width(int(int(bit_depth) / 8))
                audio.export(export_folder.joinpath(
                    f"{xrni.stem}/{data['name']}.wav"), format='wav')

    def convert_folder(search_path: Path):
        xrni_files = [file for file in search_path.glob('**/*.xrni')]
        with click.progressbar(xrni_files, label=f"Extracting Samples...") as bar:
            for file in bar:
                convert_instrument(file)

    if file_or_path.is_dir():
        return convert_folder(file_or_path)

    convert_instrument(file_or_path)


if __name__ == '__main__':
    convert()
