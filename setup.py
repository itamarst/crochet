import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import versioneer
versioneer.versionfile_source = 'crochet/_version.py'
versioneer.versionfile_build = 'crochet/_version.py'
versioneer.tag_prefix = '' # tags are like 1.2.0
versioneer.parentdir_prefix = 'crochet-'


def read(path):
    """
    Read the contents of a file.
    """
    with open(path) as f:
        return f.read()

setup(
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    name='crochet',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="Use Twisted anywhere!",
    install_requires=[
        "Twisted>=11.1",
    ],
    keywords="twisted threading",
    license="MIT",
    packages=["crochet", "crochet.tests"],
    url="https://github.com/itamarst/crochet",
    maintainer='Itamar Turner-Trauring',
    maintainer_email='itamar@itamarst.org',
    long_description=read('README.rst') + '\n' + read('docs/news.rst'),
)
