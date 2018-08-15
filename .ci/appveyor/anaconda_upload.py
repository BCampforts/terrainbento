from __future__ import print_function

import os
import sys
import subprocess
import traceback
import glob

print('Using python: {prefix}'.format(prefix=sys.prefix))

repo_tag = os.environ.get('APPVEYOR_REPO_TAG', 'false')
tag_name = os.environ.get('APPVEYOR_REPO_TAG_NAME', '')
token = os.environ.get('ANACONDA_TOKEN', 'NOT_A_TOKEN')

if repo_tag == 'true' and tag_name.startswith('v'):
    channel = 'main'
    os.environ['BUILD_STR'] = ''
else:
    channel = 'dev'
    os.environ['BUILD_STR'] = 'dev'

print('Uploading to {channel} channel'.format(channel=channel))

try:
    cmd = ' '.join(['conda', 'build', '--output', '.conda-recipe', '--old-build-string'])
    resp = subprocess.check_output(cmd, shell=True)
except subprocess.CalledProcessError:
    traceback.print_exc()
else:
    file_to_upload = resp.strip().split()[-1]

(dirname, filename) = os.path.split(file_to_upload)
try:
    print(file_to_upload)
    print(dirname)
    print(filename)
    print(dirname + b'\\' + b'terrainbento*.tar.bz2')

    print(glob.glob(dirname + b'\\' + b'terrainbento*.tar.bz2'))
    file_to_upload = glob.glob(dirname + b'\\' + b'landlab*.tar.bz2')[0]
except IndexError:
    raise RuntimeError('{name}: not a file'.format(name=file_to_upload))

print(file_to_upload)

if not os.path.isfile(file_to_upload):
    raise RuntimeError('{name}: not a file'.format(name=file_to_upload))

cmd = ' '.join(['anaconda', '-t', token, 'upload', '--force',
                '--user', 'terrainbento', '--channel', channel,
                file_to_upload.decode('utf-8')])

if channel == 'main':
    try:
        subprocess.check_call(cmd, shell=True)
    except subprocess.CalledProcessError:
        traceback.print_exc()
else:
    print('Not a tagged release. Not deploying to Anaconda Cloud.')