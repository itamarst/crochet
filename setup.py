import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

dir_path = os.path.dirname(__file__)
if os.path.exists(os.path.join(dir_path, "crochet")):
    # Make sure local Crochet is imported:
    sys.path.insert(0, dir_path)

import crochet

setup(
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    name='crochet',
    version=crochet.__version__,
    description="Use Twisted from threaded applications",
    install_requires=[
        "Twisted>=11.1",
        ],
    keywords="twisted threading",
    license="MIT",
    packages=["crochet", "crochet.tests"],
    url="https://github.com/itamarst/crochet",
    maintainer='Itamar Turner-Trauring',
    maintainer_email='itamar@futurefoundries.com',
    long_description=open('README.rst').read(),
)
