import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def get_crochet_version():
    """
    Get crochet version from version module without importing more than
    necessary.
    """
    this_dir_path = os.path.dirname(__file__)
    crochet_module_path = os.path.join(this_dir_path, "crochet")
    version_module_path = os.path.join(crochet_module_path, "_version.py")

    # The version module contains a variable called __version__
    exec(file(version_module_path).read())
    return __version__


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
    version=get_crochet_version(),
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
